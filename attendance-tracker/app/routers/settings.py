"""App settings endpoints."""
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from ..database import get_db
from ..deps import get_current_user, require_admin
from ..models import AppSettings, User
from ..schemas import SettingOut, SettingUpdate

router = APIRouter(prefix="/api/settings", tags=["settings"])

DEFAULT_SETTINGS = [
    ("app_name", "Attendance Tracker", "Application name"),
    ("timezone", "Asia/Kolkata", "Application timezone"),
    ("late_threshold_minutes", "15", "Minutes after shift start to mark late"),
    ("overtime_threshold_hours", "8", "Daily hours before overtime"),
    ("salary_currency", "INR", "Currency for salary calculations"),
    ("working_hours_per_day", "8", "Standard working hours per day"),
]


async def ensure_defaults(db: AsyncSession):
    for key, value, desc in DEFAULT_SETTINGS:
        result = await db.execute(select(AppSettings).where(AppSettings.key == key))
        if not result.scalar_one_or_none():
            db.add(AppSettings(key=key, value=value, description=desc))
    await db.commit()


@router.get("", response_model=list[SettingOut])
async def list_settings(
    db: AsyncSession = Depends(get_db),
    _: User = Depends(require_admin),
):
    await ensure_defaults(db)
    result = await db.execute(select(AppSettings).order_by(AppSettings.key))
    return [SettingOut.model_validate(s) for s in result.scalars().all()]


@router.get("/{key}", response_model=SettingOut)
async def get_setting(
    key: str,
    db: AsyncSession = Depends(get_db),
    _: User = Depends(get_current_user),
):
    result = await db.execute(select(AppSettings).where(AppSettings.key == key))
    setting = result.scalar_one_or_none()
    if setting is None:
        raise HTTPException(status_code=404, detail="Setting not found")
    return SettingOut.model_validate(setting)


@router.patch("/{key}", response_model=SettingOut)
async def update_setting(
    key: str,
    data: SettingUpdate,
    db: AsyncSession = Depends(get_db),
    _: User = Depends(require_admin),
):
    result = await db.execute(select(AppSettings).where(AppSettings.key == key))
    setting = result.scalar_one_or_none()
    if setting is None:
        setting = AppSettings(key=key, value=data.value)
        db.add(setting)
    else:
        setting.value = data.value
    await db.commit()
    await db.refresh(setting)
    return SettingOut.model_validate(setting)
