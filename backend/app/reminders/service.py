from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.reminder import Reminder


class ReminderService:
    def __init__(self, db: AsyncSession):
        self.db = db

    async def create(
        self,
        *,
        user_id: int,
        title: str,
        scheduled_for,
        description: str | None = None,
        recurrence_rule: str | None = None,
        source: str = "web",
        source_ref: str | None = None,
    ) -> Reminder:
        reminder = Reminder(
            user_id=user_id,
            title=title,
            description=description,
            scheduled_for=scheduled_for,
            recurrence_rule=recurrence_rule,
            source=source,
            source_ref=source_ref,
        )
        self.db.add(reminder)
        await self.db.commit()
        await self.db.refresh(reminder)
        return reminder

    async def list_for_user(self, *, user_id: int, limit: int = 50) -> list[Reminder]:
        result = await self.db.execute(
            select(Reminder)
            .where(Reminder.user_id == user_id)
            .order_by(Reminder.scheduled_for.asc())
            .limit(limit)
        )
        return list(result.scalars().all())

    async def get_active_for_user(self, *, user_id: int, limit: int = 20) -> list[Reminder]:
        result = await self.db.execute(
            select(Reminder)
            .where(Reminder.user_id == user_id, Reminder.status == "pending")
            .order_by(Reminder.scheduled_for.asc())
            .limit(limit)
        )
        return list(result.scalars().all())
