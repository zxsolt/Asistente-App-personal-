from fastapi import APIRouter

from app.assistant.schemas import AssistantMessageRequest, AssistantMessageResponse
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
