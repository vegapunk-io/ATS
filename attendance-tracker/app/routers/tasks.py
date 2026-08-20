"""Task management endpoints."""
from datetime import datetime

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import joinedload

from ..database import get_db
from ..deps import get_current_user, require_admin
from ..models import Person, Task, User
from ..schemas import TaskCreate, TaskOut, TaskUpdate

router = APIRouter(prefix="/api/tasks", tags=["tasks"])


def task_to_out(t: Task) -> TaskOut:
    return TaskOut(
        id=t.id,
        title=t.title,
        description=t.description,
        assigned_to=t.assigned_to,
        assignee_name=t.assignee.full_name if t.assignee else None,
        assigned_by=t.assigned_by,
        creator_name=t.creator.full_name if t.creator else None,
        priority=t.priority,
        status=t.status,
        due_date=t.due_date,
        completed_at=t.completed_at,
        created_at=t.created_at,
    )


@router.get("", response_model=list[TaskOut])
async def list_tasks(
    status_filter: str | None = None,
    db: AsyncSession = Depends(get_db),
    user: User = Depends(get_current_user),
):
    query = select(Task).options(joinedload(Task.assignee), joinedload(Task.creator)).order_by(Task.created_at.desc())
    if user.role != "admin":
        if user.person_id is None:
            return []
        query = query.where(Task.assigned_to == user.person_id)
    if status_filter:
        query = query.where(Task.status == status_filter)
    result = await db.execute(query)
    return [task_to_out(t) for t in result.scalars().all()]


@router.post("", response_model=TaskOut, status_code=status.HTTP_201_CREATED)
async def create_task(
    data: TaskCreate,
    db: AsyncSession = Depends(get_db),
    user: User = Depends(get_current_user),
):
    task = Task(
        title=data.title,
        description=data.description,
        assigned_to=data.assigned_to,
        assigned_by=user.id,
        priority=data.priority,
        due_date=data.due_date,
        status="todo",
    )
    db.add(task)
    await db.commit()
    await db.refresh(task, attribute_names=["assignee", "creator"])
    return task_to_out(task)


@router.patch("/{task_id}", response_model=TaskOut)
async def update_task(
    task_id: int,
    data: TaskUpdate,
    db: AsyncSession = Depends(get_db),
    user: User = Depends(get_current_user),
):
    task = await db.get(Task, task_id)
    if task is None:
        raise HTTPException(status_code=404, detail="Task not found")

    if user.role != "admin" and task.assigned_to != user.person_id:
        raise HTTPException(status_code=403, detail="Not allowed")

    for field in ["title", "description", "assigned_to", "priority", "status", "due_date"]:
        val = getattr(data, field)
        if val is not None:
            setattr(task, field, val)

    if data.status == "done" and task.completed_at is None:
        task.completed_at = datetime.utcnow()
    elif data.status and data.status != "done":
        task.completed_at = None

    await db.commit()
    await db.refresh(task, attribute_names=["assignee", "creator"])
    return task_to_out(task)


@router.delete("/{task_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_task(
    task_id: int,
    db: AsyncSession = Depends(get_db),
    _: User = Depends(require_admin),
):
    task = await db.get(Task, task_id)
    if task is None:
        raise HTTPException(status_code=404, detail="Task not found")
    await db.delete(task)
    await db.commit()
