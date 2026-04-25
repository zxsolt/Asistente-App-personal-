from __future__ import annotations

from datetime import date, datetime, timezone

from sqlalchemy import select
from sqlalchemy.orm import selectinload

from app.assistant.date_utils import normalize_text
from app.models.full_task import FullTask
from app.models.note import Note
from app.models.reminder import Reminder
from app.models.week import Week


class PlannerContextService:
    def __init__(self, db) -> None:
        self.db = db

    async def _load_weeks(self, *, user_id: int) -> list[Week]:
        result = await self.db.execute(
            select(Week)
            .where(Week.user_id == user_id)
            .options(selectinload(Week.full_tasks).selectinload(FullTask.actions))
            .order_by(Week.start_date.desc())
        )
        return list(result.scalars().all())

    async def _load_notes(self, *, user_id: int) -> list[Note]:
        result = await self.db.execute(
            select(Note).where(Note.user_id == user_id).order_by(Note.created_at.desc())
        )
        return list(result.scalars().all())

    async def _load_reminders(self, *, user_id: int) -> list[Reminder]:
        result = await self.db.execute(
            select(Reminder).where(Reminder.user_id == user_id).order_by(Reminder.scheduled_for.asc())
        )
        return list(result.scalars().all())

    def _matches_query(self, *, query: str, candidate: str) -> bool:
        query_terms = {term for term in normalize_text(query).split() if len(term) >= 4}
        candidate_terms = set(normalize_text(candidate).split())
        return bool(query_terms & candidate_terms)

    async def build_prioritized_context(self, *, user_id: int, query: str) -> dict[str, object]:
        weeks = await self._load_weeks(user_id=user_id)
        notes = await self._load_notes(user_id=user_id)
        reminders = await self._load_reminders(user_id=user_id)

        all_tasks: list[FullTask] = []
        for week in weeks:
            all_tasks.extend(week.full_tasks)

        today = date.today()
        current_weeks = [week for week in weeks if week.start_date <= today <= week.end_date]
        upcoming_weeks = [week for week in weeks if week.start_date > today][:3]
        active_tasks = [task for task in all_tasks if not task.completed][:20]
        recent_tasks = sorted(all_tasks, key=lambda task: task.id, reverse=True)[:20]
        historical_tasks = [task for task in all_tasks if task.completed][:30]
        relevant_tasks = [task for task in all_tasks if self._matches_query(query=query, candidate=task.name)][:12]
        relevant_notes = [note for note in notes if self._matches_query(query=query, candidate=note.content)][:10]

        return {
            "recent_context": {
                "weeks": [
                    {"id": week.id, "start_date": week.start_date.isoformat(), "end_date": week.end_date.isoformat()}
                    for week in weeks[:4]
                ],
                "tasks": [
                    {
                        "id": task.id,
                        "name": task.name,
                        "completed": task.completed,
                        "due_at": task.due_at.isoformat() if task.due_at else None,
                        "actions": [action.description for action in task.actions],
                    }
                    for task in recent_tasks
                ],
                "notes": [
                    {"id": note.id, "content": note.content, "category": note.category, "created_at": note.created_at.isoformat()}
                    for note in notes[:10]
                ],
            },
            "active_context": {
                "current_weeks": [
                    {"id": week.id, "start_date": week.start_date.isoformat(), "end_date": week.end_date.isoformat()}
                    for week in current_weeks
                ],
                "upcoming_weeks": [
                    {"id": week.id, "start_date": week.start_date.isoformat(), "end_date": week.end_date.isoformat()}
                    for week in upcoming_weeks
                ],
                "active_tasks": [
                    {
                        "id": task.id,
                        "name": task.name,
                        "task_type": task.task_type,
                        "due_at": task.due_at.isoformat() if task.due_at else None,
                        "actions": [action.description for action in task.actions],
                    }
                    for task in active_tasks
                ],
                "pending_reminders": [
                    {"id": reminder.id, "title": reminder.title, "scheduled_for": reminder.scheduled_for.isoformat()}
                    for reminder in reminders
                    if reminder.status == "pending"
                ][:10],
            },
            "historical_context": {
                "completed_tasks": [
                    {
                        "id": task.id,
                        "name": task.name,
                        "task_type": task.task_type,
                        "actions": [action.description for action in task.actions],
                    }
                    for task in historical_tasks
                ],
                "older_notes_count": max(0, len(notes) - 10),
                "weeks_count": len(weeks),
            },
            "relevant_entities": {
                "tasks": [
                    {
                        "id": task.id,
                        "name": task.name,
                        "task_type": task.task_type,
                        "actions": [action.description for action in task.actions],
                    }
                    for task in relevant_tasks
                ],
                "notes": [
                    {"id": note.id, "content": note.content, "category": note.category}
                    for note in relevant_notes
                ],
            },
            "constraints": {
                "timezone": "Europe/Madrid",
                "query_timestamp": datetime.now(timezone.utc).isoformat(),
            },
        }
