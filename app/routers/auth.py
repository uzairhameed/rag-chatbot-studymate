from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import or_, select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from app.db.database import get_db
from app.db.models import User
from app.schemas.auth import LoginRequest, TokenResponse, UserCreate, UserRead
from app.services.auth import (
    create_access_token,
    hash_password,
    verify_password,
)

router= APIRouter(prefix="/auth", tags=["auth"])

@router.post(
    "/register",
    response_model=UserRead,
    status_code=status.HTTP_201_CREATED,
)

def register_user(
    data: UserCreate,
    db: Session= Depends(get_db),
) -> User:
    
    """Create an account, storing only a password hash."""
    email = str(data.email).strip().lower()
    username=data.username.strip()

    # Give a clear conflict response if this email or username is already taken.
    existing_user = db.scalar(
        select(User).where(
            or_(User.email == email, User.username == username)
        )
    )
    if existing_user:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Username or email is already registered",
        )

    user = User(
        username=username,
        email=email,
        hashed_password=hash_password(data.password),
    )
    db.add(user)

    try:
        db.commit()
    except IntegrityError:
        # Handles a duplicate created by another request at the same time.
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Username or email is already registered",
        )

    db.refresh(user)
    return user

@router.post("/login", response_model=TokenResponse)

def login(
    data: LoginRequest,
    db: Session = Depends(get_db),
) -> TokenResponse:
    """Check credentials and return a signed access token."""
    email = str(data.email).strip().lower()
    user = db.scalar(select(User).where(User.email == email))

    # Use the same response for an unknown email and a wrong password.
    if user is None or not verify_password(data.password, user.hashed_password):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect email or password",
            headers={"WWW-Authenticate": "Bearer"},
        )

    token = create_access_token(subject=user.email)
    return TokenResponse(access_token=token)