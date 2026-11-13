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
from app.services.ingestion.csv import extract_csv
from app.services.ingestion.docx import extract_docx
from app.services.ingestion.pdf import extract_pdf
from app.services.storage import build_storage_key, upload_fileobj

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/upload", tags=["upload"])

# Only enable formats whose extractors are implemented and checked so far.
SUPPORTED_FILE_TYPES = {
    ".pdf": ("pdf", extract_pdf),
    ".docx": ("docx", extract_docx),
    ".csv": ("csv", extract_csv),
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
    """Store an original in S3 and extract its text."""
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
            detail="Currently supported: PDF, DOCX, and CSV",
        )

    file_type, extractor = file_info
    storage_key = build_storage_key(room_id, filename)

    # Create the database record first so a failed upload can be recorded.
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

    temp_path: Path | None = None

    try:
        # Extractors need a path; use a temporary copy and remove it afterward.
        with tempfile.NamedTemporaryFile(
            suffix=extension,
            prefix="studymate-",
            delete=False,
        ) as temp_file:
            temp_path = Path(temp_file.name)
            file.file.seek(0)
            shutil.copyfileobj(file.file, temp_file)

        # Save the original file in S3.
        with temp_path.open("rb") as original_file:
            upload_fileobj(original_file, storage_key, file.content_type)

        # Extract text from the temporary copy.
        text_parts = extractor(temp_path)
        logger.info(
            "Extracted %d text sections from file_id=%s",
            len(text_parts),
            uploaded_file.id,
        )

    except Exception as exc:
        logger.exception("File processing failed for file_id=%s", uploaded_file.id)
        uploaded_file.status = "failed"
        uploaded_file.error_message = str(exc)[:500]
        db.commit()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Could not store or read the uploaded file",
        ) from exc

    finally:
        file.file.close()
        if temp_path is not None:
            temp_path.unlink(missing_ok=True)

    # Chunking, embeddings, and Qdrant storage come next.
    # Keep status as processing until those steps complete.
    return UploadResponse(
        file_id=uploaded_file.id,
        chunks_created=0,
        status="processing",
    )
