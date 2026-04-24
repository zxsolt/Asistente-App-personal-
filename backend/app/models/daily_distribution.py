from sqlalchemy import ForeignKey, String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.database import Base


class DailyDistribution(Base):
    __tablename__ = "daily_distributions"

    id: Mapped[int] = mapped_column(primary_key=True)
    week_id: Mapped[int] = mapped_column(ForeignKey("weeks.id", ondelete="CASCADE"), index=True)
    day: Mapped[str] = mapped_column(String(15))  # monday..sunday
    day_type: Mapped[str | None] = mapped_column(String(20), nullable=True)  # work/study/rest
    # Comma-separated task names or JSON list stored as text
    task_assignments: Mapped[str | None] = mapped_column(Text, nullable=True)

    week: Mapped["Week"] = relationship(back_populates="daily_distributions")  # type: ignore[name-defined] # noqa: F821
