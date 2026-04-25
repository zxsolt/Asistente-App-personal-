import logging

import httpx

from app.ai.service import OpenRouterService
from app.assistant.formatters import (
    format_multi_task_confirmation,
    format_note_confirmation,
    format_note_list,
    format_reminder_confirmation,
    format_reminder_list,
    format_task_confirmation,
    format_task_list,
    format_week_confirmation,
)
from app.assistant.memory_service import AssistantMemoryService
from app.assistant.policy_service import AssistantPolicyService
from app.assistant.schemas import AssistantChannel, AssistantIntent, AssistantMessageResponse
from app.assistant.tool_registry import AssistantToolRegistry
from app.assistant.understanding_service import UnderstandingService

logger = logging.getLogger(__name__)


class AssistantService:
    def __init__(self, db) -> None:
        self.db = db
        self.ai_service = OpenRouterService()
        self.memory_service = AssistantMemoryService(db)
        self.tool_registry = AssistantToolRegistry(db)
        self.understanding_service = UnderstandingService()
        self.policy_service = AssistantPolicyService()

    def _extract_multiple_tasks(self, message: str, cleaned_message: str) -> list[str]:
        source = cleaned_message if cleaned_message and cleaned_message != message else message
        if ":" in source:
            source = source.split(":", 1)[1]
        separators = (";", "\n", ",")
        if not any(separator in source for separator in separators):
            return []
        raw_parts = source.replace("\n", ",").replace(";", ",").split(",")
        tasks = [part.strip(" :-") for part in raw_parts if part.strip(" :-")]
        return [task for task in tasks if task]

    async def handle_message(
        self,
        *,
        user_id: int,
        message: str,
        channel: AssistantChannel,
        metadata: dict[str, object] | None = None,
    ) -> AssistantMessageResponse:
        metadata = metadata or {}
        understanding = self.understanding_service.understand(message)
        decision = self.policy_service.choose(understanding=understanding)
        logger.info(
            "assistant_request",
            extra={
                "user_id": user_id,
                "channel": channel.value,
                "intent": understanding.intent.value,
                "decision": decision,
            },
        )

        if decision == "clarify":
            return AssistantMessageResponse(
                reply_text=self.understanding_service.build_clarification(understanding),
                intent=understanding.intent,
                decision="clarify",
                action_taken="clarification_requested",
                entities={"missing_fields": understanding.missing_fields},
                persistence_mode="none",
                confidence=understanding.confidence,
                rationale_summary=understanding.rationale_summary,
            )

        if decision == "act":
            source_ref = str(metadata.get("message_id")) if metadata.get("message_id") else None

            if understanding.intent == AssistantIntent.TASK_CREATE:
                multiple_tasks = self._extract_multiple_tasks(message, understanding.cleaned_message)
                if len(multiple_tasks) > 1:
                    created_tasks = []
                    for task_name in multiple_tasks:
                        created_tasks.append(
                            await self.tool_registry.create_task(
                                user_id=user_id,
                                name=task_name,
                                task_type=understanding.task_type,
                                due_at=understanding.temporal.due_at,
                                priority=understanding.priority,
                                natural_language_input=message,
                                source=channel.value,
                                source_ref=source_ref,
                            )
                        )
                    return AssistantMessageResponse(
                        reply_text=format_multi_task_confirmation(created_tasks),
                        intent=understanding.intent,
                        decision="act",
                        action_taken="task_batch_created",
                        entities={"task_ids": [task.id for task in created_tasks], "count": len(created_tasks)},
                        persistence_mode="applied",
                        confidence=0.95,
                        rationale_summary="Habia varias tareas concretas separadas claramente y se han guardado en lote.",
                    )

                task = await self.tool_registry.create_task(
                    user_id=user_id,
                    name=understanding.cleaned_message,
                    task_type=understanding.task_type,
                    due_at=understanding.temporal.due_at,
                    priority=understanding.priority,
                    natural_language_input=message,
                    source=channel.value,
                    source_ref=source_ref,
                )
                return AssistantMessageResponse(
                    reply_text=format_task_confirmation(task),
                    intent=understanding.intent,
                    decision="act",
                    action_taken="task_created",
                    entities={
                        "task_id": task.id,
                        "due_at": task.due_at.isoformat() if task.due_at else None,
                        "priority": task.priority,
                    },
                    persistence_mode="applied",
                    confidence=understanding.confidence,
                    rationale_summary=understanding.rationale_summary,
                )

            if understanding.intent == AssistantIntent.NOTE_CREATE:
                note = await self.tool_registry.create_note(
                    user_id=user_id,
                    content=understanding.cleaned_message,
                    source=channel.value,
                    source_ref=source_ref,
                )
                return AssistantMessageResponse(
                    reply_text=format_note_confirmation(note),
                    intent=understanding.intent,
                    decision="act",
                    action_taken="note_created",
                    entities={"note_id": note.id},
                    persistence_mode="applied",
                    confidence=understanding.confidence,
                    rationale_summary=understanding.rationale_summary,
                )

            if understanding.intent == AssistantIntent.REMINDER_CREATE:
                reminder = await self.tool_registry.create_reminder(
                    user_id=user_id,
                    title=understanding.cleaned_message,
                    description=message,
                    scheduled_for=understanding.temporal.due_at,
                    source=channel.value,
                    source_ref=source_ref,
                )
                return AssistantMessageResponse(
                    reply_text=format_reminder_confirmation(reminder),
                    intent=understanding.intent,
                    decision="act",
                    action_taken="reminder_created",
                    entities={"reminder_id": reminder.id, "scheduled_for": reminder.scheduled_for.isoformat()},
                    persistence_mode="applied",
                    confidence=understanding.confidence,
                    rationale_summary=understanding.rationale_summary,
                )

            if understanding.intent == AssistantIntent.WEEK_CREATE:
                week = await self.tool_registry.create_week(
                    user_id=user_id,
                    anchor_day=understanding.temporal.range_start,
                )
                return AssistantMessageResponse(
                    reply_text=format_week_confirmation(week),
                    intent=understanding.intent,
                    decision="act",
                    action_taken="week_created",
                    entities={
                        "week_id": week.id,
                        "start_date": week.start_date.isoformat(),
                        "end_date": week.end_date.isoformat(),
                    },
                    persistence_mode="applied",
                    confidence=understanding.confidence,
                    rationale_summary=understanding.rationale_summary,
                )

        if understanding.intent == AssistantIntent.TASK_QUERY:
            tasks = await self.memory_service.list_tasks_for_temporal_context(
                user_id=user_id,
                temporal=understanding.temporal,
            )
            return AssistantMessageResponse(
                reply_text=format_task_list(tasks, heading="Tareas encontradas"),
                intent=understanding.intent,
                decision="answer",
                action_taken="task_query",
                entities={"count": len(tasks)},
                persistence_mode="none",
                confidence=understanding.confidence,
                rationale_summary=understanding.rationale_summary,
            )

        if understanding.intent == AssistantIntent.NOTE_QUERY:
            notes = await self.memory_service.list_notes_for_temporal_context(
                user_id=user_id,
                temporal=understanding.temporal,
            )
            return AssistantMessageResponse(
                reply_text=format_note_list(notes, heading="Notas encontradas"),
                intent=understanding.intent,
                decision="answer",
                action_taken="note_query",
                entities={"count": len(notes)},
                persistence_mode="none",
                confidence=understanding.confidence,
                rationale_summary=understanding.rationale_summary,
            )

        if understanding.intent == AssistantIntent.REMINDER_QUERY:
            reminders = await self.memory_service.list_reminders(user_id=user_id)
            return AssistantMessageResponse(
                reply_text=format_reminder_list(reminders, heading="Recordatorios"),
                intent=understanding.intent,
                decision="answer",
                action_taken="reminder_query",
                entities={"count": len(reminders)},
                persistence_mode="none",
                confidence=understanding.confidence,
                rationale_summary=understanding.rationale_summary,
            )

        context = await self.memory_service.build_context(user_id=user_id, query=message)
        try:
            ai_result = await self.ai_service.answer(message=message, context=context)
        except (RuntimeError, httpx.HTTPError) as exc:
            logger.exception("assistant_ai_failure", extra={"user_id": user_id, "error": str(exc)})
            fallback_text = (
                self.understanding_service.build_clarification(understanding)
                if understanding.intent in {AssistantIntent.TASK_CREATE, AssistantIntent.NOTE_CREATE, AssistantIntent.REMINDER_CREATE}
                else "Ahora mismo no puedo razonar bien esa peticion. Dime una accion mas concreta."
            )
            return AssistantMessageResponse(
                reply_text=fallback_text,
                intent=AssistantIntent.GENERAL_QUERY if understanding.intent == AssistantIntent.UNKNOWN else understanding.intent,
                decision="clarify" if understanding.intent in {AssistantIntent.TASK_CREATE, AssistantIntent.NOTE_CREATE, AssistantIntent.REMINDER_CREATE} else "answer",
                action_taken="ai_unavailable",
                entities={},
                used_ai=False,
                persistence_mode="none",
                confidence=0.0,
                rationale_summary="La capa de IA no estaba disponible y he caido al comportamiento seguro.",
            )
        return AssistantMessageResponse(
            reply_text=ai_result.text,
            intent=AssistantIntent.GENERAL_QUERY if understanding.intent == AssistantIntent.UNKNOWN else understanding.intent,
            decision="answer",
            action_taken="ai_response",
            entities={"model": ai_result.model},
            used_ai=True,
            persistence_mode="none",
            confidence=max(understanding.confidence, 0.66),
            rationale_summary="He usado contexto priorizado de tu base para responder a una consulta abierta.",
        )
