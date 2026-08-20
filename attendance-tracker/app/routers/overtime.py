"""Overtime request endpoints."""
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import joinedload

from ..database import get_db
from ..deps import get_current_user, require_admin
from ..models import OvertimeRequest, Person, User
from ..schemas import OvertimeCreate, OvertimeOut, OvertimeUpdate

router = APIRouter(prefix="/api/overtime", tags=["overtime"])


def ot_to_out(ot: OvertimeRequest) -> OvertimeOut:
    return OvertimeOut(
        id=ot.id,
        person_id=ot.person_id,
        person_name=ot.person.full_name if ot.person else None,
        date=ot.date,
        hours=ot.hours,
        reason=ot.reason,
        status=ot.status,
        approved_by=ot.approved_by,
        admin_note=ot.admin_note,
        created_at=ot.created_at,
    )


@router.get("", response_model=list[OvertimeOut])
async def list_overtime(
    person_id: int | None = None,
    status_filter: str | None = None,
    db: AsyncSession = Depends(get_db),
    user: User = Depends(get_current_user),
):
    query = select(OvertimeRequest).options(joinedload(OvertimeRequest.person)).order_by(OvertimeRequest.created_at.desc())
    if user.role != "admin":
        if user.person_id is None:
            return []
        query = query.where(OvertimeRequest.person_id == user.person_id)
    elif person_id:
        query = query.where(OvertimeRequest.person_id == person_id)
    if status_filter:
        query = query.where(OvertimeRequest.status == status_filter)
    result = await db.execute(query)
    return [ot_to_out(o) for o in result.scalars().all()]


@router.post("", response_model=OvertimeOut, status_code=status.HTTP_201_CREATED)
async def create_overtime(
    data: OvertimeCreate,
    db: AsyncSession = Depends(get_db),
    user: User = Depends(get_current_user),
):
    if user.person_id is None:
        raise HTTPException(status_code=400, detail="No linked person")
    ot = OvertimeRequest(
        person_id=user.person_id,
        date=data.date,
        hours=data.hours,
        reason=data.reason,
        status="pending",
    )
    db.add(ot)
    await db.commit()
    await db.refresh(ot, attribute_names=["person"])
    return ot_to_out(ot)


@router.patch("/{ot_id}", response_model=OvertimeOut)
async def update_overtime(
    ot_id: int,
    data: OvertimeUpdate,
    db: AsyncSession = Depends(get_db),
    admin: User = Depends(require_admin),
):
    ot = await db.get(OvertimeRequest, ot_id)
    if ot is None:
        raise HTTPException(status_code=404, detail="Overtime request not found")
    ot.status = data.status
    ot.approved_by = admin.id
    ot.admin_note = data.admin_note
    await db.commit()
    await db.refresh(ot, attribute_names=["person"])

    if ot.person and ot.person.email and data.status == "approved":
        from ..notifications import send_overtime_approved
        send_overtime_approved(ot.person.email, ot.person.full_name, str(ot.date), ot.hours)

    return ot_to_out(ot)
