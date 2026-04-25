from datetime import date, datetime
from enum import Enum
from typing import Any

from pydantic import BaseModel, Field

from app.planner.schemas import PlanningJson


class AssistantChannel(str, Enum):
    WEB = "web"
    TELEGRAM = "telegram"


class AssistantIntent(str, Enum):
    TASK_CREATE = "task_create"
    TASK_QUERY = "task_query"
    NOTE_CREATE = "note_create"
    REMINDER_CREATE = "reminder_create"
    WEEK_CREATE = "week_create"
    GENERAL_QUERY = "general_query"
    UNKNOWN = "unknown"


class AssistantMessageRequest(BaseModel):
    message: str = Field(min_length=1, max_length=4000)
    channel: AssistantChannel = AssistantChannel.WEB
    metadata: dict[str, Any] = Field(default_factory=dict)


class AssistantMessageResponse(BaseModel):
    reply_text: str
    intent: AssistantIntent
    action_taken: str
    entities: dict[str, Any] = Field(default_factory=dict)
    used_ai: bool = False
    persistence_mode: str = "none"
    planning_json: PlanningJson | None = None


class ParsedTemporalContext(BaseModel):
    due_at: datetime | None = None
    range_start: date | None = None
    range_end: date | None = None
    matched_phrase: str | None = None
