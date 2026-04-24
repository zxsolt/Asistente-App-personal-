from datetime import datetime

from pydantic import BaseModel, Field


class NoteCreate(BaseModel):
    content: str = Field(min_length=1, max_length=8000)
    category: str = Field(default="general", min_length=1, max_length=50)
    source: str = Field(default="web", min_length=1, max_length=32)
    source_ref: str | None = Field(default=None, max_length=255)


class NoteResponse(BaseModel):
    model_config = {"from_attributes": True}

    id: int
    user_id: int
    content: str
    category: str
    source: str
    source_ref: str | None
    created_at: datetime
    updated_at: datetime
