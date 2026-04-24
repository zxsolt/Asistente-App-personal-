import logging
import secrets
from datetime import datetime, timedelta, timezone

from fastapi import HTTPException, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.assistant.schemas import AssistantChannel
from app.assistant.service import AssistantService
from app.core.config import settings
from app.models.telegram_link import TelegramLink
from app.telegram.client import TelegramBotClient

logger = logging.getLogger(__name__)


class TelegramLinkService:
    def __init__(self, db: AsyncSession):
        self.db = db

    async def get_for_user(self, *, user_id: int) -> TelegramLink | None:
        result = await self.db.execute(select(TelegramLink).where(TelegramLink.user_id == user_id))
        return result.scalar_one_or_none()

    async def generate_link_code(self, *, user_id: int) -> tuple[str, datetime]:
        link = await self.get_for_user(user_id=user_id)
        if not link:
            link = TelegramLink(user_id=user_id)
            self.db.add(link)

        code = secrets.token_urlsafe(8)
        expires_at = datetime.now(timezone.utc) + timedelta(minutes=settings.TELEGRAM_LINK_CODE_TTL_MINUTES)
        link.pending_link_code = code
        link.pending_link_expires_at = expires_at
        link.is_active = False
        await self.db.commit()
        await self.db.refresh(link)
        return code, expires_at

    async def activate_link(
        self,
        *,
        code: str,
        chat_id: int,
        telegram_user_id: int,
        telegram_username: str | None,
    ) -> TelegramLink | None:
        result = await self.db.execute(
            select(TelegramLink).where(TelegramLink.pending_link_code == code)
        )
        link = result.scalar_one_or_none()
        if not link or not link.pending_link_expires_at:
            return None
        if link.pending_link_expires_at < datetime.now(timezone.utc):
            return None

        link.telegram_chat_id = chat_id
        link.telegram_user_id = telegram_user_id
        link.telegram_username = telegram_username
        link.pending_link_code = None
        link.pending_link_expires_at = None
        link.last_seen_at = datetime.now(timezone.utc)
        link.is_active = True
        await self.db.commit()
        await self.db.refresh(link)
        return link

    async def get_active_by_chat_id(self, *, chat_id: int) -> TelegramLink | None:
        result = await self.db.execute(
            select(TelegramLink).where(TelegramLink.telegram_chat_id == chat_id, TelegramLink.is_active.is_(True))
        )
        return result.scalar_one_or_none()


class TelegramWebhookService:
    def __init__(self, db: AsyncSession):
        self.db = db
        self.link_service = TelegramLinkService(db)
        self.bot_client = TelegramBotClient()

    async def _extract_message(self, update: dict) -> tuple[int, int, str | None, str | None, int | None]:
        message = update.get("message") or {}
        chat = message.get("chat") or {}
        user = message.get("from") or {}
        return (
            chat.get("id"),
            user.get("id"),
            user.get("username"),
            message.get("text"),
            message.get("message_id"),
        )

    async def handle_update(self, update: dict) -> dict[str, object]:
        chat_id, telegram_user_id, username, text, message_id = await self._extract_message(update)
        if not chat_id or not telegram_user_id or not text:
            return {"handled": False, "reason": "unsupported_update"}

        stripped_text = text.strip()
        if stripped_text.startswith("/start "):
            code = stripped_text.split(maxsplit=1)[1].strip()
            link = await self.link_service.activate_link(
                code=code,
                chat_id=chat_id,
                telegram_user_id=telegram_user_id,
                telegram_username=username,
            )
            if not link:
                await self.bot_client.send_message(chat_id=chat_id, text="Codigo de enlace invalido o caducado.")
                return {"handled": True, "action": "link_failed"}

            await self.bot_client.send_message(chat_id=chat_id, text="Telegram enlazado correctamente.")
            return {"handled": True, "action": "link_success"}

        link = await self.link_service.get_active_by_chat_id(chat_id=chat_id)
        if not link:
            await self.bot_client.send_message(
                chat_id=chat_id,
                text="Tu Telegram no esta enlazado. Genera un codigo desde la app y enviame /start CODIGO.",
            )
            return {"handled": True, "action": "unlinked_user"}

        link.last_seen_at = datetime.now(timezone.utc)
        await self.db.commit()

        assistant = AssistantService(self.db)
        response = await assistant.handle_message(
            user_id=link.user_id,
            message=stripped_text,
            channel=AssistantChannel.TELEGRAM,
            metadata={"message_id": message_id, "telegram_chat_id": chat_id},
        )
        await self.bot_client.send_message(chat_id=chat_id, text=response.reply_text)
        logger.info("telegram_update_handled", extra={"chat_id": chat_id, "intent": response.intent.value})
        return {"handled": True, "action": response.action_taken}


def validate_telegram_secret(header_value: str | None) -> None:
    expected = settings.TELEGRAM_WEBHOOK_SECRET
    if expected and header_value != expected:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Invalid Telegram secret")
