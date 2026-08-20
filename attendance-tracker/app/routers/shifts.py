"""Admin-only endpoints for managing shifts and assignments."""
from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy import select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession

from ..database import get_db
from ..deps import require_admin
from ..models import Person, Shift, ShiftAssignment
from ..schemas import (
    ShiftAssignmentCreate,
    ShiftAssignmentOut,
    ShiftAssignmentUpdate,
    ShiftCreate,
    ShiftOut,
    ShiftUpdate,
)

router = APIRouter(prefix="/api/shifts", tags=["shifts"])


# ==================== SHIFTS ====================
@router.get("", response_model=list[ShiftOut])
async def list_shifts(
    db: AsyncSession = Depends(get_db),
    _: Shift = Depends(require_admin),
):
    result = await db.execute(select(Shift).order_by(Shift.name))
    return list(result.scalars().all())


@router.post("", response_model=ShiftOut, status_code=status.HTTP_201_CREATED)
async def create_shift(
    data: ShiftCreate,
    db: AsyncSession = Depends(get_db),
    _: Shift = Depends(require_admin),
):
    shift = Shift(**data.model_dump())
    db.add(shift)
    try:
        await db.commit()
    except IntegrityError:
        await db.rollback()
        raise HTTPException(status_code=409, detail="Shift name already exists")
    await db.refresh(shift)
    return shift


@router.patch("/{shift_id}", response_model=ShiftOut)
async def update_shift(
    shift_id: int,
    data: ShiftUpdate,
    db: AsyncSession = Depends(get_db),
    _: Shift = Depends(require_admin),
):
    shift = await db.get(Shift, shift_id)
    if shift is None:
        raise HTTPException(status_code=404, detail="Shift not found")
    for field, value in data.model_dump(exclude_unset=True).items():
        setattr(shift, field, value)
    try:
        await db.commit()
    except IntegrityError:
        await db.rollback()
        raise HTTPException(status_code=409, detail="Shift name already exists")
    await db.refresh(shift)
    return shift


@router.delete("/{shift_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_shift(
    shift_id: int,
    db: AsyncSession = Depends(get_db),
    _: Shift = Depends(require_admin),
):
    shift = await db.get(Shift, shift_id)
    if shift is None:
        raise HTTPException(status_code=404, detail="Shift not found")
    await db.delete(shift)
    await db.commit()


# ==================== ASSIGNMENTS ====================
@router.get("/assignments", response_model=list[ShiftAssignmentOut])
async def list_assignments(
    person_id: int | None = None,
    active_only: bool = False,
    db: AsyncSession = Depends(get_db),
    _: Shift = Depends(require_admin),
):
    query = select(ShiftAssignment).order_by(ShiftAssignment.start_date.desc())
    if person_id:
        query = query.where(ShiftAssignment.person_id == person_id)
    if active_only:
        query = query.where(ShiftAssignment.is_active.is_(True))
    result = await db.execute(query)
    assignments = list(result.scalars().all())

    # Enrich with names
    out = []
    for a in assignments:
        person = await db.get(Person, a.person_id)
        shift = await db.get(Shift, a.shift_id)
        out.append(
            ShiftAssignmentOut(
                id=a.id,
                person_id=a.person_id,
                person_name=person.full_name if person else None,
                shift_id=a.shift_id,
                shift_name=shift.name if shift else None,
                start_date=a.start_date,
                end_date=a.end_date,
                is_active=a.is_active,
            )
        )
    return out


@router.post("/assignments", response_model=ShiftAssignmentOut, status_code=status.HTTP_201_CREATED)
async def create_assignment(
    data: ShiftAssignmentCreate,
    db: AsyncSession = Depends(get_db),
    _: Shift = Depends(require_admin),
):
    person = await db.get(Person, data.person_id)
    if person is None:
        raise HTTPException(status_code=404, detail="Person not found")
    shift = await db.get(Shift, data.shift_id)
    if shift is None:
        raise HTTPException(status_code=404, detail="Shift not found")

    assignment = ShiftAssignment(**data.model_dump())
    db.add(assignment)
    await db.commit()
    await db.refresh(assignment)

    return ShiftAssignmentOut(
        id=assignment.id,
        person_id=assignment.person_id,
        person_name=person.full_name,
        shift_id=assignment.shift_id,
        shift_name=shift.name,
        start_date=assignment.start_date,
        end_date=assignment.end_date,
        is_active=assignment.is_active,
    )


@router.patch("/assignments/{assignment_id}", response_model=ShiftAssignmentOut)
async def update_assignment(
    assignment_id: int,
    data: ShiftAssignmentUpdate,
    db: AsyncSession = Depends(get_db),
    _: Shift = Depends(require_admin),
):
    assignment = await db.get(ShiftAssignment, assignment_id)
    if assignment is None:
        raise HTTPException(status_code=404, detail="Assignment not found")
    for field, value in data.model_dump(exclude_unset=True).items():
        setattr(assignment, field, value)
    await db.commit()
    await db.refresh(assignment)

    person = await db.get(Person, assignment.person_id)
    shift = await db.get(Shift, assignment.shift_id)
    return ShiftAssignmentOut(
        id=assignment.id,
        person_id=assignment.person_id,
        person_name=person.full_name if person else None,
        shift_id=assignment.shift_id,
        shift_name=shift.name if shift else None,
        start_date=assignment.start_date,
        end_date=assignment.end_date,
        is_active=assignment.is_active,
    )


@router.delete("/assignments/{assignment_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_assignment(
    assignment_id: int,
    db: AsyncSession = Depends(get_db),
    _: Shift = Depends(require_admin),
):
    assignment = await db.get(ShiftAssignment, assignment_id)
    if assignment is None:
        raise HTTPException(status_code=404, detail="Assignment not found")
    await db.delete(assignment)
    await db.commit()
