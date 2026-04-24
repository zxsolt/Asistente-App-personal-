from datetime import datetime

from sqlalchemy import Boolean, DateTime, ForeignKey, Integer, String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.database import Base


class FullTask(Base):
    __tablename__ = "full_tasks"

    id: Mapped[int] = mapped_column(primary_key=True)
    week_id: Mapped[int] = mapped_column(ForeignKey("weeks.id", ondelete="CASCADE"), index=True)
    name: Mapped[str] = mapped_column(String(255))
    task_type: Mapped[str] = mapped_column(String(10))  # "work" | "study"
    goal: Mapped[str | None] = mapped_column(Text, nullable=True)
    milestone: Mapped[str | None] = mapped_column(Text, nullable=True)
    milestone_dod: Mapped[str | None] = mapped_column(Text, nullable=True)
    time_budget_minutes: Mapped[int | None] = mapped_column(Integer, nullable=True)
    time_spent_seconds: Mapped[int] = mapped_column(Integer, nullable=False, default=0, server_default="0")
    limit_mode: Mapped[str] = mapped_column(String(10), nullable=False, default="warn", server_default="warn")
    completed: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False, server_default="0")
    priority: Mapped[str | None] = mapped_column(String(10), nullable=True)
    due_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    source: Mapped[str | None] = mapped_column(String(32), nullable=True)
    source_ref: Mapped[str | None] = mapped_column(String(255), nullable=True)
    natural_language_input: Mapped[str | None] = mapped_column(Text, nullable=True)

    week: Mapped["Week"] = relationship(back_populates="full_tasks")  # type: ignore[name-defined] # noqa: F821
    actions: Mapped[list["Action"]] = relationship(back_populates="full_task", cascade="all, delete-orphan", order_by="Action.order")  # type: ignore[name-defined] # noqa: F821
