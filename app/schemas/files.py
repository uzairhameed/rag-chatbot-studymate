from typing import Literal

from pydantic import BaseModel

class UploadResponse(BaseModel):
    """Summary returned after the orignal file is stored"""

    file_id: int
    chunks_created: int
    status: Literal["processing","ready","failed"]