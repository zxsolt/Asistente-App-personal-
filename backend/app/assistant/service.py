import logging
from datetime import datetime, timezone

import httpx

from app.ai.service import OpenRouterService
from app.assistant.classifier import classify_message
from app.assistant.date_utils import parse_temporal_context
from app.assistant.formatters import (
    format_note_confirmation,
    format_reminder_confirmation,
    format_task_confirmation,
    format_task_list,
)
from app.assistant.schemas import AssistantChannel, AssistantIntent, AssistantMessageResponse
from app.assistant.task_service import AssistantTaskService
from app.notes.service import NoteService
from app.reminders.service import ReminderService

logger = logging.getLogger(__name__)


class AssistantService:
    def __init__(self, db) -> None:
        self.db = db
        self.task_service = AssistantTaskService(db)
        self.note_service = NoteService(db)
        self.reminder_service = ReminderService(db)
        self.ai_service = OpenRouterService()

    async def _build_context(self, *, user_id: int) -> dict[str, object]:
        tasks = await self.task_service.get_recent_tasks(user_id=user_id, limit=8)
        reminders = await self.reminder_service.get_active_for_user(user_id=user_id, limit=5)
        notes = await self.note_service.list_for_user(user_id=user_id, limit=5)
        return {
            "tasks": [
                {"name": task.name, "completed": task.completed, "due_at": task.due_at.isoformat() if task.due_at else None}
                for task in tasks
            ],
            "reminders": [
                {"title": reminder.title, "scheduled_for": reminder.scheduled_for.isoformat()}
                for reminder in reminders
            ],
            "notes": [{"content": note.content, "category": note.category} for note in notes],
        }

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

        if classification.intent == AssistantIntent.TASK_CREATE:
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
            )

        if classification.intent == AssistantIntent.REMINDER_CREATE:
            if not temporal.due_at:
                return AssistantMessageResponse(
                    reply_text="Necesito una fecha para crear el recordatorio. Ejemplo: recuerdame pagar autonomos el lunes.",
                    intent=classification.intent,
                    action_taken="reminder_missing_date",
                    entities={},
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
            )

        context = await self._build_context(user_id=user_id)
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
            )
        return AssistantMessageResponse(
            reply_text=ai_result.text,
            intent=AssistantIntent.GENERAL_QUERY if classification.intent == AssistantIntent.UNKNOWN else classification.intent,
            action_taken="ai_response",
            entities={"model": ai_result.model},
            used_ai=True,
        )
