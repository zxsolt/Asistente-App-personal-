from __future__ import annotations

from datetime import date, datetime, timezone

from app.assistant.task_service import AssistantTaskService
from app.notes.service import NoteService
from app.planner.context_service import PlannerContextService
from app.reminders.service import ReminderService


class AssistantMemoryService:
    def __init__(self, db) -> None:
        self.db = db
        self.context_service = PlannerContextService(db)
        self.task_service = AssistantTaskService(db)
        self.note_service = NoteService(db)
        self.reminder_service = ReminderService(db)

    async def build_context(self, *, user_id: int, query: str) -> dict[str, object]:
        return await self.context_service.build_prioritized_context(user_id=user_id, query=query)

    async def list_tasks_for_temporal_context(self, *, user_id: int, temporal) -> list:
        range_start = temporal.range_start or datetime.now(timezone.utc).date()
        range_end = temporal.range_end or range_start
        completed_only = temporal.matched_phrase == "ayer"
        return await self.task_service.get_tasks_in_range(
            user_id=user_id,
            start=range_start,
            end=range_end,
            completed_only=completed_only,
        )

    async def list_notes_for_temporal_context(self, *, user_id: int, temporal, limit: int = 10) -> list:
        notes = await self.note_service.list_for_user(user_id=user_id, limit=limit)
        if temporal.range_start and temporal.range_end:
            return [
                note
                for note in notes
                if temporal.range_start <= note.created_at.date() <= temporal.range_end
            ]
        return notes

    async def list_reminders(self, *, user_id: int, limit: int = 10) -> list:
        return await self.reminder_service.list_for_user(user_id=user_id, limit=limit)
