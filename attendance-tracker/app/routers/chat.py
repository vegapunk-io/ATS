"""Team chat endpoints."""
from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import joinedload

from ..database import get_db
from ..deps import get_current_user
from ..models import ChatMessage, User
from ..schemas import ChatMessageCreate, ChatMessageOut

router = APIRouter(prefix="/api/chat", tags=["chat"])


def msg_to_out(m: ChatMessage) -> ChatMessageOut:
    return ChatMessageOut(
        id=m.id,
        sender_id=m.sender_id,
        sender_name=m.sender.full_name if m.sender else None,
        channel=m.channel,
        content=m.content,
        created_at=m.created_at,
    )


@router.get("", response_model=list[ChatMessageOut])
async def list_messages(
    channel: str = "general",
    limit: int = Query(default=50, le=200),
    before: int | None = None,
    db: AsyncSession = Depends(get_db),
    user: User = Depends(get_current_user),
):
    query = (
        select(ChatMessage)
        .options(joinedload(ChatMessage.sender))
        .where(ChatMessage.channel == channel)
        .order_by(ChatMessage.created_at.desc())
        .limit(limit)
    )
    if before:
        query = query.where(ChatMessage.id < before)
    result = await db.execute(query)
    messages = list(result.scalars().all())
    messages.reverse()
    return [msg_to_out(m) for m in messages]


@router.post("", response_model=ChatMessageOut, status_code=status.HTTP_201_CREATED)
async def send_message(
    data: ChatMessageCreate,
    db: AsyncSession = Depends(get_db),
    user: User = Depends(get_current_user),
):
    if user.person_id is None:
        raise HTTPException(status_code=400, detail="No linked person")
    msg = ChatMessage(
        sender_id=user.person_id,
        channel=data.channel,
        content=data.content,
    )
    db.add(msg)
    await db.commit()
    await db.refresh(msg, attribute_names=["sender"])
    return msg_to_out(msg)


@router.get("/channels")
async def list_channels(user: User = Depends(get_current_user)):
    return {"channels": ["general", "team", "random"]}
