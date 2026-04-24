from datetime import datetime

from pydantic import BaseModel, Field


class ReminderCreate(BaseModel):
    title: str = Field(min_length=1, max_length=255)
    description: str | None = Field(default=None, max_length=8000)
    scheduled_for: datetime
    recurrence_rule: str | None = Field(default=None, max_length=255)
    source: str = Field(default="web", min_length=1, max_length=32)
    source_ref: str | None = Field(default=None, max_length=255)


class ReminderResponse(BaseModel):
    model_config = {"from_attributes": True}

    id: int
    user_id: int
    title: str
    description: str | None
    scheduled_for: datetime
    recurrence_rule: str | None
    status: str
    source: str
    source_ref: str | None
    created_at: datetime
    updated_at: datetime
