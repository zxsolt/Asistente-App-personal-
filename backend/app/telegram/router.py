from fastapi import APIRouter, Header, Request

from app.core.deps import CurrentUser, DB
from app.schemas.telegram import TelegramLinkCodeResponse, TelegramLinkResponse
from app.telegram.service import TelegramLinkService, TelegramWebhookService, validate_telegram_secret

router = APIRouter(prefix="/telegram", tags=["telegram"])


@router.post("/webhook")
async def telegram_webhook(
    request: Request,
    db: DB,
    x_telegram_bot_api_secret_token: str | None = Header(default=None),
) -> dict[str, object]:
    validate_telegram_secret(x_telegram_bot_api_secret_token)
    update = await request.json()
    service = TelegramWebhookService(db)
    return await service.handle_update(update)


@router.post("/link-code", response_model=TelegramLinkCodeResponse)
async def create_link_code(current_user: CurrentUser, db: DB) -> TelegramLinkCodeResponse:
    service = TelegramLinkService(db)
    code, expires_at = await service.generate_link_code(user_id=current_user.id)
    return TelegramLinkCodeResponse(code=code, expires_at=expires_at)


@router.get("/link", response_model=TelegramLinkResponse | None)
async def get_link(current_user: CurrentUser, db: DB) -> TelegramLinkResponse | None:
    service = TelegramLinkService(db)
    return await service.get_for_user(user_id=current_user.id)
