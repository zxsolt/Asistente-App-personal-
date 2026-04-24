from fastapi import APIRouter, HTTPException, status
from sqlalchemy import select

from app.core.deps import DB, CurrentUser
from app.models.pool_task import PoolTask
from app.models.week import Week
from app.schemas.pool_task import PoolTaskCreate, PoolTaskResponse, PoolTaskUpdate

router = APIRouter(prefix="/weeks/{week_id}/pool-tasks", tags=["pool-tasks"])


async def _get_week(week_id: int, user_id: int, db: DB) -> Week:
    result = await db.execute(select(Week).where(Week.id == week_id))
    week = result.scalar_one_or_none()
    if not week or week.user_id != user_id:
        raise HTTPException(status_code=404, detail="Week not found")
    return week


@router.get("/", response_model=list[PoolTaskResponse])
async def list_pool_tasks(week_id: int, current_user: CurrentUser, db: DB) -> list[PoolTask]:
    await _get_week(week_id, current_user.id, db)
    result = await db.execute(select(PoolTask).where(PoolTask.week_id == week_id))
    return list(result.scalars().all())


@router.post("/", response_model=PoolTaskResponse, status_code=status.HTTP_201_CREATED)
async def create_pool_task(week_id: int, body: PoolTaskCreate, current_user: CurrentUser, db: DB) -> PoolTask:
    await _get_week(week_id, current_user.id, db)
    task = PoolTask(week_id=week_id, title=body.title, task_type=body.task_type)
    db.add(task)
    await db.commit()
    await db.refresh(task)
    return task


@router.patch("/{task_id}", response_model=PoolTaskResponse)
async def update_pool_task(week_id: int, task_id: int, body: PoolTaskUpdate, current_user: CurrentUser, db: DB) -> PoolTask:
    await _get_week(week_id, current_user.id, db)
    result = await db.execute(select(PoolTask).where(PoolTask.id == task_id, PoolTask.week_id == week_id))
    task = result.scalar_one_or_none()
    if not task:
        raise HTTPException(status_code=404, detail="Task not found")

    if body.title is not None:
        task.title = body.title
    if body.task_type is not None:
        task.task_type = body.task_type

    await db.commit()
    await db.refresh(task)
    return task


@router.delete("/{task_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_pool_task(week_id: int, task_id: int, current_user: CurrentUser, db: DB) -> None:
    await _get_week(week_id, current_user.id, db)
    result = await db.execute(select(PoolTask).where(PoolTask.id == task_id, PoolTask.week_id == week_id))
    task = result.scalar_one_or_none()
    if not task:
        raise HTTPException(status_code=404, detail="Task not found")
    await db.delete(task)
    await db.commit()
