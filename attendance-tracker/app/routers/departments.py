"""Department management endpoints."""
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import select, func
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import joinedload

from ..database import get_db
from ..deps import get_current_user, require_admin
from ..models import Department, Person, User
from ..schemas import DepartmentCreate, DepartmentOut, DepartmentUpdate

router = APIRouter(prefix="/api/departments", tags=["departments"])


async def dept_to_out(dept: Department, db: AsyncSession) -> DepartmentOut:
    head_name = None
    if dept.head_id:
        head = await db.get(Person, dept.head_id)
        head_name = head.full_name if head else None

    result = await db.execute(
        select(func.count()).where(Person.group_name == dept.name)
    )
    member_count = result.scalar() or 0

    return DepartmentOut(
        id=dept.id,
        name=dept.name,
        description=dept.description,
        head_id=dept.head_id,
        head_name=head_name,
        is_active=dept.is_active,
        member_count=member_count,
        created_at=dept.created_at,
    )


@router.get("", response_model=list[DepartmentOut])
async def list_departments(
    db: AsyncSession = Depends(get_db),
    _: User = Depends(get_current_user),
):
    result = await db.execute(select(Department).order_by(Department.name))
    depts = result.scalars().all()
    return [await dept_to_out(d, db) for d in depts]


@router.post("", response_model=DepartmentOut, status_code=status.HTTP_201_CREATED)
async def create_department(
    data: DepartmentCreate,
    db: AsyncSession = Depends(get_db),
    _: User = Depends(require_admin),
):
    existing = await db.execute(select(Department).where(Department.name == data.name))
    if existing.scalar_one_or_none():
        raise HTTPException(status_code=409, detail="Department already exists")

    dept = Department(**data.model_dump())
    db.add(dept)
    await db.commit()
    await db.refresh(dept)
    return await dept_to_out(dept, db)


@router.patch("/{dept_id}", response_model=DepartmentOut)
async def update_department(
    dept_id: int,
    data: DepartmentUpdate,
    db: AsyncSession = Depends(get_db),
    _: User = Depends(require_admin),
):
    dept = await db.get(Department, dept_id)
    if dept is None:
        raise HTTPException(status_code=404, detail="Department not found")

    for field, value in data.model_dump(exclude_unset=True).items():
        setattr(dept, field, value)
    await db.commit()
    await db.refresh(dept)
    return await dept_to_out(dept, db)


@router.delete("/{dept_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_department(
    dept_id: int,
    db: AsyncSession = Depends(get_db),
    _: User = Depends(require_admin),
):
    dept = await db.get(Department, dept_id)
    if dept is None:
        raise HTTPException(status_code=404, detail="Department not found")
    await db.delete(dept)
    await db.commit()
