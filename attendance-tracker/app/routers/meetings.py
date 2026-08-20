"""Meeting scheduler endpoints."""
from datetime import datetime

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import joinedload

from ..database import get_db
from ..deps import get_current_user, require_admin
from ..models import Meeting, MeetingAttendee, Person, User
from ..schemas import MeetingCreate, MeetingOut, MeetingUpdate

router = APIRouter(prefix="/api/meetings", tags=["meetings"])


def meeting_to_out(m: Meeting) -> MeetingOut:
    attendees = []
    for a in (m.attendees or []):
        attendees.append({
            "person_id": a.person_id,
            "name": a.person.full_name if a.person else None,
            "status": a.status,
        })
    return MeetingOut(
        id=m.id,
        title=m.title,
        description=m.description,
        room=m.room,
        scheduled_at=m.scheduled_at,
        duration_minutes=m.duration_minutes,
        created_by=m.created_by,
        attendees=attendees,
        created_at=m.created_at,
    )


@router.get("", response_model=list[MeetingOut])
async def list_meetings(
    date_from: str | None = None,
    date_to: str | None = None,
    db: AsyncSession = Depends(get_db),
    user: User = Depends(get_current_user),
):
    query = select(Meeting).options(
        joinedload(Meeting.attendees).joinedload(MeetingAttendee.person)
    ).order_by(Meeting.scheduled_at)

    if user.role != "admin" and user.person_id:
        my_ids_q = select(MeetingAttendee.meeting_id).where(MeetingAttendee.person_id == user.person_id)
        my_meetings = select(Meeting).options(
            joinedload(Meeting.attendees).joinedload(MeetingAttendee.person)
        ).where(Meeting.id.in_(my_ids_q))
        creator_meetings = select(Meeting).options(
            joinedload(Meeting.attendees).joinedload(MeetingAttendee.person)
        ).where(Meeting.created_by == user.id)
        from sqlalchemy import union_all, select as sa_select
        combined = my_meetings.union_all(creator_meetings)
        query = combined

    if date_from:
        query = query.where(Meeting.scheduled_at >= date_from)
    if date_to:
        query = query.where(Meeting.scheduled_at <= date_to + "T23:59:59")

    result = await db.execute(query)
    meetings = result.scalars().unique().all()
    return [meeting_to_out(m) for m in meetings]


@router.post("", response_model=MeetingOut, status_code=status.HTTP_201_CREATED)
async def create_meeting(
    data: MeetingCreate,
    db: AsyncSession = Depends(get_db),
    user: User = Depends(get_current_user),
):
    meeting = Meeting(
        title=data.title,
        description=data.description,
        room=data.room,
        scheduled_at=data.scheduled_at,
        duration_minutes=data.duration_minutes,
        created_by=user.id,
    )
    db.add(meeting)
    await db.flush()

    for pid in data.attendee_ids:
        att = MeetingAttendee(meeting_id=meeting.id, person_id=pid, status="pending")
        db.add(att)

    await db.commit()
    await db.refresh(meeting, attribute_names=["attendees"])
    return meeting_to_out(meeting)


@router.patch("/{meeting_id}", response_model=MeetingOut)
async def update_meeting(
    meeting_id: int,
    data: MeetingUpdate,
    db: AsyncSession = Depends(get_db),
    user: User = Depends(get_current_user),
):
    meeting = await db.get(Meeting, meeting_id)
    if meeting is None:
        raise HTTPException(status_code=404, detail="Meeting not found")
    if user.role != "admin" and meeting.created_by != user.id:
        raise HTTPException(status_code=403, detail="Not allowed")

    for field in ["title", "description", "room", "scheduled_at", "duration_minutes"]:
        val = getattr(data, field)
        if val is not None:
            setattr(meeting, field, val)

    if data.attendee_ids is not None:
        existing = list(await db.execute(
            select(MeetingAttendee).where(MeetingAttendee.meeting_id == meeting_id)
        )).scalars().all()
        for e in existing:
            await db.delete(e)
        for pid in data.attendee_ids:
            db.add(MeetingAttendee(meeting_id=meeting_id, person_id=pid, status="pending"))

    await db.commit()
    await db.refresh(meeting, attribute_names=["attendees"])
    return meeting_to_out(meeting)


@router.delete("/{meeting_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_meeting(
    meeting_id: int,
    db: AsyncSession = Depends(get_db),
    user: User = Depends(get_current_user),
):
    meeting = await db.get(Meeting, meeting_id)
    if meeting is None:
        raise HTTPException(status_code=404, detail="Meeting not found")
    if user.role != "admin" and meeting.created_by != user.id:
        raise HTTPException(status_code=403, detail="Not allowed")
    await db.delete(meeting)
    await db.commit()


@router.patch("/{meeting_id}/attendees/{person_id}")
async def update_attendee(
    meeting_id: int,
    person_id: int,
    status_val: str = Query(alias="status"),
    db: AsyncSession = Depends(get_db),
    user: User = Depends(get_current_user),
):
    if user.person_id != person_id and user.role != "admin":
        raise HTTPException(status_code=403, detail="Not allowed")
    result = await db.execute(
        select(MeetingAttendee).where(
            MeetingAttendee.meeting_id == meeting_id,
            MeetingAttendee.person_id == person_id,
        )
    )
    att = result.scalar_one_or_none()
    if att is None:
        raise HTTPException(status_code=404, detail="Attendee not found")
    att.status = status_val
    await db.commit()
    return {"detail": "Updated"}
