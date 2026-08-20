"""Announcements endpoints."""
from datetime import datetime

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from ..database import get_db
from ..deps import get_current_user, require_admin
from ..models import Announcement, User
from ..schemas import AnnouncementCreate, AnnouncementOut

router = APIRouter(prefix="/api/announcements", tags=["announcements"])


def ann_to_out(ann: Announcement, creator_name: str | None = None) -> AnnouncementOut:
    return AnnouncementOut(
        id=ann.id,
        title=ann.title,
        content=ann.content,
        priority=ann.priority,
        is_active=ann.is_active,
        created_by=ann.created_by,
        created_by_name=creator_name,
        expires_at=ann.expires_at,
        created_at=ann.created_at,
    )


@router.get("", response_model=list[AnnouncementOut])
async def list_announcements(
    db: AsyncSession = Depends(get_db),
    _: User = Depends(get_current_user),
):
    result = await db.execute(
        select(Announcement).where(Announcement.is_active.is_(True)).order_by(Announcement.created_at.desc())
    )
    announcements = result.scalars().all()
    return [ann_to_out(a) for a in announcements]


@router.get("/all", response_model=list[AnnouncementOut])
async def list_all_announcements(
    db: AsyncSession = Depends(get_db),
    _: User = Depends(require_admin),
):
    result = await db.execute(select(Announcement).order_by(Announcement.created_at.desc()))
    return [ann_to_out(a) for a in result.scalars().all()]


@router.post("", response_model=AnnouncementOut, status_code=status.HTTP_201_CREATED)
async def create_announcement(
    data: AnnouncementCreate,
    db: AsyncSession = Depends(get_db),
    user: User = Depends(require_admin),
):
    ann = Announcement(**data.model_dump(), created_by=user.id)
    db.add(ann)
    await db.commit()
    await db.refresh(ann)
    return ann_to_out(ann, user.full_name)


@router.patch("/{ann_id}", response_model=AnnouncementOut)
async def update_announcement(
    ann_id: int,
    data: AnnouncementCreate,
    db: AsyncSession = Depends(get_db),
    _: User = Depends(require_admin),
):
    ann = await db.get(Announcement, ann_id)
    if ann is None:
        raise HTTPException(status_code=404, detail="Announcement not found")

    for field, value in data.model_dump().items():
        setattr(ann, field, value)
    await db.commit()
    await db.refresh(ann)
    return ann_to_out(ann)


@router.delete("/{ann_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_announcement(
    ann_id: int,
    db: AsyncSession = Depends(get_db),
    _: User = Depends(require_admin),
):
    ann = await db.get(Announcement, ann_id)
    if ann is None:
        raise HTTPException(status_code=404, detail="Announcement not found")
    await db.delete(ann)
    await db.commit()
