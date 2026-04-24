from sqlalchemy import ForeignKey, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.database import Base


class WeeklyReview(Base):
    __tablename__ = "weekly_reviews"

    id: Mapped[int] = mapped_column(primary_key=True)
    week_id: Mapped[int] = mapped_column(ForeignKey("weeks.id", ondelete="CASCADE"), unique=True)
    closed_this_week: Mapped[str | None] = mapped_column(Text, nullable=True)
    pending_why: Mapped[str | None] = mapped_column(Text, nullable=True)
    moving_to_next_week: Mapped[str | None] = mapped_column(Text, nullable=True)

    week: Mapped["Week"] = relationship(back_populates="weekly_review")  # type: ignore[name-defined] # noqa: F821
