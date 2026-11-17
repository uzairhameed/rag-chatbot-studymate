from __future__ import annotations
from sqlalchemy import (
    CheckConstraint,
    DateTime,
    ForeignKey,
    Integer,
    JSON,
    String,
    Text,
    func,
    UniqueConstraint,
)
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.database import Base

class User(Base):
    """A registered StudyMate user."""

    __tablename__ = "users"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    username: Mapped[str] = mapped_column(String(50), unique=True, index=True)
    email: Mapped[str] = mapped_column(String(255), unique=True, index=True)
    # Store a password hash here, never the user's plain-text password.
    hashed_password: Mapped[str] = mapped_column(String(255))
    created_at: Mapped[DateTime] = mapped_column(
        DateTime(timezone=True), server_default=func.now()
    )

    # Lets us access a user's rooms through user.rooms.
    rooms: Mapped[list[ChatRoom]] = relationship(back_populates="owner")
    messages: Mapped[list[ChatMessage]] = relationship(back_populates="user")
    # Membership records for rooms this user has been added to.
    room_memberships: Mapped[list[RoomMember]] = relationship(
    back_populates="user",
    cascade="all, delete-orphan",
)

class ChatRoom(Base):
    """A course or study room owned by one user."""
    __tablename__ = "chat_rooms"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    name: Mapped[str] = mapped_column(String(120))
    description: Mapped[str | None] = mapped_column(Text, nullable=True)
    owner_id: Mapped[int] = mapped_column(
        ForeignKey("users.id", ondelete="CASCADE"), index=True
    )
    created_at: Mapped[DateTime] = mapped_column(
        DateTime(timezone=True), server_default=func.now()
    )

    # Links this room back to the user who owns it.
    owner: Mapped[User] = relationship(back_populates="rooms")
    messages: Mapped[list[ChatMessage]] = relationship(
        back_populates="room", cascade="all, delete-orphan"
    )
    uploaded_files: Mapped[list[UploadedFile]] = relationship(
        back_populates="room", cascade="all, delete-orphan"
    )
    # Membership records for users explicitly added to this room.
    members: Mapped[list[RoomMember]] = relationship(
       back_populates="room",
       cascade="all, delete-orphan",
)

class RoomMember(Base):
    """A user explicitly granted access to a room."""
    __tablename__ = "room_members"
    __table_args__ = (
        UniqueConstraint(
            "room_id",
            "user_id",
            name="uq_room_members_room_user",
        ),
    )

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    room_id: Mapped[int] = mapped_column(
        ForeignKey("chat_rooms.id", ondelete="CASCADE"),
        index=True,
    )
    user_id: Mapped[int] = mapped_column(
        ForeignKey("users.id", ondelete="CASCADE"),
        index=True,
    )
    joined_at: Mapped[DateTime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
    )

    room: Mapped[ChatRoom] = relationship(back_populates="members")
    user: Mapped[User] = relationship(back_populates="room_memberships")

class ChatMessage(Base):
    """One user or assistant message in a room."""
    __tablename__ = "chat_messages"
    __table_args__ = (
        CheckConstraint("role IN ('user', 'assistant')", name="valid_message_role"),
    )

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    room_id: Mapped[int] = mapped_column(
        ForeignKey("chat_rooms.id", ondelete="CASCADE"), index=True
    )
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id"), index=True)
    role: Mapped[str] = mapped_column(String(20))
    content: Mapped[str] = mapped_column(Text)
    # Keeps citation details with the answer; defaults to [] when there are none.
    sources: Mapped[list[dict[str, object]]] = mapped_column(JSON, default=list)
    created_at: Mapped[DateTime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), index=True
    )
    room: Mapped[ChatRoom] = relationship(back_populates="messages")
    user: Mapped[User] = relationship(back_populates="messages")

class UploadedFile(Base):
    """Database record for an original file stored in S3."""
    __tablename__ = "uploaded_files"
    __table_args__ = (
        CheckConstraint(
            "status IN ('processing', 'ready', 'failed')",
            name="valid_upload_status",
        ),
    )

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    room_id: Mapped[int] = mapped_column(
        ForeignKey("chat_rooms.id", ondelete="CASCADE"), index=True
    )
    filename: Mapped[str] = mapped_column(String(255))
    file_type: Mapped[str] = mapped_column(String(100))
    # S3 object key, for example: rooms/12/files/lecture-notes.pdf
    storage_key: Mapped[str] = mapped_column(String(1024), unique=True)
    status: Mapped[str] = mapped_column(String(20), default="processing")
    error_message: Mapped[str | None] = mapped_column(Text, nullable=True)
    uploaded_at: Mapped[DateTime] = mapped_column(
        DateTime(timezone=True), server_default=func.now()
    )

    room: Mapped[ChatRoom] = relationship(back_populates="uploaded_files")
