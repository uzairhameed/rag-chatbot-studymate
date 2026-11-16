import logging
import shutil
import tempfile
from pathlib import Path

from fastapi import APIRouter, Depends, File, HTTPException, UploadFile, status
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.db.database import get_db
from app.db.models import ChatRoom, UploadedFile, User
from app.schemas.files import UploadResponse
from app.services.auth import get_current_user
from app.services.ingestion.chunker import chunk_texts
from app.services.ingestion.csv import extract_csv
from app.services.ingestion.docx import extract_docx
from app.services.ingestion.pdf import extract_pdf
from app.services.storage import build_storage_key, upload_fileobj
from app.services.vector_store import delete_file_chunks, embed_and_store
from app.services.ingestion.markdown import extract_markdown
from app.services.ingestion.txt import extract_txt
from app.services.ingestion.pptx import extract_pptx
from app.services.ingestion.image import extract_image
from app.services.ingestion.audio import extract_audio
from app.services.ingestion.video import extract_video

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/upload", tags=["upload"])

# Enable only types whose extractors are implemented and checked.
SUPPORTED_FILE_TYPES = {
    ".pdf": ("pdf", extract_pdf),
    ".docx": ("docx", extract_docx),
    ".csv": ("csv", extract_csv),
    ".md": ("markdown", extract_markdown),
    ".txt": ("text", extract_txt),
    ".pptx": ("pptx", extract_pptx),
    ".png": ("image", extract_image),
    ".jpg": ("image", extract_image),
    ".jpeg": ("image", extract_image),
    ".webp": ("image", extract_image),
    ".mp3": ("audio", extract_audio),
    ".wav": ("audio", extract_audio),
    ".m4a": ("audio", extract_audio),
    ".ogg": ("audio", extract_audio),
    ".flac": ("audio", extract_audio),
    ".mp4": ("video", extract_video),
    ".mov": ("video", extract_video),
    ".avi": ("video", extract_video),
    ".mkv": ("video", extract_video),
    ".webm": ("video", extract_video),
    
}


@router.post(
    "/{room_id}",
    response_model=UploadResponse,
    status_code=status.HTTP_202_ACCEPTED,
)
def upload_room_file(
    room_id: int,
    file: UploadFile = File(...),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> UploadResponse:
    """Store, extract, chunk, and index a file for an owned room."""
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

    filename = Path(file.filename or "uploaded-file").name
    extension = Path(filename).suffix.lower()
    file_info = SUPPORTED_FILE_TYPES.get(extension)

    if file_info is None:
        raise HTTPException(
            status_code=status.HTTP_415_UNSUPPORTED_MEDIA_TYPE,
            detail="Currently supported: PDF, DOCX, CSV, TXT, Markdown, PPTX, PNG, JPG, JPEG, WEBP,MP3, WAV, M4A, OGG, and FLAC",
        )

    file_type, extractor = file_info
    storage_key = build_storage_key(room_id, filename)

    # Save a processing record so failures can be tracked in PostgreSQL.
    uploaded_file = UploadedFile(
        room_id=room_id,
        filename=filename,
        file_type=file_type,
        storage_key=storage_key,
        status="processing",
    )
    db.add(uploaded_file)
    db.commit()
    db.refresh(uploaded_file)
    file_id = uploaded_file.id

    temp_path: Path | None = None

    try:
        # Make a temporary copy because extractors work with file paths.
        with tempfile.NamedTemporaryFile(
            suffix=extension,
            prefix="studymate-",
            delete=False,
        ) as temp_file:
            temp_path = Path(temp_file.name)
            file.file.seek(0)
            shutil.copyfileobj(file.file, temp_file)

        # Preserve the original file in S3.
        with temp_path.open("rb") as original_file:
            upload_fileobj(original_file, storage_key, file.content_type)

        # Extract text, then split it into overlapping RAG chunks.
        text_parts = extractor(temp_path)
        chunks = chunk_texts(text_parts)
        if not chunks:
            raise ValueError("No text chunks were produced from this file")

        # Embed and store each chunk with metadata used for room filtering/citations.
        chunks_created = embed_and_store(
            chunks,
            room_id=room_id,
            file_id=file_id,
            filename=filename,
            file_type=file_type,
        )

        uploaded_file.status = "ready"
        uploaded_file.error_message = None
        db.commit()

        logger.info(
            "Indexed %d chunks for file_id=%s",
            chunks_created,
            file_id,
        )

    except Exception as exc:
        logger.exception("File processing failed for file_id=%s", file_id)

        # If vectors were written before a later error, remove those vectors.
        try:
            delete_file_chunks(file_id)
        except Exception:
            logger.exception("Could not clean Qdrant vectors for file_id=%s", file_id)

        # Roll back any failed DB transaction, then record the failed status.
        db.rollback()
        failed_file = db.get(UploadedFile, file_id)
        if failed_file is not None:
            failed_file.status = "failed"
            failed_file.error_message = str(exc)[:500]
            db.commit()

        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Could not process the uploaded file",
        ) from exc

    finally:
        file.file.close()
        if temp_path is not None:
            temp_path.unlink(missing_ok=True)

    return UploadResponse(
        file_id=file_id,
        chunks_created=chunks_created,
        status="ready",
    )