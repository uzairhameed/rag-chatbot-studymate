from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field,field_validator

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

class RoomMemberCreate(BaseModel):
    """Email address of an existing user to add to a room."""

    email: str = Field(min_length=3, max_length=255)

    @field_validator("email")
    @classmethod
    def normalize_email(cls, value: str) -> str:
        """Trim whitespace and normalize email casing before lookup."""
        return value.strip().lower()


class RoomMemberRead(BaseModel):
    """Basic details returned after adding a member."""

    user_id: int
    username: str
    email: str
    joined_at: datetime