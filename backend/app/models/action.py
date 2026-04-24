from sqlalchemy import ForeignKey, Integer, String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.database import Base


class Action(Base):
    __tablename__ = "actions"

    id: Mapped[int] = mapped_column(primary_key=True)
    full_task_id: Mapped[int] = mapped_column(ForeignKey("full_tasks.id", ondelete="CASCADE"), index=True)
    order: Mapped[int] = mapped_column(Integer, default=1)
    description: Mapped[str] = mapped_column(Text)
    dod: Mapped[str | None] = mapped_column(Text, nullable=True)
    day: Mapped[str | None] = mapped_column(String(15), nullable=True)  # "monday".."sunday"
    status: Mapped[str] = mapped_column(String(15), default="pending")  # pending|in_progress|done|discarded

    full_task: Mapped["FullTask"] = relationship(back_populates="actions")  # type: ignore[name-defined] # noqa: F821
