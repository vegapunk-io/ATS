"""Shift swap/trade request endpoints."""
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import joinedload

from ..database import get_db
from ..deps import get_current_user, require_admin
from ..models import Person, ShiftSwap, User
from ..schemas import ShiftSwapCreate, ShiftSwapOut, ShiftSwapUpdate

router = APIRouter(prefix="/api/shift-swaps", tags=["shift-swaps"])


def swap_to_out(swap: ShiftSwap) -> ShiftSwapOut:
    return ShiftSwapOut(
        id=swap.id,
        requester_id=swap.requester_id,
        requester_name=swap.requester.full_name if swap.requester else None,
        target_id=swap.target_id,
        target_name=swap.target.full_name if swap.target else None,
        requester_date=swap.requester_date,
        target_date=swap.target_date,
        reason=swap.reason,
        status=swap.status,
        approved_by=swap.approved_by,
        admin_note=swap.admin_note,
        created_at=swap.created_at,
    )


@router.get("", response_model=list[ShiftSwapOut])
async def list_swaps(
    status_filter: str | None = None,
    db: AsyncSession = Depends(get_db),
    user: User = Depends(get_current_user),
):
    query = select(ShiftSwap).options(
        joinedload(ShiftSwap.requester), joinedload(ShiftSwap.target)
    ).order_by(ShiftSwap.created_at.desc())

    if user.role != "admin":
        if user.person_id is None:
            return []
        query = query.where(
            (ShiftSwap.requester_id == user.person_id) | (ShiftSwap.target_id == user.person_id)
        )
    if status_filter:
        query = query.where(ShiftSwap.status == status_filter)
    result = await db.execute(query)
    return [swap_to_out(s) for s in result.scalars().all()]


@router.post("", response_model=ShiftSwapOut, status_code=status.HTTP_201_CREATED)
async def create_swap(
    data: ShiftSwapCreate,
    db: AsyncSession = Depends(get_db),
    user: User = Depends(get_current_user),
):
    if user.person_id is None:
        raise HTTPException(status_code=400, detail="No linked person")
    swap = ShiftSwap(
        requester_id=user.person_id,
        target_id=data.target_id,
        requester_date=data.requester_date,
        target_date=data.target_date,
        reason=data.reason,
        status="pending",
    )
    db.add(swap)
    await db.commit()
    await db.refresh(swap, attribute_names=["requester", "target"])
    return swap_to_out(swap)


@router.patch("/{swap_id}", response_model=ShiftSwapOut)
async def update_swap(
    swap_id: int,
    data: ShiftSwapUpdate,
    db: AsyncSession = Depends(get_db),
    user: User = Depends(get_current_user),
):
    swap = await db.get(ShiftSwap, swap_id)
    if swap is None:
        raise HTTPException(status_code=404, detail="Shift swap not found")

    if user.role == "admin":
        swap.status = data.status
        swap.approved_by = user.id
        swap.admin_note = data.admin_note
    elif data.status == "cancelled" and swap.requester_id == user.person_id and swap.status == "pending":
        swap.status = "cancelled"
    else:
        raise HTTPException(status_code=403, detail="Not allowed")

    await db.commit()
    await db.refresh(swap, attribute_names=["requester", "target"])
    return swap_to_out(swap)
