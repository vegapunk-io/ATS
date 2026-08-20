"""Activity audit logging helper."""
import json
import logging
from datetime import datetime

from sqlalchemy.ext.asyncio import AsyncSession

from .models import ActivityLog

logger = logging.getLogger(__name__)


async def log_activity(
    db: AsyncSession,
    user_id: int | None,
    username: str | None,
    action: str,
    entity: str,
    entity_id: int | None = None,
    details: dict | str | None = None,
    ip_address: str | None = None,
):
    """Log an activity to the audit trail."""
    details_str = None
    if details:
        if isinstance(details, dict):
            details_str = json.dumps(details, default=str)
        else:
            details_str = str(details)

    log = ActivityLog(
        user_id=user_id,
        username=username,
        action=action,
        entity=entity,
        entity_id=entity_id,
        details=details_str,
        ip_address=ip_address,
    )
    db.add(log)
    await db.flush()
