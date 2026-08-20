"""Admin-only endpoints for sending notifications."""
from datetime import date, datetime

from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel, Field
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from ..database import get_db
from ..deps import get_app_tz, require_admin
from ..models import AttendanceRecord, Person, Shift, ShiftAssignment, User
from ..notifications import (
    send_check_in_reminder,
    send_late_check_in_alert,
    send_no_show_alert,
)

router = APIRouter(prefix="/api/notifications", tags=["notifications"])


class SendReminderRequest(BaseModel):
    person_id: int | None = None  # None = send to all active people


class SendAlertRequest(BaseModel):
    person_id: int
    alert_type: str = Field(pattern="^(late|no_show)$")


@router.post("/send-reminder")
async def send_reminder(
    data: SendReminderRequest,
    db: AsyncSession = Depends(get_db),
    _: User = Depends(require_admin),
):
    """Send check-in reminders to people."""
    if data.person_id:
        person = await db.get(Person, data.person_id)
        if person is None:
            raise HTTPException(status_code=404, detail="Person not found")
        people = [person]
    else:
        people = list(
            (await db.execute(select(Person).where(Person.is_active.is_(True)))).scalars().all()
        )

    sent = 0
    for person in people:
        if person.email:
            if send_check_in_reminder(person.email, person.full_name):
                sent += 1

    return {"sent": sent, "total": len(people)}


@router.post("/send-alert")
async def send_alert(
    data: SendAlertRequest,
    db: AsyncSession = Depends(get_db),
    admin: User = Depends(require_admin),
):
    """Send a late or no-show alert to admin about a specific person."""
    person = await db.get(Person, data.person_id)
    if person is None:
        raise HTTPException(status_code=404, detail="Person not found")

    # Get admin's email
    admin_email = admin.email
    if not admin_email:
        raise HTTPException(status_code=400, detail="Admin email not configured")

    result = False
    if data.alert_type == "no_show":
        result = send_no_show_alert(admin_email, admin.full_name, person.full_name)
    elif data.alert_type == "late":
        # Get today's record
        today = datetime.now(get_app_tz()).date()
        record = (
            await db.execute(
                select(AttendanceRecord).where(
                    AttendanceRecord.person_id == person.id,
                    AttendanceRecord.date == today,
                )
            )
        ).scalar_one_or_none()

        if record is None or record.check_in is None:
            raise HTTPException(status_code=400, detail="No check-in record found for today")

        check_in_time = record.check_in.astimezone(get_app_tz()).strftime("%H:%M")

        # Try to find shift assignment
        shift_start = "09:00"  # default
        assignment = (
            await db.execute(
                select(ShiftAssignment).where(
                    ShiftAssignment.person_id == person.id,
                    ShiftAssignment.start_date <= today,
                    ShiftAssignment.is_active.is_(True),
                )
            )
        ).scalar_one_or_none()

        if assignment:
            shift = await db.get(Shift, assignment.shift_id)
            if shift:
                shift_start = shift.start_time.strftime("%H:%M")

        result = send_late_check_in_alert(
            admin_email, admin.full_name, person.full_name, check_in_time, shift_start
        )

    return {"sent": result}


@router.get("/settings")
async def get_notification_settings(
    _: User = Depends(require_admin),
):
    """Get current notification settings."""
    from ..config import settings
    return {
        "email_enabled": settings.email_enabled,
        "smtp_host": settings.smtp_host,
        "smtp_port": settings.smtp_port,
        "smtp_user": settings.smtp_user,
        "smtp_from_email": settings.smtp_from_email,
        "late_check_in_minutes": settings.late_check_in_minutes,
        "send_daily_reminder": settings.send_daily_reminder,
        "send_late_alert": settings.send_late_alert,
    }
