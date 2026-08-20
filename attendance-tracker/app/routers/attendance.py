"""Attendance endpoints: check-in/check-out, records, admin management."""
from datetime import date, datetime, timedelta

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy import select, func
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import joinedload

from ..database import get_db
from ..deps import get_app_tz, get_current_user, require_admin, today_local
from ..models import AttendanceRecord, Person, User, Shift, ShiftAssignment
from ..schemas import (
    AttendanceCreate,
    AttendanceOut,
    AttendanceUpdate,
    DashboardStats,
    TeamMember,
)

router = APIRouter(prefix="/api/attendance", tags=["attendance"])


def record_to_out(record: AttendanceRecord) -> AttendanceOut:
    """Serialize a record with joined person info and computed duration."""
    duration = None
    if record.check_in and record.check_out:
        duration = int((record.check_out - record.check_in).total_seconds() // 60)
    return AttendanceOut(
        id=record.id,
        person_id=record.person_id,
        person_name=record.person.full_name if record.person else None,
        group_name=record.person.group_name if record.person else None,
        date=record.date,
        check_in=record.check_in,
        check_out=record.check_out,
        status=record.status,
        note=record.note,
        duration_minutes=duration,
    )


async def resolve_person(
    user: User,
    person_id: int | None,
    db: AsyncSession,
) -> Person:
    """Return the person this action applies to.

    Admins may act on any person (via person_id); otherwise the user's own
    linked person is used. Non-admins can never act on another person.
    """
    if user.role == "admin" and person_id is not None:
        person = await db.get(Person, person_id)
        if person is None:
            raise HTTPException(status_code=404, detail="Person not found")
    elif user.person_id is not None:
        person = await db.get(Person, user.person_id)
        if person is None:
            raise HTTPException(status_code=404, detail="Linked person not found")
    else:
        raise HTTPException(
            status_code=400,
            detail="person_id is required (or link your account to a person)",
        )

    if not person.is_active:
        raise HTTPException(status_code=400, detail="Person is inactive")
    return person


async def get_record_or_404(record_id: int, db: AsyncSession) -> AttendanceRecord:
    record = await db.get(AttendanceRecord, record_id)
    if record is None:
        raise HTTPException(status_code=404, detail="Attendance record not found")
    return record


@router.get("", response_model=list[AttendanceOut])
async def list_attendance(
    person_id: int | None = None,
    group: str | None = None,
    date_from: date | None = None,
    date_to: date | None = None,
    status: str | None = Query(default=None, pattern="^(present|absent|half_day|holiday)$"),
    limit: int = Query(default=100, le=1000),
    offset: int = 0,
    db: AsyncSession = Depends(get_db),
    user: User = Depends(get_current_user),
):
    """List attendance records.

    Regular users only ever see records for their own linked person.
    """
    query = select(AttendanceRecord).options(
        joinedload(AttendanceRecord.person)
    ).order_by(
        AttendanceRecord.date.desc(), AttendanceRecord.check_in.desc()
    )

    if user.role != "admin":
        if user.person_id is None:
            return []
        query = query.where(AttendanceRecord.person_id == user.person_id)
    elif person_id is not None:
        query = query.where(AttendanceRecord.person_id == person_id)

    if group:
        query = query.join(Person).where(Person.group_name == group)
    if date_from:
        query = query.where(AttendanceRecord.date >= date_from)
    if date_to:
        query = query.where(AttendanceRecord.date <= date_to)
    if status:
        query = query.where(AttendanceRecord.status == status)

    result = await db.execute(query.limit(min(limit, 1000)).offset(max(offset, 0)))
    return [record_to_out(r) for r in result.scalars().all()]


@router.get("/today", response_model=AttendanceOut | None)
async def today_record(
    db: AsyncSession = Depends(get_db),
    user: User = Depends(get_current_user),
):
    """The current user's record for today (or None if not yet recorded)."""
    if user.person_id is None:
        return None
    result = await db.execute(
        select(AttendanceRecord)
        .options(joinedload(AttendanceRecord.person))
        .where(
            AttendanceRecord.person_id == user.person_id,
            AttendanceRecord.date == today_local(),
        )
    )
    record = result.scalar_one_or_none()
    return record_to_out(record) if record else None


@router.post("/check-in", response_model=AttendanceOut)
async def check_in(
    person_id: int | None = None,
    db: AsyncSession = Depends(get_db),
    user: User = Depends(get_current_user),
):
    """Check in. Creates today's record (or updates it) for the person."""
    person = await resolve_person(user, person_id, db)
    today = today_local()
    now = datetime.now(get_app_tz())

    result = await db.execute(
        select(AttendanceRecord).where(
            AttendanceRecord.person_id == person.id,
            AttendanceRecord.date == today,
        )
    )
    record = result.scalar_one_or_none()

    if record is None:
        record = AttendanceRecord(
            person_id=person.id, date=today, check_in=now, status="present"
        )
        db.add(record)
    elif record.check_in is not None:
        raise HTTPException(
            status_code=409,
            detail=f"Already checked in at {record.check_in.isoformat()}",
        )
    else:
        record.check_in = now
        record.status = "present"

    await db.commit()
    await db.refresh(record, attribute_names=["person"])
    return record_to_out(record)


@router.post("/check-out", response_model=AttendanceOut)
async def check_out(
    person_id: int | None = None,
    db: AsyncSession = Depends(get_db),
    user: User = Depends(get_current_user),
):
    """Check out. Requires an open check-in for today."""
    person = await resolve_person(user, person_id, db)
    today = today_local()

    result = await db.execute(
        select(AttendanceRecord).where(
            AttendanceRecord.person_id == person.id,
            AttendanceRecord.date == today,
        )
    )
    record = result.scalar_one_or_none()

    if record is None or record.check_in is None:
        raise HTTPException(status_code=409, detail="You have not checked in today")
    if record.check_out is not None:
        raise HTTPException(
            status_code=409,
            detail=f"Already checked out at {record.check_out.isoformat()}",
        )

    record.check_out = datetime.now(get_app_tz())
    await db.commit()
    await db.refresh(record, attribute_names=["person"])
    return record_to_out(record)


@router.post("/manual", response_model=AttendanceOut, status_code=status.HTTP_201_CREATED)
async def create_manual_record(
    data: AttendanceCreate,
    db: AsyncSession = Depends(get_db),
    _: User = Depends(require_admin),
):
    """Admin-only: manually create a record (e.g. mark a person absent on a date)."""
    person = await db.get(Person, data.person_id)
    if person is None:
        raise HTTPException(status_code=404, detail="Person not found")

    result = await db.execute(
        select(AttendanceRecord).where(
            AttendanceRecord.person_id == data.person_id,
            AttendanceRecord.date == data.date,
        )
    )
    if result.scalar_one_or_none() is not None:
        raise HTTPException(
            status_code=409,
            detail=f"A record already exists for person {data.person_id} on {data.date}",
        )

    record = AttendanceRecord(**data.model_dump())
    db.add(record)
    await db.commit()
    await db.refresh(record, attribute_names=["person"])
    return record_to_out(record)


@router.patch("/{record_id}", response_model=AttendanceOut)
async def update_record(
    record_id: int,
    data: AttendanceUpdate,
    db: AsyncSession = Depends(get_db),
    _: User = Depends(require_admin),
):
    """Admin-only: edit a record's times, status or note."""
    record = await get_record_or_404(record_id, db)
    for field, value in data.model_dump(exclude_unset=True).items():
        setattr(record, field, value)
    await db.commit()
    await db.refresh(record, attribute_names=["person"])
    return record_to_out(record)


@router.delete("/{record_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_record(
    record_id: int,
    db: AsyncSession = Depends(get_db),
    _: User = Depends(require_admin),
):
    record = await get_record_or_404(record_id, db)
    await db.delete(record)
    await db.commit()


@router.get("/stats", response_model=DashboardStats)
async def get_dashboard_stats(
    db: AsyncSession = Depends(get_db),
    user: User = Depends(get_current_user),
):
    """Get dashboard stats: streak, late count, monthly summary."""
    if user.person_id is None:
        return DashboardStats()

    today = today_local()
    first_of_month = today.replace(day=1)

    # Get all records for this person in current month
    result = await db.execute(
        select(AttendanceRecord).where(
            AttendanceRecord.person_id == user.person_id,
            AttendanceRecord.date >= first_of_month,
            AttendanceRecord.date <= today,
        ).order_by(AttendanceRecord.date.desc())
    )
    month_records = list(result.scalars().all())

    # Calculate streak (consecutive present days ending today or yesterday)
    streak = 0
    check_date = today
    # Get all records sorted by date desc for streak calculation
    all_result = await db.execute(
        select(AttendanceRecord).where(
            AttendanceRecord.person_id == user.person_id,
            AttendanceRecord.date <= today,
        ).order_by(AttendanceRecord.date.desc()).limit(60)
    )
    all_records = list(all_result.scalars().all())
    records_by_date = {r.date: r for r in all_records}

    # Check if today has a present record
    if today in records_by_date and records_by_date[today].status == "present":
        streak = 1
        check_date = today - timedelta(days=1)
    elif today in records_by_date and records_by_date[today].status == "half_day":
        streak = 1
        check_date = today - timedelta(days=1)
    else:
        check_date = today - timedelta(days=1)

    # Count consecutive days backwards
    while check_date in records_by_date:
        rec = records_by_date[check_date]
        if rec.status in ("present", "half_day"):
            streak += 1
            check_date -= timedelta(days=1)
        else:
            break

    # Calculate late count (check-in after 10:00 AM)
    app_tz = get_app_tz()
    late_count = 0
    for rec in month_records:
        if rec.check_in and rec.status == "present":
            local_time = rec.check_in.astimezone(app_tz)
            if local_time.hour > 10 or (local_time.hour == 10 and local_time.minute > 0):
                late_count += 1

    # Monthly stats
    total_present = sum(1 for r in month_records if r.status == "present")
    total_absent = sum(1 for r in month_records if r.status == "absent")
    total_half = sum(1 for r in month_records if r.status == "half_day")

    # Total hours
    total_minutes = 0
    for r in month_records:
        if r.check_in and r.check_out and r.check_out > r.check_in:
            total_minutes += int((r.check_out - r.check_in).total_seconds() // 60)
    total_hours = round(total_minutes / 60, 1)

    # Attendance rate
    days_so_far = (today - first_of_month).days + 1
    rate = round((total_present + total_half) / days_so_far, 2) if days_so_far > 0 else 0.0

    return DashboardStats(
        streak=streak,
        late_count=late_count,
        total_present_month=total_present,
        total_absent_month=total_absent,
        total_hours_month=total_hours,
        attendance_rate_month=rate,
    )


@router.get("/team", response_model=list[TeamMember])
async def team_dashboard(
    group: str | None = None,
    db: AsyncSession = Depends(get_db),
    _: User = Depends(require_admin),
):
    """Admin: see who's checked in today (live team view)."""
    today = today_local()

    # Get all active people
    person_q = select(Person).where(Person.is_active.is_(True))
    if group:
        person_q = person_q.where(Person.group_name == group)
    people = list((await db.execute(person_q.order_by(Person.full_name))).scalars().all())

    # Get today's records
    rec_q = select(AttendanceRecord).options(
        joinedload(AttendanceRecord.person)
    ).where(AttendanceRecord.date == today)
    records = list((await db.execute(rec_q)).scalars().all())
    rec_by_person = {r.person_id: r for r in records}

    result = []
    for p in people:
        rec = rec_by_person.get(p.id)
        is_on_clock = rec and rec.check_in and not rec.check_out
        result.append(TeamMember(
            person_id=p.id,
            person_name=p.full_name,
            group_name=p.group_name,
            status=rec.status if rec else "absent",
            check_in=rec.check_in if rec else None,
            check_out=rec.check_out if rec else None,
            is_on_clock=bool(is_on_clock),
        ))

    return result
