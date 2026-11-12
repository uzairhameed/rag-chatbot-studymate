from fastapi import APIRouter, Depends, HTTPException, Response, status

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.db.database import get_db
from app.db.models import ChatRoom, User
from app.schemas.rooms import RoomCreate, RoomRead
from app.services.auth import get_current_user

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
            .where(ChatRoom.owner_id == current_user.id)
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