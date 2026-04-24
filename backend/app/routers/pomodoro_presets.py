from fastapi import APIRouter, HTTPException, status
from sqlalchemy import select

from app.core.deps import CurrentUser, DB
from app.models.pomodoro_preset import PomodoroPreset
from app.schemas.pomodoro_preset import (
    PomodoroPresetCreate,
    PomodoroPresetResponse,
    PomodoroPresetUpdate,
)

router = APIRouter(prefix="/pomodoro-presets", tags=["pomodoro-presets"])


async def _owned_or_404(preset_id: int, user_id: int, db: DB) -> PomodoroPreset:
    result = await db.execute(select(PomodoroPreset).where(PomodoroPreset.id == preset_id))
    preset = result.scalar_one_or_none()
    if not preset or preset.user_id != user_id:
        raise HTTPException(status_code=404, detail="Pomodoro preset not found")
    return preset


@router.get("/", response_model=list[PomodoroPresetResponse])
async def list_presets(current_user: CurrentUser, db: DB) -> list[PomodoroPreset]:
    result = await db.execute(
        select(PomodoroPreset)
        .where(PomodoroPreset.user_id == current_user.id)
        .order_by(PomodoroPreset.created_at.desc())
    )
    return list(result.scalars().all())


@router.post("/", response_model=PomodoroPresetResponse, status_code=status.HTTP_201_CREATED)
async def create_preset(body: PomodoroPresetCreate, current_user: CurrentUser, db: DB) -> PomodoroPreset:
    preset = PomodoroPreset(
        user_id=current_user.id,
        name=body.name.strip(),
        focus_minutes=body.focus_minutes,
        short_break_minutes=body.short_break_minutes,
        long_break_minutes=body.long_break_minutes,
        cycles_before_long_break=body.cycles_before_long_break,
        music_url=body.music_url.strip(),
    )
    db.add(preset)
    await db.commit()
    await db.refresh(preset)
    return preset


@router.patch("/{preset_id}", response_model=PomodoroPresetResponse)
async def update_preset(
    preset_id: int,
    body: PomodoroPresetUpdate,
    current_user: CurrentUser,
    db: DB,
) -> PomodoroPreset:
    preset = await _owned_or_404(preset_id, current_user.id, db)
    updates = body.model_dump(exclude_none=True)
    for field, value in updates.items():
        if isinstance(value, str):
            value = value.strip()
        setattr(preset, field, value)
    await db.commit()
    await db.refresh(preset)
    return preset


@router.delete("/{preset_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_preset(preset_id: int, current_user: CurrentUser, db: DB) -> None:
    preset = await _owned_or_404(preset_id, current_user.id, db)
    await db.delete(preset)
    await db.commit()
