from __future__ import annotations

import json
import logging
from datetime import datetime, timezone

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.assistant.schemas import AssistantNotificationResponse
from app.models.assistant_notification import AssistantNotification
from app.models.telegram_link import TelegramLink
from app.telegram.client import TelegramBotClient

logger = logging.getLogger(__name__)


class AssistantNotificationService:
    def __init__(self, db: AsyncSession) -> None:
        self.db = db
        self.telegram_client = TelegramBotClient()

    def _serialize_payload(self, payload: dict[str, object] | None) -> str | None:
        if not payload:
            return None
        return json.dumps(payload, ensure_ascii=True)

    def _deserialize_payload(self, payload_json: str | None) -> dict[str, object]:
        if not payload_json:
            return {}
        try:
            loaded = json.loads(payload_json)
        except json.JSONDecodeError:
            return {}
        return loaded if isinstance(loaded, dict) else {}

    def to_response(self, notification: AssistantNotification) -> AssistantNotificationResponse:
        return AssistantNotificationResponse(
            id=notification.id,
            kind=notification.kind,
            title=notification.title,
            message=notification.message,
            payload=self._deserialize_payload(notification.payload_json),
            channel_targets=[value for value in notification.channel_targets.split(",") if value],
            status=notification.status,
            source=notification.source,
            created_at=notification.created_at,
            sent_at=notification.sent_at,
            read_at=notification.read_at,
            last_error=notification.last_error,
        )

    async def list_for_user(self, *, user_id: int, limit: int = 50) -> list[AssistantNotificationResponse]:
        result = await self.db.execute(
            select(AssistantNotification)
            .where(AssistantNotification.user_id == user_id)
            .order_by(AssistantNotification.created_at.desc())
            .limit(limit)
        )
        return [self.to_response(notification) for notification in result.scalars().all()]

    async def mark_read(self, *, user_id: int, notification_id: int) -> AssistantNotificationResponse | None:
        result = await self.db.execute(
            select(AssistantNotification).where(
                AssistantNotification.id == notification_id,
                AssistantNotification.user_id == user_id,
            )
        )
        notification = result.scalar_one_or_none()
        if not notification:
            return None

        if notification.read_at is None:
            notification.read_at = datetime.now(timezone.utc)
            await self.db.commit()
            await self.db.refresh(notification)
        return self.to_response(notification)

    async def create_proactive_notification(
        self,
        *,
        user_id: int,
        kind: str,
        title: str,
        message: str,
        payload: dict[str, object] | None,
        channels: list[str],
        dedupe_key: str,
    ) -> AssistantNotificationResponse | None:
        existing = await self.db.execute(
            select(AssistantNotification).where(
                AssistantNotification.user_id == user_id,
                AssistantNotification.dedupe_key == dedupe_key,
            )
        )
        if existing.scalar_one_or_none():
            return None

        notification = AssistantNotification(
            user_id=user_id,
            kind=kind,
            title=title,
            message=message,
            payload_json=self._serialize_payload(payload),
            channel_targets=",".join(channels),
            status="pending",
            dedupe_key=dedupe_key,
            source="watcher",
        )
        self.db.add(notification)
        await self.db.commit()
        await self.db.refresh(notification)
        await self.dispatch(notification=notification)
        return self.to_response(notification)

    async def dispatch(self, *, notification: AssistantNotification) -> None:
        channels = [value for value in notification.channel_targets.split(",") if value]
        now = datetime.now(timezone.utc)
        last_error: str | None = None

        if "telegram" in channels:
            chat_result = await self.db.execute(
                select(TelegramLink).where(
                    TelegramLink.user_id == notification.user_id,
                    TelegramLink.is_active.is_(True),
                )
            )
            link = chat_result.scalar_one_or_none()
            if link and link.telegram_chat_id:
                try:
                    await self.telegram_client.send_message(
                        chat_id=link.telegram_chat_id,
                        text=f"{notification.title}\n{notification.message}",
                    )
                except Exception as exc:  # pragma: no cover - network dependent
                    logger.exception(
                        "assistant_notification_telegram_failed",
                        extra={"notification_id": notification.id, "user_id": notification.user_id},
                    )
                    last_error = str(exc)
            else:
                last_error = "telegram_not_linked"

        notification.sent_at = now
        notification.last_error = last_error
        notification.status = "failed" if last_error and channels == ["telegram"] else "sent"
        await self.db.commit()
        await self.db.refresh(notification)
