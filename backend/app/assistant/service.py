import logging
from datetime import datetime, timezone

import httpx

from app.ai.service import OpenRouterService
from app.assistant.classifier import classify_message
from app.assistant.date_utils import normalize_text, parse_temporal_context
from app.assistant.formatters import (
    format_multi_task_confirmation,
    format_note_confirmation,
    format_reminder_confirmation,
    format_task_confirmation,
    format_task_list,
    format_week_confirmation,
)
from app.assistant.schemas import AssistantChannel, AssistantIntent, AssistantMessageResponse
from app.assistant.task_service import AssistantTaskService
from app.notes.service import NoteService
from app.planner.context_service import PlannerContextService
from app.planner.service import PlannerService
from app.reminders.service import ReminderService

logger = logging.getLogger(__name__)


class AssistantService:
    def __init__(self, db) -> None:
        self.db = db
        self.task_service = AssistantTaskService(db)
        self.note_service = NoteService(db)
        self.reminder_service = ReminderService(db)
        self.ai_service = OpenRouterService()
        self.planner_service = PlannerService(db)
        self.context_service = PlannerContextService(db)

    def _extract_multiple_tasks(self, message: str, cleaned_message: str) -> list[str]:
        normalized = normalize_text(message)
        if not any(token in normalized for token in ("varias tareas", "muchas tareas", "mas tareas")):
            return []

        source = cleaned_message if cleaned_message and cleaned_message != message else message
        if ":" in source:
            source = source.split(":", 1)[1]
        separators = (";", "\n", ",")
        if not any(separator in source for separator in separators):
            return []

        raw_parts = source.replace("\n", ",").replace(";", ",").split(",")
        tasks = []
        for part in raw_parts:
            candidate = part.strip(" :-")
            normalized_candidate = normalize_text(candidate)
            if not candidate:
                continue
            if normalized_candidate in {"varias tareas", "muchas tareas", "mas tareas", "tareas"}:
                continue
            tasks.append(candidate)
        return tasks

    def _is_ambiguous_task_request(self, message: str, cleaned_message: str) -> bool:
        normalized_message = normalize_text(message)
        normalized_cleaned = normalize_text(cleaned_message)
        generic_patterns = {
            "varias tareas",
            "muchas tareas",
            "mas tareas",
            "nuevas tareas",
            "tareas",
            "anademe varias tareas",
            "anade varias tareas",
            "crea varias tareas",
        }
        if normalized_cleaned in generic_patterns or normalized_message in generic_patterns:
            return True
        if "varias tareas" in normalized_message and not self._extract_multiple_tasks(message, cleaned_message):
            return True
        return False

    async def _build_context(self, *, user_id: int) -> dict[str, object]:
        return await self.context_service.build_prioritized_context(user_id=user_id, query="")

    async def handle_message(
        self,
        *,
        user_id: int,
        message: str,
        channel: AssistantChannel,
        metadata: dict[str, object] | None = None,
    ) -> AssistantMessageResponse:
        metadata = metadata or {}
        classification = classify_message(message)
        temporal = parse_temporal_context(message)
        logger.info(
            "assistant_request",
            extra={
                "user_id": user_id,
                "channel": channel.value,
                "intent": classification.intent.value,
            },
        )

        if self.planner_service.should_plan(message=message) and classification.intent not in {
            AssistantIntent.NOTE_CREATE,
            AssistantIntent.REMINDER_CREATE,
            AssistantIntent.WEEK_CREATE,
        }:
            planner_result = await self.planner_service.build_plan(user_id=user_id, message=message)
            return AssistantMessageResponse(
                reply_text=planner_result.natural_response,
                intent=classification.intent,
                action_taken="plan_proposed",
                entities={},
                used_ai=False,
                persistence_mode=planner_result.persistence_mode,
                planning_json=planner_result.planning_json,
                confidence=0.72,
                rationale_summary="He interpretado la entrada como una necesidad de planificacion con varias decisiones implicitas.",
            )

        if classification.intent == AssistantIntent.TASK_CREATE:
            multiple_tasks = self._extract_multiple_tasks(message, classification.cleaned_message)
            if multiple_tasks:
                created_tasks = []
                for task_name in multiple_tasks:
                    created_tasks.append(
                        await self.task_service.create_task(
                            user_id=user_id,
                            name=task_name,
                            task_type=classification.task_type,
                            due_at=temporal.due_at,
                            priority=classification.priority,
                            natural_language_input=message,
                            source=channel.value,
                            source_ref=str(metadata.get("message_id")) if metadata.get("message_id") else None,
                        )
                    )
                return AssistantMessageResponse(
                    reply_text=format_multi_task_confirmation(created_tasks),
                    intent=classification.intent,
                    action_taken="task_batch_created",
                    entities={"task_ids": [task.id for task in created_tasks], "count": len(created_tasks)},
                    persistence_mode="applied",
                    confidence=0.93,
                    rationale_summary="La peticion contenia varias tareas separadas de forma clara y se han creado en lote.",
                )

            if self._is_ambiguous_task_request(message, classification.cleaned_message):
                return AssistantMessageResponse(
                    reply_text=(
                        "Necesito el detalle de las tareas. "
                        "Puedes enviarmelas en una frase separadas por comas, por ejemplo: "
                        "\"anademe varias tareas: llamar al dentista, comprar pan, pagar autonomos\"."
                    ),
                    intent=classification.intent,
                    action_taken="task_create_needs_details",
                    entities={},
                    persistence_mode="draft",
                    confidence=0.35,
                    rationale_summary="He detectado intencion de crear tareas, pero faltan los contenidos concretos.",
                )

            task = await self.task_service.create_task(
                user_id=user_id,
                name=classification.cleaned_message or message,
                task_type=classification.task_type,
                due_at=temporal.due_at,
                priority=classification.priority,
                natural_language_input=message,
                source=channel.value,
                source_ref=str(metadata.get("message_id")) if metadata.get("message_id") else None,
            )
            return AssistantMessageResponse(
                reply_text=format_task_confirmation(task),
                intent=classification.intent,
                action_taken="task_created",
                entities={
                    "task_id": task.id,
                    "due_at": task.due_at.isoformat() if task.due_at else None,
                    "priority": task.priority,
                },
                persistence_mode="applied",
                confidence=0.95,
                rationale_summary="La peticion de tarea era concreta y se ha guardado directamente.",
            )

        if classification.intent == AssistantIntent.TASK_QUERY:
            range_start = temporal.range_start or datetime.now(timezone.utc).date()
            range_end = temporal.range_end or range_start
            completed_only = "hice" in message.lower()
            tasks = await self.task_service.get_tasks_in_range(
                user_id=user_id,
                start=range_start,
                end=range_end,
                completed_only=completed_only,
            )
            heading = "Tareas encontradas"
            return AssistantMessageResponse(
                reply_text=format_task_list(tasks, heading=heading),
                intent=classification.intent,
                action_taken="task_query",
                entities={"count": len(tasks), "range_start": range_start.isoformat(), "range_end": range_end.isoformat()},
                persistence_mode="none",
                confidence=0.89,
                rationale_summary="He consultado tus tareas en el rango temporal detectado y te devuelvo el resultado directo.",
            )

        if classification.intent == AssistantIntent.NOTE_CREATE:
            note = await self.note_service.create(
                user_id=user_id,
                content=classification.cleaned_message or message,
                category="general",
                source=channel.value,
                source_ref=str(metadata.get("message_id")) if metadata.get("message_id") else None,
            )
            return AssistantMessageResponse(
                reply_text=format_note_confirmation(note),
                intent=classification.intent,
                action_taken="note_created",
                entities={"note_id": note.id},
                persistence_mode="applied",
                confidence=0.94,
                rationale_summary="La frase encajaba como nota directa y se ha guardado sin necesidad de aclaracion.",
            )

        if classification.intent == AssistantIntent.WEEK_CREATE:
            anchor_day = temporal.range_start
            week = await self.task_service.create_week(user_id=user_id, anchor_day=anchor_day)
            return AssistantMessageResponse(
                reply_text=format_week_confirmation(week),
                intent=classification.intent,
                action_taken="week_created",
                entities={
                    "week_id": week.id,
                    "start_date": week.start_date.isoformat(),
                    "end_date": week.end_date.isoformat(),
                },
                persistence_mode="applied",
                confidence=0.9,
                rationale_summary="La peticion indicaba claramente crear una nueva semana en el planner.",
            )

        if classification.intent == AssistantIntent.REMINDER_CREATE:
            if not temporal.due_at:
                return AssistantMessageResponse(
                    reply_text="Necesito una fecha para crear el recordatorio. Ejemplo: recuerdame pagar autonomos el lunes.",
                    intent=classification.intent,
                    action_taken="reminder_missing_date",
                    entities={},
                    persistence_mode="draft",
                    confidence=0.42,
                    rationale_summary="He detectado la intencion de recordatorio, pero falta el momento en el que debe dispararse.",
                )
            reminder = await self.reminder_service.create(
                user_id=user_id,
                title=classification.cleaned_message or message,
                description=message,
                scheduled_for=temporal.due_at,
                source=channel.value,
                source_ref=str(metadata.get("message_id")) if metadata.get("message_id") else None,
            )
            return AssistantMessageResponse(
                reply_text=format_reminder_confirmation(reminder),
                intent=classification.intent,
                action_taken="reminder_created",
                entities={"reminder_id": reminder.id, "scheduled_for": reminder.scheduled_for.isoformat()},
                persistence_mode="applied",
                confidence=0.96,
                rationale_summary="El recordatorio incluia un momento claro y se ha guardado para que el watcher lo vigile.",
            )

        context = await self.context_service.build_prioritized_context(user_id=user_id, query=message)
        try:
            ai_result = await self.ai_service.answer(message=message, context=context)
        except (RuntimeError, httpx.HTTPError) as exc:
            logger.exception("assistant_ai_failure", extra={"user_id": user_id, "error": str(exc)})
            return AssistantMessageResponse(
                reply_text="No puedo usar la capa de IA ahora mismo. Revisa OpenRouter o intenta una accion mas directa.",
                intent=AssistantIntent.GENERAL_QUERY if classification.intent == AssistantIntent.UNKNOWN else classification.intent,
                action_taken="ai_unavailable",
                entities={},
                used_ai=False,
                persistence_mode="none",
                confidence=0.0,
                rationale_summary="La capa de razonamiento con IA no estaba disponible en este momento.",
            )
        return AssistantMessageResponse(
            reply_text=ai_result.text,
            intent=AssistantIntent.GENERAL_QUERY if classification.intent == AssistantIntent.UNKNOWN else classification.intent,
            action_taken="ai_response",
            entities={"model": ai_result.model},
            used_ai=True,
            persistence_mode="none",
            confidence=0.67,
            rationale_summary="He usado la capa de IA con contexto priorizado de toda tu base para responder a una consulta abierta.",
        )
