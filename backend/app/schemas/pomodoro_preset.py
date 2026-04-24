from urllib.parse import parse_qs, urlparse

from pydantic import BaseModel, Field, field_validator


def _is_valid_youtube_url(url: str) -> bool:
    parsed = urlparse(url.strip())
    if parsed.scheme not in {"http", "https"}:
        return False

    host = (parsed.netloc or "").lower()
    allowed_hosts = {"youtube.com", "www.youtube.com", "m.youtube.com", "youtu.be", "www.youtu.be"}
    if host not in allowed_hosts:
        return False

    if host in {"youtu.be", "www.youtu.be"}:
        return bool(parsed.path.strip("/"))

    if parsed.path == "/watch":
        return bool(parse_qs(parsed.query).get("v", [""])[0])
    if parsed.path.startswith("/shorts/"):
        return bool(parsed.path.split("/shorts/", maxsplit=1)[1].strip("/"))
    if parsed.path.startswith("/embed/"):
        return bool(parsed.path.split("/embed/", maxsplit=1)[1].strip("/"))
    return False


class PomodoroPresetBase(BaseModel):
    name: str = Field(min_length=1, max_length=100)
    focus_minutes: int = Field(ge=1, le=180)
    short_break_minutes: int = Field(ge=1, le=60)
    long_break_minutes: int = Field(ge=1, le=120)
    cycles_before_long_break: int = Field(ge=1, le=12)
    music_url: str = Field(min_length=8, max_length=1024)

    @field_validator("music_url")
    @classmethod
    def validate_music_url(cls, value: str) -> str:
        v = value.strip()
        if not _is_valid_youtube_url(v):
            raise ValueError("music_url must be a valid YouTube URL")
        return v


class PomodoroPresetCreate(PomodoroPresetBase):
    pass


class PomodoroPresetUpdate(BaseModel):
    name: str | None = Field(default=None, min_length=1, max_length=100)
    focus_minutes: int | None = Field(default=None, ge=1, le=180)
    short_break_minutes: int | None = Field(default=None, ge=1, le=60)
    long_break_minutes: int | None = Field(default=None, ge=1, le=120)
    cycles_before_long_break: int | None = Field(default=None, ge=1, le=12)
    music_url: str | None = Field(default=None, min_length=8, max_length=1024)

    @field_validator("music_url")
    @classmethod
    def validate_music_url(cls, value: str | None) -> str | None:
        if value is None:
            return None
        v = value.strip()
        if not _is_valid_youtube_url(v):
            raise ValueError("music_url must be a valid YouTube URL")
        return v


class PomodoroPresetResponse(BaseModel):
    model_config = {"from_attributes": True}

    id: int
    user_id: int
    name: str
    focus_minutes: int
    short_break_minutes: int
    long_break_minutes: int
    cycles_before_long_break: int
    music_url: str
