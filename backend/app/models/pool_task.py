from sqlalchemy import ForeignKey, String
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.database import Base


class PoolTask(Base):
    __tablename__ = "pool_tasks"

    id: Mapped[int] = mapped_column(primary_key=True)
    week_id: Mapped[int] = mapped_column(ForeignKey("weeks.id", ondelete="CASCADE"), index=True)
    title: Mapped[str] = mapped_column(String(255))
    task_type: Mapped[str] = mapped_column(String(10))  # "work" | "study"

    week: Mapped["Week"] = relationship(back_populates="pool_tasks")  # type: ignore[name-defined] # noqa: F821
