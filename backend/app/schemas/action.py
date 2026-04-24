from typing import Literal

from pydantic import BaseModel

DayLiteral = Literal["monday", "tuesday", "wednesday", "thursday", "friday", "saturday", "sunday"]
StatusLiteral = Literal["pending", "in_progress", "done", "discarded"]


class ActionCreate(BaseModel):
    order: int = 1
    description: str
    dod: str | None = None
    day: DayLiteral | None = None
    status: StatusLiteral = "pending"


class ActionUpdate(BaseModel):
    order: int | None = None
    description: str | None = None
    dod: str | None = None
    day: DayLiteral | None = None
    status: StatusLiteral | None = None


class ActionStatusUpdate(BaseModel):
    status: StatusLiteral


class ActionResponse(BaseModel):
    model_config = {"from_attributes": True}

    id: int
    full_task_id: int
    order: int
    description: str
    dod: str | None
    day: str | None
    status: str
