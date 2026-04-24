from datetime import date

from pydantic import BaseModel, model_validator

from app.schemas.pool_task import PoolTaskResponse
from app.schemas.full_task import FullTaskResponse
from app.schemas.daily_distribution import DailyDistributionResponse
from app.schemas.weekly_review import WeeklyReviewResponse


class WeekCreate(BaseModel):
    start_date: date
    end_date: date

    @model_validator(mode="after")
    def end_after_start(self) -> "WeekCreate":
        if self.end_date <= self.start_date:
            raise ValueError("end_date must be after start_date")
        return self


class WeekUpdate(BaseModel):
    start_date: date | None = None
    end_date: date | None = None


class WeekResponse(BaseModel):
    model_config = {"from_attributes": True}

    id: int
    start_date: date
    end_date: date


class WeekDetailResponse(WeekResponse):
    pool_tasks: list[PoolTaskResponse] = []
    full_tasks: list[FullTaskResponse] = []
    daily_distributions: list[DailyDistributionResponse] = []
    weekly_review: WeeklyReviewResponse | None = None
