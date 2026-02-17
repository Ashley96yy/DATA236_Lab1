from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.api.deps import get_current_user
from app.core.config import get_settings
from app.core.security import create_access_token, get_password_hash, verify_password
from app.db.session import get_db
from app.models.user import User
from app.schemas.auth import AuthUserResponse, LoginRequest, LoginResponse, SignupRequest

router = APIRouter(prefix="/auth", tags=["auth"])


@router.post("/signup", response_model=AuthUserResponse, status_code=status.HTTP_201_CREATED)
def signup(payload: SignupRequest, db: Session = Depends(get_db)) -> AuthUserResponse:
    email = payload.email.strip().lower()

    existing_user = db.execute(select(User).where(User.email == email)).scalar_one_or_none()
    if existing_user is not None:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Email already exists.",
        )

    user = User(
        name=payload.name.strip(),
        email=email,
        password_hash=get_password_hash(payload.password),
    )
    db.add(user)
    db.commit()
    db.refresh(user)
    return AuthUserResponse.model_validate(user)


@router.post("/login", response_model=LoginResponse)
def login(payload: LoginRequest, db: Session = Depends(get_db)) -> LoginResponse:
    email = payload.email.strip().lower()
    user = db.execute(select(User).where(User.email == email)).scalar_one_or_none()

    if user is None or not verify_password(payload.password, user.password_hash):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid email or password.",
        )

    settings = get_settings()
    token = create_access_token(
        subject=str(user.id),
        expires_minutes=settings.jwt_access_token_expire_minutes,
    )
    return LoginResponse(
        access_token=token,
        token_type="bearer",
        user=AuthUserResponse.model_validate(user),
    )


@router.get("/me", response_model=AuthUserResponse)
def read_current_user(
    current_user: Annotated[User, Depends(get_current_user)],
) -> AuthUserResponse:
    return AuthUserResponse.model_validate(current_user)
