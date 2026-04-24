from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.note import Note


class NoteService:
    def __init__(self, db: AsyncSession):
        self.db = db

    async def create(
        self,
        *,
        user_id: int,
        content: str,
        category: str = "general",
        source: str = "web",
        source_ref: str | None = None,
    ) -> Note:
        note = Note(
            user_id=user_id,
            content=content,
            category=category,
            source=source,
            source_ref=source_ref,
        )
        self.db.add(note)
        await self.db.commit()
        await self.db.refresh(note)
        return note

    async def list_for_user(self, *, user_id: int, limit: int = 50) -> list[Note]:
        result = await self.db.execute(
            select(Note).where(Note.user_id == user_id).order_by(Note.created_at.desc()).limit(limit)
        )
        return list(result.scalars().all())
