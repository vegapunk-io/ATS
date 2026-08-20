"""Leave management endpoints."""
from datetime import date

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import joinedload

from ..database import get_db
from ..deps import get_current_user, require_admin, today_local
from ..models import Leave, Person, User
from ..schemas import LeaveCreate, LeaveOut, LeaveUpdate

router = APIRouter(prefix="/api/leaves", tags=["leaves"])


def leave_to_out(leave: Leave) -> LeaveOut:
    return LeaveOut(
        id=leave.id,
        person_id=leave.person_id,
        person_name=leave.person.full_name if leave.person else None,
        leave_type=leave.leave_type,
        start_date=leave.start_date,
        end_date=leave.end_date,
        reason=leave.reason,
        status=leave.status,
        approved_by=leave.approved_by,
        admin_note=leave.admin_note,
        created_at=leave.created_at,
    )


@router.get("", response_model=list[LeaveOut])
async def list_leaves(
    person_id: int | None = None,
    status_filter: str | None = Query(default=None, alias="status"),
    db: AsyncSession = Depends(get_db),
    user: User = Depends(get_current_user),
):
    """List leave requests. Regular users see only their own."""
    query = select(Leave).options(joinedload(Leave.person)).order_by(Leave.created_at.desc())

    if user.role != "admin":
        if user.person_id is None:
            return []
        query = query.where(Leave.person_id == user.person_id)
    elif person_id:
        query = query.where(Leave.person_id == person_id)

    if status_filter:
        query = query.where(Leave.status == status_filter)

    result = await db.execute(query)
    return [leave_to_out(l) for l in result.scalars().all()]


@router.post("", response_model=LeaveOut, status_code=status.HTTP_201_CREATED)
async def create_leave(
    data: LeaveCreate,
    db: AsyncSession = Depends(get_db),
    user: User = Depends(get_current_user),
):
    """Create a leave request."""
    if user.person_id is None:
        raise HTTPException(status_code=400, detail="No linked person")

    if data.end_date < data.start_date:
        raise HTTPException(status_code=400, detail="end_date must be >= start_date")

    leave = Leave(
        person_id=user.person_id,
        leave_type=data.leave_type,
        start_date=data.start_date,
        end_date=data.end_date,
        reason=data.reason,
        status="pending",
    )
    db.add(leave)
    await db.commit()
    await db.refresh(leave, attribute_names=["person"])
    return leave_to_out(leave)


@router.patch("/{leave_id}", response_model=LeaveOut)
async def update_leave(
    leave_id: int,
    data: LeaveUpdate,
    db: AsyncSession = Depends(get_db),
    admin: User = Depends(require_admin),
):
    """Admin: approve or reject a leave request."""
    leave = await db.get(Leave, leave_id)
    if leave is None:
        raise HTTPException(status_code=404, detail="Leave not found")

    leave.status = data.status
    leave.approved_by = admin.id
    leave.admin_note = data.admin_note
    await db.commit()
    await db.refresh(leave, attribute_names=["person"])

    if leave.person and leave.person.email:
        from ..notifications import send_leave_approved, send_leave_rejected
        name = leave.person.full_name
        email = leave.person.email
        ltype = leave.leave_type
        sdate = str(leave.start_date)
        edate = str(leave.end_date)
        if data.status == "approved":
            send_leave_approved(email, name, ltype, sdate, edate)
        elif data.status == "rejected":
            send_leave_rejected(email, name, ltype, sdate, edate, data.admin_note)

    return leave_to_out(leave)


@router.delete("/{leave_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_leave(
    leave_id: int,
    db: AsyncSession = Depends(get_db),
    user: User = Depends(get_current_user),
):
    """Delete a leave request (own pending or admin any)."""
    leave = await db.get(Leave, leave_id)
    if leave is None:
        raise HTTPException(status_code=404, detail="Leave not found")

    if user.role != "admin" and leave.person_id != user.person_id:
        raise HTTPException(status_code=403, detail="Not allowed")
    if user.role != "admin" and leave.status != "pending":
        raise HTTPException(status_code=400, detail="Can only delete pending leaves")

    await db.delete(leave)
    await db.commit()
