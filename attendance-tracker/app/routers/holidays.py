"""Admin-only endpoints for managing holidays."""
from datetime import date

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession

from ..database import get_db
from ..deps import require_admin
from ..models import AttendanceRecord, Holiday, Person
from ..schemas import HolidayCreate, HolidayOut, HolidayUpdate

router = APIRouter(prefix="/api/holidays", tags=["holidays"])


async def get_holiday_or_404(holiday_id: int, db: AsyncSession) -> Holiday:
    holiday = await db.get(Holiday, holiday_id)
    if holiday is None:
        raise HTTPException(status_code=404, detail="Holiday not found")
    return holiday


async def auto_mark_holiday(holiday_date: date, db: AsyncSession):
    """Create 'holiday' attendance records for all active people on the given date."""
    people = list(
        (await db.execute(select(Person).where(Person.is_active.is_(True)))).scalars().all()
    )
    for person in people:
        exists = (
            await db.execute(
                select(AttendanceRecord).where(
                    AttendanceRecord.person_id == person.id,
                    AttendanceRecord.date == holiday_date,
                )
            )
        ).scalar_one_or_none()
        if exists is None:
            db.add(
                AttendanceRecord(
                    person_id=person.id,
                    date=holiday_date,
                    status="holiday",
                )
            )
        elif exists.status != "holiday":
            exists.status = "holiday"
            exists.check_in = None
            exists.check_out = None
    await db.flush()


@router.get("", response_model=list[HolidayOut])
async def list_holidays(
    db: AsyncSession = Depends(get_db),
    _: Holiday = Depends(require_admin),
):
    result = await db.execute(select(Holiday).order_by(Holiday.date))
    return list(result.scalars().all())


@router.post("", response_model=HolidayOut, status_code=status.HTTP_201_CREATED)
async def create_holiday(
    data: HolidayCreate,
    db: AsyncSession = Depends(get_db),
    _: Holiday = Depends(require_admin),
):
    holiday = Holiday(**data.model_dump())
    db.add(holiday)
    try:
        await db.commit()
    except IntegrityError:
        await db.rollback()
        raise HTTPException(status_code=409, detail="A holiday already exists for this date")
    await db.refresh(holiday)

    # Auto-mark attendance as holiday
    await auto_mark_holiday(holiday.date, db)
    await db.commit()

    return holiday


@router.patch("/{holiday_id}", response_model=HolidayOut)
async def update_holiday(
    holiday_id: int,
    data: HolidayUpdate,
    db: AsyncSession = Depends(get_db),
    _: Holiday = Depends(require_admin),
):
    holiday = await get_holiday_or_404(holiday_id, db)
    for field, value in data.model_dump(exclude_unset=True).items():
        setattr(holiday, field, value)
    try:
        await db.commit()
    except IntegrityError:
        await db.rollback()
        raise HTTPException(status_code=409, detail="A holiday already exists for this date")
    await db.refresh(holiday)
    return holiday


@router.delete("/{holiday_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_holiday(
    holiday_id: int,
    db: AsyncSession = Depends(get_db),
    _: Holiday = Depends(require_admin),
):
    holiday = await get_holiday_or_404(holiday_id, db)
    await db.delete(holiday)
    await db.commit()
