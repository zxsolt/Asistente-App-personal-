from fastapi import APIRouter, HTTPException, status

from app.assistant.notification_service import AssistantNotificationService
from app.assistant.schemas import (
    AssistantMessageRequest,
    AssistantMessageResponse,
    AssistantNotificationResponse,
)
from app.assistant.service import AssistantService
from app.core.deps import CurrentUser, DB

router = APIRouter(prefix="/assistant", tags=["assistant"])


@router.post("/message", response_model=AssistantMessageResponse)
async def assistant_message(
    body: AssistantMessageRequest,
    current_user: CurrentUser,
    db: DB,
) -> AssistantMessageResponse:
    service = AssistantService(db)
    return await service.handle_message(
        user_id=current_user.id,
        message=body.message,
        channel=body.channel,
        metadata=body.metadata,
    )


@router.get("/notifications", response_model=list[AssistantNotificationResponse])
async def assistant_notifications(
    current_user: CurrentUser,
    db: DB,
) -> list[AssistantNotificationResponse]:
    service = AssistantNotificationService(db)
    return await service.list_for_user(user_id=current_user.id)


@router.post("/notifications/{notification_id}/read", response_model=AssistantNotificationResponse)
async def mark_assistant_notification_read(
    notification_id: int,
    current_user: CurrentUser,
    db: DB,
) -> AssistantNotificationResponse:
    service = AssistantNotificationService(db)
    notification = await service.mark_read(user_id=current_user.id, notification_id=notification_id)
    if notification is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Notification not found")
    return notification
