from fastapi import APIRouter, HTTPException, status
from sqlalchemy import select
from sqlalchemy.orm import selectinload

from app.core.deps import DB, CurrentUser
from app.models.full_task import FullTask
from app.models.week import Week
from app.schemas.week import WeekCreate, WeekDetailResponse, WeekResponse, WeekUpdate

router = APIRouter(prefix="/weeks", tags=["weeks"])


def _owned_or_404(week: Week | None, user_id: int) -> Week:
    if not week or week.user_id != user_id:
        raise HTTPException(status_code=404, detail="Week not found")
    return week


@router.get("/", response_model=list[WeekResponse])
async def list_weeks(current_user: CurrentUser, db: DB) -> list[Week]:
    result = await db.execute(
        select(Week).where(Week.user_id == current_user.id).order_by(Week.start_date.desc())
    )
    return list(result.scalars().all())


@router.post("/", response_model=WeekResponse, status_code=status.HTTP_201_CREATED)
async def create_week(body: WeekCreate, current_user: CurrentUser, db: DB) -> Week:
    week = Week(user_id=current_user.id, start_date=body.start_date, end_date=body.end_date)
    db.add(week)
    await db.commit()
    await db.refresh(week)
    return week


@router.get("/{week_id}", response_model=WeekDetailResponse)
async def get_week(week_id: int, current_user: CurrentUser, db: DB) -> Week:
    result = await db.execute(
        select(Week)
        .where(Week.id == week_id)
        .options(
            selectinload(Week.pool_tasks),
            selectinload(Week.full_tasks).selectinload(FullTask.actions),
            selectinload(Week.daily_distributions),
            selectinload(Week.weekly_review),
        )
    )
    week = result.scalar_one_or_none()
    return _owned_or_404(week, current_user.id)


@router.patch("/{week_id}", response_model=WeekResponse)
async def update_week(week_id: int, body: WeekUpdate, current_user: CurrentUser, db: DB) -> Week:
    result = await db.execute(select(Week).where(Week.id == week_id))
    week = _owned_or_404(result.scalar_one_or_none(), current_user.id)

    if body.start_date is not None:
        week.start_date = body.start_date
    if body.end_date is not None:
        week.end_date = body.end_date

    await db.commit()
    await db.refresh(week)
    return week


@router.delete("/{week_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_week(week_id: int, current_user: CurrentUser, db: DB) -> None:
    result = await db.execute(select(Week).where(Week.id == week_id))
    week = _owned_or_404(result.scalar_one_or_none(), current_user.id)
    await db.delete(week)
    await db.commit()
