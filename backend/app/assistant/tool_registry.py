from __future__ import annotations

from app.assistant.task_service import AssistantTaskService
from app.notes.service import NoteService
from app.reminders.service import ReminderService


class AssistantToolRegistry:
    def __init__(self, db) -> None:
        self.db = db
        self.task_service = AssistantTaskService(db)
        self.note_service = NoteService(db)
        self.reminder_service = ReminderService(db)

    async def create_task(
        self,
        *,
        user_id: int,
        name: str,
        task_type: str,
        due_at,
        priority: str | None,
        natural_language_input: str,
        source: str,
        source_ref: str | None,
    ):
        return await self.task_service.create_task(
            user_id=user_id,
            name=name,
            task_type=task_type,
            due_at=due_at,
            priority=priority,
            natural_language_input=natural_language_input,
            source=source,
            source_ref=source_ref,
        )

    async def create_note(
        self,
        *,
        user_id: int,
        content: str,
        source: str,
        source_ref: str | None,
    ):
        return await self.note_service.create(
            user_id=user_id,
            content=content,
            category="general",
            source=source,
            source_ref=source_ref,
        )

    async def create_reminder(
        self,
        *,
        user_id: int,
        title: str,
        description: str,
        scheduled_for,
        source: str,
        source_ref: str | None,
    ):
        return await self.reminder_service.create(
            user_id=user_id,
            title=title,
            description=description,
            scheduled_for=scheduled_for,
            source=source,
            source_ref=source_ref,
        )

    async def create_week(self, *, user_id: int, anchor_day):
        return await self.task_service.create_week(user_id=user_id, anchor_day=anchor_day)
