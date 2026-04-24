from datetime import datetime

from pydantic import BaseModel


class TelegramLinkCodeResponse(BaseModel):
    code: str
    expires_at: datetime


class TelegramLinkResponse(BaseModel):
    model_config = {"from_attributes": True}

    id: int
    user_id: int
    telegram_chat_id: int | None
    telegram_user_id: int | None
    telegram_username: str | None
    is_active: bool
    pending_link_expires_at: datetime | None
    last_seen_at: datetime | None
