from pydantic import BaseModel


class WeeklyReviewUpsert(BaseModel):
    closed_this_week: str | None = None
    pending_why: str | None = None
    moving_to_next_week: str | None = None


class WeeklyReviewResponse(BaseModel):
    model_config = {"from_attributes": True}

    id: int
    week_id: int
    closed_this_week: str | None
    pending_why: str | None
    moving_to_next_week: str | None
