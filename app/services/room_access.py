"""Shared permission checks for room access."""

from fastapi import HTTPException, status
from sqlalchemy import or_, select
from sqlalchemy.orm import Session

from app.db.models import ChatRoom, RoomMember


def get_accessible_room(db: Session, room_id: int, user_id: int) -> ChatRoom:
    """Return a room when the user owns it or is an added member."""
    room = db.scalar(
        select(ChatRoom).where(
            ChatRoom.id == room_id,
            or_(
                ChatRoom.owner_id == user_id,
                ChatRoom.members.any(RoomMember.user_id == user_id),
            ),
        )
    )
    if room is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Room not found",
        )
    return room


def get_owned_room(db: Session, room_id: int, user_id: int) -> ChatRoom:
    """Return a room only when the user owns it."""
    room = db.scalar(
        select(ChatRoom).where(
            ChatRoom.id == room_id,
            ChatRoom.owner_id == user_id,
        )
    )
    if room is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Room not found",
        )
    return room
