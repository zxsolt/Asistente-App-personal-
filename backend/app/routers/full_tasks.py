from fastapi import APIRouter, HTTPException, status
from sqlalchemy import select
from sqlalchemy.orm import selectinload

from app.core.deps import DB, CurrentUser
from app.models.full_task import FullTask
from app.models.week import Week
from app.schemas.full_task import FocusLogCreate, FullTaskCreate, FullTaskResponse, FullTaskUpdate

router = APIRouter(prefix="/weeks/{week_id}/tasks", tags=["full-tasks"])


async def _get_week(week_id: int, user_id: int, db: DB) -> Week:
    result = await db.execute(select(Week).where(Week.id == week_id))
    week = result.scalar_one_or_none()
    if not week or week.user_id != user_id:
        raise HTTPException(status_code=404, detail="Week not found")
    return week


@router.get("/", response_model=list[FullTaskResponse])
async def list_tasks(week_id: int, current_user: CurrentUser, db: DB) -> list[FullTask]:
    await _get_week(week_id, current_user.id, db)
    result = await db.execute(
        select(FullTask)
        .where(FullTask.week_id == week_id)
        .options(selectinload(FullTask.actions))
    )
    return list(result.scalars().all())


@router.post("/", response_model=FullTaskResponse, status_code=status.HTTP_201_CREATED)
async def create_task(week_id: int, body: FullTaskCreate, current_user: CurrentUser, db: DB) -> FullTask:
    await _get_week(week_id, current_user.id, db)
    task = FullTask(
        week_id=week_id,
        name=body.name,
        task_type=body.task_type,
        goal=body.goal,
        milestone=body.milestone,
        milestone_dod=body.milestone_dod,
        time_budget_minutes=body.time_budget_minutes,
        limit_mode=body.limit_mode,
        priority=body.priority,
        due_at=body.due_at,
        source=body.source,
        source_ref=body.source_ref,
        natural_language_input=body.natural_language_input,
    )
    db.add(task)
    await db.commit()
    await db.refresh(task)
    # reload with actions
    result = await db.execute(
        select(FullTask).where(FullTask.id == task.id).options(selectinload(FullTask.actions))
    )
    return result.scalar_one()


@router.get("/{task_id}", response_model=FullTaskResponse)
async def get_task(week_id: int, task_id: int, current_user: CurrentUser, db: DB) -> FullTask:
    await _get_week(week_id, current_user.id, db)
    result = await db.execute(
        select(FullTask)
        .where(FullTask.id == task_id, FullTask.week_id == week_id)
        .options(selectinload(FullTask.actions))
    )
    task = result.scalar_one_or_none()
    if not task:
        raise HTTPException(status_code=404, detail="Task not found")
    return task


@router.patch("/{task_id}", response_model=FullTaskResponse)
async def update_task(week_id: int, task_id: int, body: FullTaskUpdate, current_user: CurrentUser, db: DB) -> FullTask:
    await _get_week(week_id, current_user.id, db)
    result = await db.execute(
        select(FullTask)
        .where(FullTask.id == task_id, FullTask.week_id == week_id)
        .options(selectinload(FullTask.actions))
    )
    task = result.scalar_one_or_none()
    if not task:
        raise HTTPException(status_code=404, detail="Task not found")

    for field, value in body.model_dump(exclude_unset=True).items():
        setattr(task, field, value)

    await db.commit()
    await db.refresh(task)
    result = await db.execute(
        select(FullTask).where(FullTask.id == task.id).options(selectinload(FullTask.actions))
    )
    return result.scalar_one()


@router.delete("/{task_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_task(week_id: int, task_id: int, current_user: CurrentUser, db: DB) -> None:
    await _get_week(week_id, current_user.id, db)
    result = await db.execute(select(FullTask).where(FullTask.id == task_id, FullTask.week_id == week_id))
    task = result.scalar_one_or_none()
    if not task:
        raise HTTPException(status_code=404, detail="Task not found")
    await db.delete(task)
    await db.commit()


@router.post("/{task_id}/log-focus", response_model=FullTaskResponse)
async def log_focus(
    week_id: int,
    task_id: int,
    body: FocusLogCreate,
    current_user: CurrentUser,
    db: DB,
) -> FullTask:
    await _get_week(week_id, current_user.id, db)
    result = await db.execute(
        select(FullTask)
        .where(FullTask.id == task_id, FullTask.week_id == week_id)
        .options(selectinload(FullTask.actions))
    )
    task = result.scalar_one_or_none()
    if not task:
        raise HTTPException(status_code=404, detail="Task not found")

    task.time_spent_seconds = (task.time_spent_seconds or 0) + body.seconds
    await db.commit()
    await db.refresh(task)
    result = await db.execute(
        select(FullTask).where(FullTask.id == task.id).options(selectinload(FullTask.actions))
    )
    return result.scalar_one()
