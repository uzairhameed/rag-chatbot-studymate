import os
from datetime import datetime,timedelta, timezone

from dotenv import load_dotenv
from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from jose import JWTError, jwt
from sqlalchemy import select
from sqlalchemy.orm import Session
from passlib.context import CryptContext

from app.db.database import get_db
from app.db.models import User

load_dotenv()

SECRET_KEY = os.getenv("SECRET_KEY")
if not SECRET_KEY:
    raise RuntimeError("SECRET_KEY is missing from the environment")

ALGORITHM = os.getenv("ALGORITHM", "HS256")
ACCESS_TOKEN_EXPIRE_MINUTES = int(
    os.getenv("ACCESS_TOKEN_EXPIRE_MINUTES", "30")
)

# HTTP Bearer matches our JSON login endpoint and JWT Authorization header.
bearer_scheme = HTTPBearer(auto_error=False)

# Passwords are hashed before storage; plain-text passwords are never saved.
password_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

def hash_password(password: str) -> str:
    """Turn a plain-text password into a one-way password hash."""
    return password_context.hash(password)

def verify_password(password: str, hashed_password: str) -> bool:
    """Check a login password against the saved hash."""
    return password_context.verify(password, hashed_password)

def create_access_token(subject: str) -> str:
    """Create a signed JWT whose subject identifies the logged-in user."""
    expires_at = datetime.now(timezone.utc) + timedelta(
        minutes=ACCESS_TOKEN_EXPIRE_MINUTES
    )
    payload = {"sub": subject, "exp": expires_at}
    return jwt.encode(payload, SECRET_KEY, algorithm=ALGORITHM)

def get_current_user(
    credentials: HTTPAuthorizationCredentials | None = Depends(bearer_scheme),
    db: Session = Depends(get_db),
) -> User:
    """Validate the Bearer token and return its user, or reject the request."""
    unauthorized = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Invalid or missing authentication token",
        headers={"WWW-Authenticate": "Bearer"},
    )

    if credentials is None:
        raise unauthorized

    try:
        payload = jwt.decode(
            credentials.credentials,
            SECRET_KEY,
            algorithms=[ALGORITHM],
        )
        email = payload.get("sub")
        if not isinstance(email, str):
            raise unauthorized
    except JWTError:
        raise unauthorized

    user = db.scalar(select(User).where(User.email == email))
    if user is None:
        raise unauthorized

    return user

