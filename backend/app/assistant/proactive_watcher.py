from __future__ import annotations

import asyncio
import logging
from datetime import date, datetime, timedelta, timezone

from sqlalchemy import select
from sqlalchemy.orm import selectinload

from app.assistant.notification_service import AssistantNotificationService
from app.core.config import settings
from app.core.database import AsyncSessionLocal
from app.models.full_task import FullTask
from app.models.reminder import Reminder
from app.models.user import User
from app.models.week import Week

logger = logging.getLogger(__name__)


class ProactiveWatcher:
    def __init__(self) -> None:
        self._running = False

    async def run_forever(self) -> None:
        self._running = True
        while self._running:
            try:
                await self.run_once()
            except asyncio.CancelledError:
                raise
            except Exception:
                logger.exception("assistant_watcher_cycle_failed")
            await asyncio.sleep(settings.ASSISTANT_WATCHER_INTERVAL_SECONDS)

    def stop(self) -> None:
        self._running = False

    async def run_once(self) -> None:
        async with AsyncSessionLocal() as db:
            result = await db.execute(select(User.id))
            user_ids = list(result.scalars().all())
            notification_service = AssistantNotificationService(db)

            for user_id in user_ids:
                try:
                    await self._evaluate_user(
                        user_id=user_id,
                        notification_service=notification_service,
                    )
                except Exception:
                    logger.exception("assistant_watcher_user_failed", extra={"user_id": user_id})

    async def _load_weeks(self, *, db, user_id: int) -> list[Week]:
        result = await db.execute(
            select(Week)
            .where(Week.user_id == user_id)
            .options(selectinload(Week.full_tasks).selectinload(FullTask.actions))
            .order_by(Week.start_date.desc())
        )
        return list(result.scalars().all())

    async def _load_pending_reminders(self, *, db, user_id: int) -> list[Reminder]:
        result = await db.execute(
            select(Reminder)
            .where(Reminder.user_id == user_id, Reminder.status == "pending")
            .order_by(Reminder.scheduled_for.asc())
        )
        return list(result.scalars().all())

    async def _evaluate_user(
        self,
        *,
        user_id: int,
        notification_service: AssistantNotificationService,
    ) -> None:
        db = notification_service.db
        weeks = await self._load_weeks(db=db, user_id=user_id)
        reminders = await self._load_pending_reminders(db=db, user_id=user_id)

        now = datetime.now(timezone.utc)
        today = now.date()
        current_week = next((week for week in weeks if week.start_date <= today <= week.end_date), None)
        all_tasks = [task for week in weeks for task in week.full_tasks]
        open_tasks = [task for task in all_tasks if not task.completed]
        tasks_due_today = [task for task in open_tasks if task.due_at and task.due_at.date() == today]
        overdue_tasks = [
            task for task in open_tasks if task.due_at and task.due_at.date() < today and (task.priority or "medium") != "low"
        ]
        reminder_cutoff = now + timedelta(minutes=settings.ASSISTANT_REMINDER_LOOKAHEAD_MINUTES)
        due_reminders = [reminder for reminder in reminders if reminder.scheduled_for <= reminder_cutoff]

        for reminder in due_reminders:
            await notification_service.create_proactive_notification(
                user_id=user_id,
                kind="reminder_due",
                title="Recordatorio cercano",
                message=f"{reminder.title} ({self._humanize_datetime(reminder.scheduled_for)})",
                payload={"reminder_id": reminder.id, "scheduled_for": reminder.scheduled_for.isoformat()},
                channels=["web", "telegram"],
                dedupe_key=f"reminder_due:{reminder.id}",
            )

        if current_week and not tasks_due_today and not due_reminders:
            await notification_service.create_proactive_notification(
                user_id=user_id,
                kind="today_empty",
                title="Hoy esta vacio",
                message="No veo nada claro para hoy. Puedes pedirme que te organice el dia o que cree una tarea puntual.",
                payload={"date": today.isoformat()},
                channels=["web"],
                dedupe_key=f"today_empty:{today.isoformat()}",
            )

        if len(tasks_due_today) >= 4:
            await notification_service.create_proactive_notification(
                user_id=user_id,
                kind="today_overloaded",
                title="Hoy esta cargado",
                message=f"Tienes {len(tasks_due_today)} tareas venciendo hoy. Conviene repartir o simplificar.",
                payload={"task_ids": [task.id for task in tasks_due_today], "date": today.isoformat()},
                channels=["web"],
                dedupe_key=f"today_overloaded:{today.isoformat()}",
            )

        if overdue_tasks:
            stale = overdue_tasks[0]
            await notification_service.create_proactive_notification(
                user_id=user_id,
                kind="stale_task",
                title="Tarea atascada",
                message=f"\"{stale.name}\" ya deberia haberse movido. Si quieres, la replanteamos juntos.",
                payload={"task_id": stale.id, "due_at": stale.due_at.isoformat() if stale.due_at else None},
                channels=["web", "telegram"] if stale.priority == "high" else ["web"],
                dedupe_key=f"stale_task:{stale.id}",
            )

        if current_week and len(current_week.full_tasks) <= 1:
            await notification_service.create_proactive_notification(
                user_id=user_id,
                kind="week_gap",
                title="Semana sin estructura",
                message="Tu semana actual esta casi vacia. Puedes pedirme que la rellene contigo o que proponga un plan.",
                payload={"week_id": current_week.id},
                channels=["web"],
                dedupe_key=f"week_gap:{current_week.id}",
            )

        follow_up_task = next((task for task in open_tasks if not task.actions and not task.completed), None)
        if follow_up_task:
            await notification_service.create_proactive_notification(
                user_id=user_id,
                kind="follow_up_hint",
                title="Siguiente paso pendiente",
                message=f"\"{follow_up_task.name}\" no tiene siguiente paso claro. Puedo ayudarte a partirla en acciones.",
                payload={"task_id": follow_up_task.id},
                channels=["web"],
                dedupe_key=f"follow_up_hint:{follow_up_task.id}",
            )

    def _humanize_datetime(self, value: datetime) -> str:
        local_value = value.astimezone(timezone.utc)
        return local_value.strftime("%Y-%m-%d %H:%M UTC")
