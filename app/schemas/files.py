"""Request and response schemas for uploaded files."""

from datetime import datetime
from typing import Literal

from pydantic import BaseModel, ConfigDict


class UploadResponse(BaseModel):
    """Summary returned after a file upload is processed."""

    file_id: int
    chunks_created: int
    status: Literal["processing", "ready", "failed"]


class UploadedFileRead(BaseModel):
    """File details shown in a room's sidebar."""

    model_config = ConfigDict(from_attributes=True)

    id: int
    filename: str
    file_type: str
    status: Literal["processing", "ready", "failed"]
    error_message: str | None
    uploaded_at: datetime
