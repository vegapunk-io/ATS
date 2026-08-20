"""Salary/Payroll endpoints."""
from calendar import monthrange

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import joinedload

from ..database import get_db
from ..deps import get_current_user, require_admin
from ..models import AttendanceRecord, Person, SalaryRecord, User
from ..schemas import SalaryGenerate, SalaryOut

router = APIRouter(prefix="/api/salary", tags=["salary"])


async def salary_to_out(sal: SalaryRecord, db: AsyncSession) -> SalaryOut:
    person = await db.get(Person, sal.person_id)
    return SalaryOut(
        id=sal.id,
        person_id=sal.person_id,
        person_name=person.full_name if person else None,
        month=sal.month,
        year=sal.year,
        base_salary=sal.base_salary,
        working_days=sal.working_days,
        present_days=sal.present_days,
        absent_days=sal.absent_days,
        half_days=sal.half_days,
        overtime_hours=sal.overtime_hours,
        deduction=sal.deduction,
        bonus=sal.bonus,
        net_salary=sal.net_salary,
        status=sal.status,
        created_at=sal.created_at,
    )


@router.get("", response_model=list[SalaryOut])
async def list_salary(
    month: int | None = None,
    year: int | None = None,
    person_id: int | None = None,
    db: AsyncSession = Depends(get_db),
    user: User = Depends(get_current_user),
):
    query = select(SalaryRecord).order_by(SalaryRecord.year.desc(), SalaryRecord.month.desc())

    if user.role != "admin" and user.person_id:
        query = query.where(SalaryRecord.person_id == user.person_id)
    elif person_id:
        query = query.where(SalaryRecord.person_id == person_id)

    if month:
        query = query.where(SalaryRecord.month == month)
    if year:
        query = query.where(SalaryRecord.year == year)

    result = await db.execute(query)
    records = result.scalars().all()
    return [await salary_to_out(s, db) for s in records]


@router.post("/generate", response_model=list[SalaryOut], status_code=status.HTTP_201_CREATED)
async def generate_salary(
    data: SalaryGenerate,
    db: AsyncSession = Depends(get_db),
    _: User = Depends(require_admin),
):
    """Auto-generate salary for all active people based on attendance."""
    people = list((await db.execute(
        select(Person).where(Person.is_active.is_(True))
    )).scalars().all())

    _, days_in_month = monthrange(data.year, data.month)
    working_days = sum(1 for d in range(1, days_in_month + 1)
                       if __import__('datetime').date(data.year, data.month, d).weekday() < 5)

    results = []
    for person in people:
        existing = await db.execute(
            select(SalaryRecord).where(
                SalaryRecord.person_id == person.id,
                SalaryRecord.month == data.month,
                SalaryRecord.year == data.year,
            )
        )
        if existing.scalar_one_or_none():
            continue

        recs = list((await db.execute(
            select(AttendanceRecord).where(
                AttendanceRecord.person_id == person.id,
                AttendanceRecord.date >= f"{data.year}-{data.month:02d}-01",
                AttendanceRecord.date <= f"{data.year}-{data.month:02d}-{days_in_month}",
            )
        )).scalars().all())

        present = sum(1 for r in recs if r.status == "present")
        absent = sum(1 for r in recs if r.status == "absent")
        half = sum(1 for r in recs if r.status == "half_day")

        overtime = 0.0
        for r in recs:
            if r.check_in and r.check_out:
                mins = (r.check_out - r.check_in).total_seconds() / 60
                if mins > 480:
                    overtime += (mins - 480) / 60

        daily_rate = data.base_salary / working_days if working_days else 0
        earned = (present * daily_rate) + (half * daily_rate * 0.5)
        deduction = (absent * daily_rate) + (half * daily_rate * 0.5)
        net = earned - deduction + (overtime * daily_rate / 8)

        sal = SalaryRecord(
            person_id=person.id,
            month=data.month,
            year=data.year,
            base_salary=data.base_salary,
            working_days=working_days,
            present_days=present,
            absent_days=absent,
            half_days=half,
            overtime_hours=round(overtime, 1),
            deduction=round(deduction, 2),
            bonus=0.0,
            net_salary=round(max(net, 0), 2),
            status="draft",
        )
        db.add(sal)
        results.append(sal)

    await db.commit()
    for s in results:
        await db.refresh(s)
    return [await salary_to_out(s, db) for s in results]


@router.patch("/{sal_id}", response_model=SalaryOut)
async def update_salary(
    sal_id: int,
    bonus: float = 0,
    deduction: float = 0,
    status_val: str = Query(default=None, alias="status"),
    db: AsyncSession = Depends(get_db),
    _: User = Depends(require_admin),
):
    sal = await db.get(SalaryRecord, sal_id)
    if sal is None:
        raise HTTPException(status_code=404, detail="Salary record not found")

    if bonus:
        sal.bonus = bonus
    if deduction:
        sal.deduction = deduction
    if status_val:
        sal.status = status_val

    daily_rate = sal.base_salary / sal.working_days if sal.working_days else 0
    earned = (sal.present_days * daily_rate) + (sal.half_days * daily_rate * 0.5)
    sal.net_salary = round(max(earned - sal.deduction + sal.bonus + (sal.overtime_hours * daily_rate / 8), 0), 2)

    await db.commit()
    await db.refresh(sal)
    return await salary_to_out(sal, db)
