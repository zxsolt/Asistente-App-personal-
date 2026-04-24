from fastapi import APIRouter, HTTPException, status
from sqlalchemy import select
from sqlalchemy.orm import selectinload

from app.core.deps import DB, CurrentUser
from app.models.action import Action
from app.models.full_task import FullTask
from app.models.week import Week
from app.schemas.action import ActionCreate, ActionResponse, ActionStatusUpdate, ActionUpdate

router = APIRouter(prefix="/tasks/{task_id}/actions", tags=["actions"])


async def _get_task(task_id: int, user_id: int, db: DB) -> FullTask:
    result = await db.execute(
        select(FullTask)
        .where(FullTask.id == task_id)
        .options(selectinload(FullTask.week))
    )
    task = result.scalar_one_or_none()
    if not task:
        raise HTTPException(status_code=404, detail="Task not found")
    # verify ownership via week
    week_result = await db.execute(select(Week).where(Week.id == task.week_id))
    week = week_result.scalar_one_or_none()
    if not week or week.user_id != user_id:
        raise HTTPException(status_code=404, detail="Task not found")
    return task


@router.get("/", response_model=list[ActionResponse])
async def list_actions(task_id: int, current_user: CurrentUser, db: DB) -> list[Action]:
    await _get_task(task_id, current_user.id, db)
    result = await db.execute(
        select(Action).where(Action.full_task_id == task_id).order_by(Action.order)
    )
    return list(result.scalars().all())


@router.post("/", response_model=ActionResponse, status_code=status.HTTP_201_CREATED)
async def create_action(task_id: int, body: ActionCreate, current_user: CurrentUser, db: DB) -> Action:
    await _get_task(task_id, current_user.id, db)
    action = Action(
        full_task_id=task_id,
        order=body.order,
        description=body.description,
        dod=body.dod,
        day=body.day,
        status=body.status,
    )
    db.add(action)
    await db.commit()
    await db.refresh(action)
    return action


@router.patch("/{action_id}", response_model=ActionResponse)
async def update_action(task_id: int, action_id: int, body: ActionUpdate, current_user: CurrentUser, db: DB) -> Action:
    await _get_task(task_id, current_user.id, db)
    result = await db.execute(
        select(Action).where(Action.id == action_id, Action.full_task_id == task_id)
    )
    action = result.scalar_one_or_none()
    if not action:
        raise HTTPException(status_code=404, detail="Action not found")

    for field, value in body.model_dump(exclude_none=True).items():
        setattr(action, field, value)

    await db.commit()
    await db.refresh(action)
    return action


@router.patch("/{action_id}/status", response_model=ActionResponse)
async def update_action_status(task_id: int, action_id: int, body: ActionStatusUpdate, current_user: CurrentUser, db: DB) -> Action:
    await _get_task(task_id, current_user.id, db)
    result = await db.execute(
        select(Action).where(Action.id == action_id, Action.full_task_id == task_id)
    )
    action = result.scalar_one_or_none()
    if not action:
        raise HTTPException(status_code=404, detail="Action not found")

    action.status = body.status
    await db.commit()
    await db.refresh(action)
    return action


@router.delete("/{action_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_action(task_id: int, action_id: int, current_user: CurrentUser, db: DB) -> None:
    await _get_task(task_id, current_user.id, db)
    result = await db.execute(
        select(Action).where(Action.id == action_id, Action.full_task_id == task_id)
    )
    action = result.scalar_one_or_none()
    if not action:
        raise HTTPException(status_code=404, detail="Action not found")
    await db.delete(action)
    await db.commit()
