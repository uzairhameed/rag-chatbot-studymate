from datetime import datetime

from pydantic import BaseModel, ConfigDict, EmailStr, Field

class UserCreate(BaseModel):
    """ Fields required when a user registers."""

    username: str=Field(min_length=3, max_length=50)
    email: EmailStr
    password: str = Field(min_length=8, max_length=128)

class UserRead(BaseModel):
    """Safe user fields returned by the API; never includes the password hash."""
    model_config=ConfigDict(from_attributes=True)

    id: int
    username: str
    email: EmailStr
    created_at: datetime

class LoginRequest(BaseModel):
    """Credentials sent to the JSON login endpoint"""

    email: EmailStr
    password: str

class TokenResponse(BaseModel):
    """JWT returned after successful login"""

    access_token: str
    token_type: str ="bearer"