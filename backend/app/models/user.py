from datetime import datetime, timezone

from sqlalchemy import Boolean, DateTime, String
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.database import Base


class User(Base):
    __tablename__ = "users"

    id: Mapped[int] = mapped_column(primary_key=True)
    username: Mapped[str] = mapped_column(String(50), unique=True, index=True)
    email: Mapped[str] = mapped_column(String(255), unique=True, index=True)
    hashed_password: Mapped[str] = mapped_column(String(255))
    is_superuser: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False, server_default="0")
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=lambda: datetime.now(timezone.utc)
    )

    weeks: Mapped[list["Week"]] = relationship(back_populates="user", cascade="all, delete-orphan")  # type: ignore[name-defined] # noqa: F821
    pomodoro_presets: Mapped[list["PomodoroPreset"]] = relationship(  # type: ignore[name-defined] # noqa: F821
        back_populates="user",
        cascade="all, delete-orphan",
    )
    notes: Mapped[list["Note"]] = relationship(back_populates="user", cascade="all, delete-orphan")  # type: ignore[name-defined] # noqa: F821
    reminders: Mapped[list["Reminder"]] = relationship(back_populates="user", cascade="all, delete-orphan")  # type: ignore[name-defined] # noqa: F821
    telegram_links: Mapped[list["TelegramLink"]] = relationship(back_populates="user", cascade="all, delete-orphan")  # type: ignore[name-defined] # noqa: F821
