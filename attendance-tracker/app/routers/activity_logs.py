"""Activity audit log endpoints."""
from fastapi import APIRouter, Depends, Query
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from ..database import get_db
from ..deps import get_current_user, require_admin
from ..models import ActivityLog, User
from ..schemas import ActivityLogOut

router = APIRouter(prefix="/api/activity-logs", tags=["activity-logs"])


@router.get("", response_model=list[ActivityLogOut])
async def list_logs(
    entity: str | None = None,
    action: str | None = None,
    user_id: int | None = None,
    limit: int = Query(default=100, le=500),
    db: AsyncSession = Depends(get_db),
    _: User = Depends(require_admin),
):
    query = select(ActivityLog).order_by(ActivityLog.created_at.desc()).limit(limit)
    if entity:
        query = query.where(ActivityLog.entity == entity)
    if action:
        query = query.where(ActivityLog.action == action)
    if user_id:
        query = query.where(ActivityLog.user_id == user_id)
    result = await db.execute(query)
    return [ActivityLogOut.model_validate(l) for l in result.scalars().all()]
