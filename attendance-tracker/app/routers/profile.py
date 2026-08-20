"""User profile endpoints."""
from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from ..database import get_db
from ..deps import get_current_user
from ..models import Person, User
from ..schemas import UserOut, PersonOut

router = APIRouter(prefix="/api/profile", tags=["profile"])


class ProfileUpdate(BaseModel):
    full_name: str | None = None
    email: str | None = None


@router.get("")
async def get_profile(
    db: AsyncSession = Depends(get_db),
    user: User = Depends(get_current_user),
):
    """Get current user's full profile with person details."""
    person = None
    if user.person_id:
        person = await db.get(Person, user.person_id)

    return {
        "user": UserOut.model_validate(user),
        "person": PersonOut.model_validate(person) if person else None,
    }


@router.patch("", response_model=UserOut)
async def update_profile(
    data: ProfileUpdate,
    db: AsyncSession = Depends(get_db),
    user: User = Depends(get_current_user),
):
    """Update current user's basic info."""
    if data.full_name is not None:
        user.full_name = data.full_name
    if data.email is not None:
        user.email = data.email if data.email else None
    await db.commit()
    await db.refresh(user)
    return user


@router.get("/stats")
async def get_profile_stats(
    db: AsyncSession = Depends(get_db),
    user: User = Depends(get_current_user),
):
    """Get current user's attendance stats."""
    from ..deps import today_local
    from datetime import date, timedelta
    from ..models import AttendanceRecord

    if not user.person_id:
        return {"streak": 0, "total_present": 0, "total_hours": 0, "attendance_rate": 0}

    today = today_local()
    first_of_month = today.replace(day=1)

    result = await db.execute(
        select(AttendanceRecord).where(
            AttendanceRecord.person_id == user.person_id,
            AttendanceRecord.date >= first_of_month,
            AttendanceRecord.date <= today,
        )
    )
    records = list(result.scalars().all())

    present = sum(1 for r in records if r.status == "present")
    half = sum(1 for r in records if r.status == "half_day")
    days_so_far = (today - first_of_month).days + 1
    rate = round((present + half) / days_so_far, 2) if days_so_far > 0 else 0

    total_mins = sum(
        int((r.check_out - r.check_in).total_seconds() // 60)
        for r in records if r.check_in and r.check_out
    )

    # Calculate streak
    streak = 0
    check_date = today
    all_result = await db.execute(
        select(AttendanceRecord).where(
            AttendanceRecord.person_id == user.person_id,
            AttendanceRecord.date <= today,
        ).order_by(AttendanceRecord.date.desc()).limit(60)
    )
    all_records = list(all_result.scalars().all())
    by_date = {r.date: r for r in all_records}

    if today in by_date and by_date[today].status in ("present", "half_day"):
        streak = 1
        check_date = today - timedelta(days=1)
    else:
        check_date = today - timedelta(days=1)

    while check_date in by_date:
        if by_date[check_date].status in ("present", "half_day"):
            streak += 1
            check_date -= timedelta(days=1)
        else:
            break

    return {
        "streak": streak,
        "total_present": present,
        "total_hours": round(total_mins / 60, 1),
        "attendance_rate": rate,
    }
