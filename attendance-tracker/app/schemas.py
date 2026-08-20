"""Pydantic schemas for request/response validation."""
from datetime import date, datetime, time
from typing import Optional

from pydantic import BaseModel, ConfigDict, EmailStr, Field


# ---------- Auth ----------
class Token(BaseModel):
    access_token: str
    token_type: str = "bearer"


class UserOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    username: str
    email: str | None = None
    full_name: str
    role: str
    is_active: bool
    person_id: int | None = None
    created_at: datetime | None = None


# ---------- Users (admin) ----------
class UserCreate(BaseModel):
    username: str = Field(min_length=3, max_length=64)
    email: EmailStr | None = None
    full_name: str = Field(min_length=1, max_length=255)
    password: str = Field(min_length=6, max_length=128)
    role: str = Field(default="user", pattern="^(admin|user)$")
    person_id: int | None = None


class UserUpdate(BaseModel):
    email: EmailStr | None = None
    full_name: str | None = Field(default=None, min_length=1, max_length=255)
    password: str | None = Field(default=None, min_length=6, max_length=128)
    role: str | None = Field(default=None, pattern="^(admin|user)$")
    is_active: bool | None = None
    person_id: int | None = None


# ---------- People ----------
class PersonBase(BaseModel):
    full_name: str = Field(min_length=1, max_length=255)
    email: EmailStr | None = None
    group_name: str | None = Field(default=None, max_length=128)
    is_active: bool = True


class PersonCreate(PersonBase):
    pass


class PersonUpdate(BaseModel):
    full_name: str | None = Field(default=None, min_length=1, max_length=255)
    email: EmailStr | None = None
    group_name: str | None = Field(default=None, max_length=128)
    is_active: bool | None = None


class PersonOut(PersonBase):
    model_config = ConfigDict(from_attributes=True)

    id: int
    created_at: datetime


# ---------- Attendance ----------
class AttendanceCreate(BaseModel):
    """Admin-only: manually create/override a record (e.g. mark absent)."""

    person_id: int
    date: date
    check_in: datetime | None = None
    check_out: datetime | None = None
    status: str = Field(default="present", pattern="^(present|absent|half_day|holiday)$")
    note: str | None = None


class AttendanceUpdate(BaseModel):
    check_in: datetime | None = None
    check_out: datetime | None = None
    status: str | None = Field(default=None, pattern="^(present|absent|half_day|holiday)$")
    note: str | None = None


class AttendanceOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    person_id: int
    person_name: str | None = None
    group_name: str | None = None
    date: date
    check_in: datetime | None = None
    check_out: datetime | None = None
    status: str
    note: str | None = None
    duration_minutes: int | None = None


# ---------- Reports ----------
class PersonSummary(BaseModel):
    person_id: int
    person_name: str
    group_name: str | None = None
    total_days: int
    present_days: int
    absent_days: int
    half_days: int
    holiday_days: int
    unrecorded_days: int
    total_work_minutes: int
    avg_work_minutes: int | None = None
    avg_check_in: str | None = None
    avg_check_out: str | None = None
    attendance_rate: float = 0.0


class SummaryResponse(BaseModel):
    date_from: date
    date_to: date
    total_days: int
    total_people: int
    people: list[PersonSummary]


# ---------- Holidays ----------
class HolidayCreate(BaseModel):
    name: str = Field(min_length=1, max_length=255)
    date: date
    description: Optional[str] = None


class HolidayUpdate(BaseModel):
    name: Optional[str] = Field(default=None, min_length=1, max_length=255)
    date: Optional[date] = None
    description: Optional[str] = None


class HolidayOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    name: str
    date: date
    description: Optional[str] = None
    created_at: datetime


# ---------- Shifts ----------
class ShiftCreate(BaseModel):
    name: str = Field(min_length=1, max_length=128)
    start_time: time
    end_time: time


class ShiftUpdate(BaseModel):
    name: Optional[str] = Field(default=None, min_length=1, max_length=128)
    start_time: Optional[time] = None
    end_time: Optional[time] = None
    is_active: Optional[bool] = None


class ShiftOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    name: str
    start_time: time
    end_time: time
    is_active: bool
    created_at: datetime


class ShiftAssignmentCreate(BaseModel):
    person_id: int
    shift_id: int
    start_date: date
    end_date: Optional[date] = None


class ShiftAssignmentUpdate(BaseModel):
    shift_id: Optional[int] = None
    start_date: Optional[date] = None
    end_date: Optional[date] = None
    is_active: Optional[bool] = None


class ShiftAssignmentOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    person_id: int
    person_name: Optional[str] = None
    shift_id: int
    shift_name: Optional[str] = None
    start_date: date
    end_date: Optional[date] = None
    is_active: bool


# ---------- Dashboard Stats ----------
class DashboardStats(BaseModel):
    streak: int = 0
    late_count: int = 0
    total_present_month: int = 0
    total_absent_month: int = 0
    total_hours_month: float = 0.0
    attendance_rate_month: float = 0.0


# ---------- Leave ----------
class LeaveCreate(BaseModel):
    leave_type: str = Field(default="sick", pattern="^(sick|casual|annual|unpaid|other)$")
    start_date: date
    end_date: date
    reason: str | None = None


class LeaveUpdate(BaseModel):
    status: str = Field(pattern="^(pending|approved|rejected)$")
    admin_note: str | None = None


class LeaveOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    person_id: int
    person_name: str | None = None
    leave_type: str
    start_date: date
    end_date: date
    reason: str | None = None
    status: str
    approved_by: int | None = None
    admin_note: str | None = None
    created_at: datetime


# ---------- Break ----------
class BreakCreate(BaseModel):
    break_type: str = Field(default="lunch", pattern="^(lunch|tea|coffee|other)$")


class BreakOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    person_id: int
    person_name: str | None = None
    date: date
    break_start: datetime
    break_end: datetime | None = None
    break_type: str
    duration_minutes: int | None = None


# ---------- Team Dashboard ----------
class TeamMember(BaseModel):
    person_id: int
    person_name: str
    group_name: str | None = None
    status: str  # present | absent | half_day | holiday
    check_in: datetime | None = None
    check_out: datetime | None = None
    is_on_clock: bool = False


# ---------- Department ----------
class DepartmentCreate(BaseModel):
    name: str = Field(min_length=1, max_length=128)
    description: str | None = None
    head_id: int | None = None


class DepartmentUpdate(BaseModel):
    name: str | None = Field(default=None, min_length=1, max_length=128)
    description: str | None = None
    head_id: int | None = None
    is_active: bool | None = None


class DepartmentOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    name: str
    description: str | None = None
    head_id: int | None = None
    head_name: str | None = None
    is_active: bool
    member_count: int = 0
    created_at: datetime


# ---------- Announcement ----------
class AnnouncementCreate(BaseModel):
    title: str = Field(min_length=1, max_length=255)
    content: str = Field(min_length=1)
    priority: str = Field(default="normal", pattern="^(low|normal|high|urgent)$")
    expires_at: datetime | None = None


class AnnouncementOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    title: str
    content: str
    priority: str
    is_active: bool
    created_by: int | None = None
    created_by_name: str | None = None
    expires_at: datetime | None = None
    created_at: datetime


# ---------- Salary ----------
class SalaryGenerate(BaseModel):
    month: int = Field(ge=1, le=12)
    year: int = Field(ge=2020, le=2030)
    base_salary: float = Field(default=50000.0, ge=0)


class SalaryOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    person_id: int
    person_name: str | None = None
    month: int
    year: int
    base_salary: float
    working_days: int
    present_days: int
    absent_days: int
    half_days: int
    overtime_hours: float
    deduction: float
    bonus: float
    net_salary: float
    status: str
    created_at: datetime


# ---------- Settings ----------
class SettingUpdate(BaseModel):
    value: str


class SettingOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    key: str
    value: str | None = None
    description: str | None = None
    updated_at: datetime


# ---------- Overtime ----------
class OvertimeCreate(BaseModel):
    date: date
    hours: float = Field(ge=0.5, le=24)
    reason: str | None = None


class OvertimeUpdate(BaseModel):
    status: str = Field(pattern="^(approved|rejected)$")
    admin_note: str | None = None


class OvertimeOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    person_id: int
    person_name: str | None = None
    date: date
    hours: float
    reason: str | None = None
    status: str
    approved_by: int | None = None
    admin_note: str | None = None
    created_at: datetime


# ---------- Shift Swap ----------
class ShiftSwapCreate(BaseModel):
    target_id: int | None = None
    requester_date: date
    target_date: date | None = None
    reason: str | None = None


class ShiftSwapUpdate(BaseModel):
    status: str = Field(pattern="^(accepted|rejected|cancelled)$")
    admin_note: str | None = None


class ShiftSwapOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    requester_id: int
    requester_name: str | None = None
    target_id: int | None = None
    target_name: str | None = None
    requester_date: date
    target_date: date | None = None
    reason: str | None = None
    status: str
    approved_by: int | None = None
    admin_note: str | None = None
    created_at: datetime


# ---------- Tasks ----------
class TaskCreate(BaseModel):
    title: str = Field(min_length=1, max_length=255)
    description: str | None = None
    assigned_to: int | None = None
    priority: str = Field(default="normal", pattern="^(low|normal|high|urgent)$")
    due_date: date | None = None


class TaskUpdate(BaseModel):
    title: str | None = None
    description: str | None = None
    assigned_to: int | None = None
    priority: str | None = None
    status: str | None = Field(default=None, pattern="^(todo|in_progress|done)$")
    due_date: date | None = None


class TaskOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    title: str
    description: str | None = None
    assigned_to: int | None = None
    assignee_name: str | None = None
    assigned_by: int | None = None
    creator_name: str | None = None
    priority: str
    status: str
    due_date: date | None = None
    completed_at: datetime | None = None
    created_at: datetime


# ---------- Chat ----------
class ChatMessageCreate(BaseModel):
    content: str = Field(min_length=1, max_length=5000)
    channel: str = Field(default="general", max_length=64)


class ChatMessageOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    sender_id: int
    sender_name: str | None = None
    channel: str
    content: str
    created_at: datetime


# ---------- Meetings ----------
class MeetingCreate(BaseModel):
    title: str = Field(min_length=1, max_length=255)
    description: str | None = None
    room: str | None = None
    scheduled_at: datetime
    duration_minutes: int = Field(default=30, ge=5, le=480)
    attendee_ids: list[int] = []


class MeetingUpdate(BaseModel):
    title: str | None = None
    description: str | None = None
    room: str | None = None
    scheduled_at: datetime | None = None
    duration_minutes: int | None = None
    attendee_ids: list[int] | None = None


class MeetingOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    title: str
    description: str | None = None
    room: str | None = None
    scheduled_at: datetime
    duration_minutes: int
    created_by: int | None = None
    creator_name: str | None = None
    attendees: list[dict] = []
    created_at: datetime


# ---------- Activity Log ----------
class ActivityLogOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    user_id: int | None = None
    username: str | None = None
    action: str
    entity: str
    entity_id: int | None = None
    details: str | None = None
    ip_address: str | None = None
    created_at: datetime


# ---------- Profile ----------
class ProfileOut(BaseModel):
    user: UserOut
    person: PersonOut | None = None
    stats: DashboardStats | None = None
