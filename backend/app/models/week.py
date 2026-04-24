from datetime import date, datetime, timezone

from sqlalchemy import Date, DateTime, ForeignKey
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.database import Base


class Week(Base):
    __tablename__ = "weeks"

    id: Mapped[int] = mapped_column(primary_key=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id", ondelete="CASCADE"), index=True)
    start_date: Mapped[date] = mapped_column(Date)
    end_date: Mapped[date] = mapped_column(Date)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=lambda: datetime.now(timezone.utc)
    )

    user: Mapped["User"] = relationship(back_populates="weeks")  # type: ignore[name-defined] # noqa: F821
    pool_tasks: Mapped[list["PoolTask"]] = relationship(back_populates="week", cascade="all, delete-orphan")  # type: ignore[name-defined] # noqa: F821
    full_tasks: Mapped[list["FullTask"]] = relationship(back_populates="week", cascade="all, delete-orphan")  # type: ignore[name-defined] # noqa: F821
    daily_distributions: Mapped[list["DailyDistribution"]] = relationship(back_populates="week", cascade="all, delete-orphan")  # type: ignore[name-defined] # noqa: F821
    weekly_review: Mapped["WeeklyReview | None"] = relationship(back_populates="week", cascade="all, delete-orphan", uselist=False)  # type: ignore[name-defined] # noqa: F821
