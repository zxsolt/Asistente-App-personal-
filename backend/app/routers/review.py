from fastapi import APIRouter, HTTPException, status
from sqlalchemy import select

from app.core.deps import DB, CurrentUser
from app.models.week import Week
from app.models.weekly_review import WeeklyReview
from app.schemas.weekly_review import WeeklyReviewResponse, WeeklyReviewUpsert

router = APIRouter(prefix="/weeks/{week_id}/review", tags=["review"])


async def _get_week(week_id: int, user_id: int, db: DB) -> Week:
    result = await db.execute(select(Week).where(Week.id == week_id))
    week = result.scalar_one_or_none()
    if not week or week.user_id != user_id:
        raise HTTPException(status_code=404, detail="Week not found")
    return week


@router.get("/", response_model=WeeklyReviewResponse | None)
async def get_review(week_id: int, current_user: CurrentUser, db: DB) -> WeeklyReview | None:
    await _get_week(week_id, current_user.id, db)
    result = await db.execute(select(WeeklyReview).where(WeeklyReview.week_id == week_id))
    return result.scalar_one_or_none()


@router.put("/", response_model=WeeklyReviewResponse, status_code=status.HTTP_200_OK)
async def upsert_review(week_id: int, body: WeeklyReviewUpsert, current_user: CurrentUser, db: DB) -> WeeklyReview:
    await _get_week(week_id, current_user.id, db)
    result = await db.execute(select(WeeklyReview).where(WeeklyReview.week_id == week_id))
    review = result.scalar_one_or_none()

    if review:
        review.closed_this_week = body.closed_this_week
        review.pending_why = body.pending_why
        review.moving_to_next_week = body.moving_to_next_week
    else:
        review = WeeklyReview(
            week_id=week_id,
            closed_this_week=body.closed_this_week,
            pending_why=body.pending_why,
            moving_to_next_week=body.moving_to_next_week,
        )
        db.add(review)

    await db.commit()
    await db.refresh(review)
    return review
