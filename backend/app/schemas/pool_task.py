from typing import Literal

from pydantic import BaseModel


class PoolTaskCreate(BaseModel):
    title: str
    task_type: Literal["work", "study"]


class PoolTaskUpdate(BaseModel):
    title: str | None = None
    task_type: Literal["work", "study"] | None = None


class PoolTaskResponse(BaseModel):
    model_config = {"from_attributes": True}

    id: int
    week_id: int
    title: str
    task_type: str
