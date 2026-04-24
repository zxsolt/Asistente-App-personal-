from typing import Literal

from pydantic import BaseModel, Field

from app.schemas.action import ActionResponse


class FullTaskCreate(BaseModel):
    name: str
    task_type: Literal["work", "study"]
    goal: str | None = None
    milestone: str | None = None
    milestone_dod: str | None = None
    time_budget_minutes: int | None = Field(default=None, ge=1, le=10080)
    limit_mode: Literal["warn", "hard_stop"] = "warn"


class FullTaskUpdate(BaseModel):
    name: str | None = None
    task_type: Literal["work", "study"] | None = None
    goal: str | None = None
    milestone: str | None = None
    milestone_dod: str | None = None
    time_budget_minutes: int | None = Field(default=None, ge=1, le=10080)
    limit_mode: Literal["warn", "hard_stop"] | None = None
    completed: bool | None = None


class FocusLogCreate(BaseModel):
    seconds: int = Field(ge=1, le=14400)


class FullTaskResponse(BaseModel):
    model_config = {"from_attributes": True}

    id: int
    week_id: int
    name: str
    task_type: str
    goal: str | None
    milestone: str | None
    milestone_dod: str | None
    time_budget_minutes: int | None
    time_spent_seconds: int
    limit_mode: str
    completed: bool
    actions: list[ActionResponse] = []
