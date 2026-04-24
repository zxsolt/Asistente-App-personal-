from datetime import date, datetime, timezone

from sqlalchemy import and_, or_, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.assistant.date_utils import end_of_week, start_of_week
from app.models.full_task import FullTask
from app.models.week import Week


class AssistantTaskService:
    def __init__(self, db: AsyncSession):
        self.db = db

    async def _find_week_covering(self, *, user_id: int, day: date) -> Week | None:
        result = await self.db.execute(
            select(Week).where(Week.user_id == user_id, Week.start_date <= day, Week.end_date >= day)
        )
        return result.scalar_one_or_none()

    async def ensure_week_for_date(self, *, user_id: int, day: date) -> Week:
        week = await self._find_week_covering(user_id=user_id, day=day)
        if week:
            return week

        week = Week(user_id=user_id, start_date=start_of_week(day), end_date=end_of_week(day))
        self.db.add(week)
        await self.db.flush()
        return week

    async def create_task(
        self,
        *,
        user_id: int,
        name: str,
        task_type: str,
        due_at: datetime | None,
        priority: str | None,
        natural_language_input: str | None,
        source: str,
        source_ref: str | None = None,
    ) -> FullTask:
        target_day = (due_at or datetime.now(timezone.utc)).date()
        week = await self.ensure_week_for_date(user_id=user_id, day=target_day)
        task = FullTask(
            week_id=week.id,
            name=name,
            task_type=task_type,
            due_at=due_at,
            priority=priority,
            source=source,
            source_ref=source_ref,
            natural_language_input=natural_language_input,
        )
        self.db.add(task)
        await self.db.commit()
        await self.db.refresh(task)
        return task

    async def get_tasks_in_range(
        self,
        *,
        user_id: int,
        start: date,
        end: date,
        completed_only: bool = False,
        limit: int = 50,
    ) -> list[FullTask]:
        start_dt = datetime.combine(start, datetime.min.time(), tzinfo=timezone.utc)
        end_dt = datetime.combine(end, datetime.max.time(), tzinfo=timezone.utc)
        conditions = [
            Week.user_id == user_id,
            or_(
                and_(FullTask.due_at.is_not(None), FullTask.due_at >= start_dt, FullTask.due_at <= end_dt),
                and_(FullTask.due_at.is_(None), Week.start_date <= end, Week.end_date >= start),
            ),
        ]
        if completed_only:
            conditions.append(FullTask.completed.is_(True))
        result = await self.db.execute(
            select(FullTask)
            .join(Week, Week.id == FullTask.week_id)
            .where(*conditions)
            .order_by(FullTask.completed.asc(), FullTask.due_at.is_(None), FullTask.due_at.asc(), FullTask.id.desc())
            .limit(limit)
        )
        return list(result.scalars().all())

    async def get_recent_tasks(self, *, user_id: int, limit: int = 10) -> list[FullTask]:
        result = await self.db.execute(
            select(FullTask)
            .join(Week, Week.id == FullTask.week_id)
            .where(Week.user_id == user_id)
            .order_by(FullTask.id.desc())
            .limit(limit)
        )
        return list(result.scalars().all())
