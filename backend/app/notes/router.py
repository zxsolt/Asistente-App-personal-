from fastapi import APIRouter, Query, status

from app.core.deps import CurrentUser, DB
from app.notes.service import NoteService
from app.schemas.note import NoteCreate, NoteResponse

router = APIRouter(prefix="/notes", tags=["notes"])


@router.get("/", response_model=list[NoteResponse])
async def list_notes(
    current_user: CurrentUser,
    db: DB,
    limit: int = Query(default=50, ge=1, le=200),
) -> list[NoteResponse]:
    service = NoteService(db)
    return await service.list_for_user(user_id=current_user.id, limit=limit)


@router.post("/", response_model=NoteResponse, status_code=status.HTTP_201_CREATED)
async def create_note(body: NoteCreate, current_user: CurrentUser, db: DB) -> NoteResponse:
    service = NoteService(db)
    return await service.create(
        user_id=current_user.id,
        content=body.content,
        category=body.category,
        source=body.source,
        source_ref=body.source_ref,
    )
