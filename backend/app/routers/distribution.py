from fastapi import APIRouter, HTTPException
from sqlalchemy import select

from app.core.deps import DB, CurrentUser
from app.models.daily_distribution import DailyDistribution
from app.models.week import Week
from app.schemas.daily_distribution import DailyDistributionResponse, DailyDistributionUpsert

router = APIRouter(prefix="/weeks/{week_id}/distribution", tags=["distribution"])


async def _get_week(week_id: int, user_id: int, db: DB) -> Week:
    result = await db.execute(select(Week).where(Week.id == week_id))
    week = result.scalar_one_or_none()
    if not week or week.user_id != user_id:
        raise HTTPException(status_code=404, detail="Week not found")
    return week


@router.get("/", response_model=list[DailyDistributionResponse])
async def get_distribution(week_id: int, current_user: CurrentUser, db: DB) -> list[DailyDistribution]:
    await _get_week(week_id, current_user.id, db)
    result = await db.execute(select(DailyDistribution).where(DailyDistribution.week_id == week_id))
    return list(result.scalars().all())


@router.put("/", response_model=list[DailyDistributionResponse])
async def upsert_distribution(
    week_id: int,
    body: list[DailyDistributionUpsert],
    current_user: CurrentUser,
    db: DB,
) -> list[DailyDistribution]:
    await _get_week(week_id, current_user.id, db)

    # delete existing and replace
    existing = await db.execute(select(DailyDistribution).where(DailyDistribution.week_id == week_id))
    for row in existing.scalars().all():
        await db.delete(row)

    new_rows: list[DailyDistribution] = []
    for item in body:
        row = DailyDistribution(
            week_id=week_id,
            day=item.day,
            day_type=item.day_type,
            task_assignments=",".join(item.task_assignments) if item.task_assignments else None,
        )
        db.add(row)
        new_rows.append(row)

    await db.commit()
    for row in new_rows:
        await db.refresh(row)
    return new_rows
