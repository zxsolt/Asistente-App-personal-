from fastapi import APIRouter, Query, status

from app.core.deps import CurrentUser, DB
from app.reminders.service import ReminderService
from app.schemas.reminder import ReminderCreate, ReminderResponse

router = APIRouter(prefix="/reminders", tags=["reminders"])


@router.get("/", response_model=list[ReminderResponse])
async def list_reminders(
    current_user: CurrentUser,
    db: DB,
    limit: int = Query(default=50, ge=1, le=200),
) -> list[ReminderResponse]:
    service = ReminderService(db)
    return await service.list_for_user(user_id=current_user.id, limit=limit)


@router.post("/", response_model=ReminderResponse, status_code=status.HTTP_201_CREATED)
async def create_reminder(body: ReminderCreate, current_user: CurrentUser, db: DB) -> ReminderResponse:
    service = ReminderService(db)
    return await service.create(
        user_id=current_user.id,
        title=body.title,
        description=body.description,
        scheduled_for=body.scheduled_for,
        recurrence_rule=body.recurrence_rule,
        source=body.source,
        source_ref=body.source_ref,
    )
