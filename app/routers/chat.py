"""Chat, history, and history-clearing endpoints."""
import re
from pathlib import Path
from fastapi import APIRouter, Depends, HTTPException, Query, Response, status
from sqlalchemy import delete, select
from sqlalchemy.orm import Session

from app.db.database import get_db
from app.db.models import ChatMessage, ChatRoom, User, UploadedFile
from app.schemas.chat import ChatMessageRead, ChatRequest, ChatResponse
from app.services.auth import get_current_user
from app.services.rag import answer_from_chunks
from app.services.vector_store import get_file_chunks, search_chunks
from app.services.room_access import get_accessible_room


router = APIRouter(prefix="/chat", tags=["chat"])


def get_owned_room(db: Session, room_id: int, user_id: int) -> ChatRoom:
    """Find a room only when it belongs to the signed-in user."""
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


def find_summary_file(
    db: Session,
    room_id: int,
    query: str,
) -> UploadedFile | None:
    """Find the ready file named in a document-summary request."""
    summary_terms = ("summarize", "summarise", "summary", "overview")
    if not any(term in query.lower() for term in summary_terms):
        return None

    files = list(
        db.scalars(
            select(UploadedFile).where(
                UploadedFile.room_id == room_id,
                UploadedFile.status == "ready",
            )
        ).all()
    )

    query_words = set(re.findall(r"[a-z0-9]+", query.lower()))
    matches = []

    for uploaded_file in files:
        filename_words = set(
            re.findall(
                r"[a-z0-9]+",
                Path(uploaded_file.filename).stem.lower(),
            )
        )
        if filename_words and filename_words.issubset(query_words):
            matches.append(uploaded_file)

    if len(matches) == 1:
        return matches[0]

    # If there is only one ready file, “summarize this document” is unambiguous.
    if not matches and len(files) == 1:
        return files[0]

    return None

@router.post("/{room_id}", response_model=ChatResponse)
def chat_in_room(
    room_id: int,
    data: ChatRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> ChatResponse:
    """Answer a question from this room's documents and save the conversation."""
    get_accessible_room(db, room_id, current_user.id) 
    # Load the six latest saved messages, then restore their chronological order.
    recent_messages = list(
        db.scalars(
            select(ChatMessage)
            .where(ChatMessage.room_id == room_id)
            .order_by(ChatMessage.created_at.desc(), ChatMessage.id.desc())
            .limit(6)
        ).all()
    )
    history = [
        {"role": message.role, "content": message.content}
        for message in reversed(recent_messages)
    ]

    summary_file = find_summary_file(db, room_id, data.query)

    if summary_file is not None:
        chunks = get_file_chunks(summary_file.id)
    else:
        chunks = search_chunks(data.query, room_id=room_id, limit=5)

    answer, sources = answer_from_chunks(data.query, history, chunks)
    # Store both sides of the conversation; user messages have no citations.
    user_message = ChatMessage(
        room_id=room_id,
        user_id=current_user.id,
        role="user",
        content=data.query,
        sources=[],
    )
    assistant_message = ChatMessage(
        room_id=room_id,
        user_id=current_user.id,
        role="assistant",
        content=answer,
        sources=sources,
    )
    db.add_all([user_message, assistant_message])
    db.commit()

    # The response schema requires sources to always be a list.
    return ChatResponse(answer=answer, sources=sources)


@router.get("/{room_id}/history", response_model=list[ChatMessageRead])
def get_room_history(
    room_id: int,
    skip: int = Query(default=0, ge=0),
    limit: int = Query(default=50, ge=1, le=100),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> list[ChatMessage]:
    """Return room messages in chronological order, with pagination."""
    get_accessible_room(db, room_id, current_user.id)
    
    return list(
        db.scalars(
            select(ChatMessage)
            .where(ChatMessage.room_id == room_id)
            .order_by(ChatMessage.created_at, ChatMessage.id)
            .offset(skip)
            .limit(limit)
        ).all()
    )


@router.delete(
    "/{room_id}/history",
    status_code=status.HTTP_204_NO_CONTENT,
)
def clear_room_history(
    room_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> Response:
    """Delete every message in a room; only its owner may do this."""
    get_owned_room(db, room_id, current_user.id)
    db.execute(delete(ChatMessage).where(ChatMessage.room_id == room_id))
    db.commit()
    return Response(status_code=status.HTTP_204_NO_CONTENT)
