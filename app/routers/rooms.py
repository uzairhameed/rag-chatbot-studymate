from fastapi import APIRouter, Depends, HTTPException, Response, status

from sqlalchemy import or_,select
from sqlalchemy.orm import Session

from app.db.database import get_db
from app.db.models import ChatRoom, User, RoomMember
from app.schemas.rooms import RoomCreate, RoomRead,RoomMemberCreate,RoomMemberRead
from app.services.auth import get_current_user
from sqlalchemy.exc import IntegrityError


router = APIRouter(prefix="/rooms", tags=["rooms"])

@router.get("/", response_model=list[RoomRead])
def list_rooms(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> list[ChatRoom]:
    """Return only rooms owned by the signed-in user."""
    return list(
        db.scalars(
            select(ChatRoom)
            .where(
        or_(
        ChatRoom.owner_id == current_user.id,
        ChatRoom.members.any(RoomMember.user_id == current_user.id),
    )
)
            .order_by(ChatRoom.created_at.desc())
        ).all()
    )

@router.post(
    "/",
    response_model=RoomRead,
    status_code=status.HTTP_201_CREATED,
)
def create_room(
    data: RoomCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> ChatRoom:
    """Create a room owned by the signed-in user."""
    room = ChatRoom(
        name=data.name.strip(),
        description=data.description,
        owner_id=current_user.id,
    )
    db.add(room)
    db.commit()
    db.refresh(room)
    return room

@router.delete("/{room_id}", status_code=status.HTTP_204_NO_CONTENT)

def delete_room(
    room_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> Response:
    """Delete a room only when it belongs to the signed-in user."""
    room = db.scalar(
        select(ChatRoom).where(
            ChatRoom.id == room_id,
            ChatRoom.owner_id == current_user.id,
        )
    )
    if room is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Room not found",
        )

    db.delete(room)
    db.commit()
    return Response(status_code=status.HTTP_204_NO_CONTENT)

@router.post(
    "/{room_id}/members",
    response_model=RoomMemberRead,
    status_code=status.HTTP_201_CREATED,
)
def add_room_member(
    room_id: int,
    data: RoomMemberCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> RoomMemberRead:
    """Let a room owner grant access to an existing user."""
    room = db.scalar(
        select(ChatRoom).where(
            ChatRoom.id == room_id,
            ChatRoom.owner_id == current_user.id,
        )
    )
    if room is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Room not found",
        )

    member = db.scalar(select(User).where(User.email == data.email))
    if member is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="No user found with that email",
        )

    if member.id == current_user.id:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="The room owner is already a room member",
        )

    existing_membership = db.scalar(
        select(RoomMember).where(
            RoomMember.room_id == room_id,
            RoomMember.user_id == member.id,
        )
    )
    if existing_membership is not None:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="That user is already a room member",
        )

    membership = RoomMember(room_id=room_id, user_id=member.id)
    db.add(membership)

    try:
        db.commit()
    except IntegrityError:
        # Handles a duplicate membership created by a simultaneous request.
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="That user is already a room member",
        )

    db.refresh(membership)
    return RoomMemberRead(
        user_id=member.id,
        username=member.username,
        email=member.email,
        joined_at=membership.joined_at,
    )