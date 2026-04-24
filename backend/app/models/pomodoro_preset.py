from datetime import datetime, timezone

from sqlalchemy import DateTime, ForeignKey, Integer, String
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.database import Base


class PomodoroPreset(Base):
    __tablename__ = "pomodoro_presets"

    id: Mapped[int] = mapped_column(primary_key=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id", ondelete="CASCADE"), index=True)
    name: Mapped[str] = mapped_column(String(100))
    focus_minutes: Mapped[int] = mapped_column(Integer, nullable=False, default=25, server_default="25")
    short_break_minutes: Mapped[int] = mapped_column(Integer, nullable=False, default=5, server_default="5")
    long_break_minutes: Mapped[int] = mapped_column(Integer, nullable=False, default=15, server_default="15")
    cycles_before_long_break: Mapped[int] = mapped_column(Integer, nullable=False, default=4, server_default="4")
    music_url: Mapped[str] = mapped_column(String(1024))
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=lambda: datetime.now(timezone.utc)
    )

    user: Mapped["User"] = relationship(back_populates="pomodoro_presets")  # type: ignore[name-defined] # noqa: F821
