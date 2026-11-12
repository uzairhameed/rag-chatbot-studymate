from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field

class RoomCreate(BaseModel):
    """Fields required to create a study room."""

    name: str = Field(min_length=1, max_length=120)
    description: str | None = None

class RoomRead(BaseModel):
    """Room fields returned by the API."""

    model_config = ConfigDict(from_attributes=True)

    id: int
    name: str
    description: str | None
    owner_id: int
    created_at: datetime

