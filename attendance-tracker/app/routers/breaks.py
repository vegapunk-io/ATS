"""Break/lunch tracking endpoints."""
from datetime import datetime

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import joinedload

from ..database import get_db
from ..deps import get_app_tz, get_current_user, require_admin, today_local
from ..models import Break, Person, User
from ..schemas import BreakCreate, BreakOut

router = APIRouter(prefix="/api/breaks", tags=["breaks"])


def break_to_out(brk: Break) -> BreakOut:
    duration = None
    if brk.break_start and brk.break_end:
        duration = int((brk.break_end - brk.break_start).total_seconds() // 60)
    return BreakOut(
        id=brk.id,
        person_id=brk.person_id,
        person_name=brk.person.full_name if brk.person else None,
        date=brk.date,
        break_start=brk.break_start,
        break_end=brk.break_end,
        break_type=brk.break_type,
        duration_minutes=duration,
    )


@router.get("/today", response_model=list[BreakOut])
async def today_breaks(
    db: AsyncSession = Depends(get_db),
    user: User = Depends(get_current_user),
):
    """Get today's breaks for the current user."""
    if user.person_id is None:
        return []

    result = await db.execute(
        select(Break)
        .options(joinedload(Break.person))
        .where(
            Break.person_id == user.person_id,
            Break.date == today_local(),
        )
        .order_by(Break.break_start.desc())
    )
    return [break_to_out(b) for b in result.scalars().all()]


@router.post("/start", response_model=BreakOut, status_code=status.HTTP_201_CREATED)
async def start_break(
    data: BreakCreate,
    db: AsyncSession = Depends(get_db),
    user: User = Depends(get_current_user),
):
    """Start a break. Must not have an ongoing break."""
    if user.person_id is None:
        raise HTTPException(status_code=400, detail="No linked person")

    today = today_local()
    now = datetime.now(get_app_tz())

    # Check for ongoing break
    result = await db.execute(
        select(Break).where(
            Break.person_id == user.person_id,
            Break.date == today,
            Break.break_end.is_(None),
        )
    )
    ongoing = result.scalar_one_or_none()
    if ongoing:
        raise HTTPException(status_code=409, detail="You already have an ongoing break")

    brk = Break(
        person_id=user.person_id,
        date=today,
        break_start=now,
        break_type=data.break_type,
    )
    db.add(brk)
    await db.commit()
    await db.refresh(brk, attribute_names=["person"])
    return break_to_out(brk)


@router.post("/end", response_model=BreakOut)
async def end_break(
    db: AsyncSession = Depends(get_db),
    user: User = Depends(get_current_user),
):
    """End the current ongoing break."""
    if user.person_id is None:
        raise HTTPException(status_code=400, detail="No linked person")

    today = today_local()
    now = datetime.now(get_app_tz())

    result = await db.execute(
        select(Break).where(
            Break.person_id == user.person_id,
            Break.date == today,
            Break.break_end.is_(None),
        )
    )
    brk = result.scalar_one_or_none()
    if brk is None:
        raise HTTPException(status_code=409, detail="No ongoing break found")

    brk.break_end = now
    await db.commit()
    await db.refresh(brk, attribute_names=["person"])
    return break_to_out(brk)


@router.get("/status")
async def break_status(
    db: AsyncSession = Depends(get_db),
    user: User = Depends(get_current_user),
):
    """Check if user has an ongoing break."""
    if user.person_id is None:
        return {"on_break": False}

    today = today_local()
    result = await db.execute(
        select(Break).where(
            Break.person_id == user.person_id,
            Break.date == today,
            Break.break_end.is_(None),
        )
    )
    brk = result.scalar_one_or_none()
    if brk:
        return {"on_break": True, "break_id": brk.id, "break_type": brk.break_type, "started": brk.break_start}
    return {"on_break": False}
