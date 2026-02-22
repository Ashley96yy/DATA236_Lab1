from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.api.deps import get_current_user
from app.core.config import get_settings
from app.core.security import create_access_token, get_password_hash, verify_password
from app.db.session import get_db
from app.models.owner import Owner
from app.models.user import User
from app.schemas.auth import (
    AuthOwnerResponse,
    AuthUserResponse,
    LoginRequest,
    LoginResponse,
    OwnerLoginResponse,
    OwnerSignupRequest,
    SignupRequest,
)

router = APIRouter(prefix="/auth", tags=["auth"])


def _signup_user(payload: SignupRequest, db: Session) -> AuthUserResponse:
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


def _login_user(payload: LoginRequest, db: Session) -> LoginResponse:
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
        token_type="user",
    )
    return LoginResponse(
        access_token=token,
        token_type="bearer",
        user=AuthUserResponse.model_validate(user),
    )


@router.post("/signup", response_model=AuthUserResponse, status_code=status.HTTP_201_CREATED)
def signup(payload: SignupRequest, db: Session = Depends(get_db)) -> AuthUserResponse:
    return _signup_user(payload, db)


@router.post("/login", response_model=LoginResponse)
def login(payload: LoginRequest, db: Session = Depends(get_db)) -> LoginResponse:
    return _login_user(payload, db)


@router.post("/user/signup", response_model=AuthUserResponse, status_code=status.HTTP_201_CREATED)
def signup_user(payload: SignupRequest, db: Session = Depends(get_db)) -> AuthUserResponse:
    return _signup_user(payload, db)


@router.post("/user/login", response_model=LoginResponse)
def login_user(payload: LoginRequest, db: Session = Depends(get_db)) -> LoginResponse:
    return _login_user(payload, db)


@router.post("/owner/signup", response_model=AuthOwnerResponse, status_code=status.HTTP_201_CREATED)
def signup_owner(payload: OwnerSignupRequest, db: Session = Depends(get_db)) -> AuthOwnerResponse:
    email = payload.email.strip().lower()

    existing_owner = db.execute(select(Owner).where(Owner.email == email)).scalar_one_or_none()
    if existing_owner is not None:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Email already exists.",
        )

    owner = Owner(
        name=payload.name.strip(),
        email=email,
        password_hash=get_password_hash(payload.password),
        restaurant_location=payload.restaurant_location.strip(),
    )
    db.add(owner)
    db.commit()
    db.refresh(owner)
    return AuthOwnerResponse.model_validate(owner)


@router.post("/owner/login", response_model=OwnerLoginResponse)
def login_owner(payload: LoginRequest, db: Session = Depends(get_db)) -> OwnerLoginResponse:
    email = payload.email.strip().lower()
    owner = db.execute(select(Owner).where(Owner.email == email)).scalar_one_or_none()

    if owner is None or not verify_password(payload.password, owner.password_hash):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid email or password.",
        )

    settings = get_settings()
    token = create_access_token(
        subject=str(owner.id),
        expires_minutes=settings.jwt_access_token_expire_minutes,
        token_type="owner",
    )
    return OwnerLoginResponse(
        access_token=token,
        token_type="bearer",
        owner=AuthOwnerResponse.model_validate(owner),
    )


@router.get("/me", response_model=AuthUserResponse)
def read_current_user(
    current_user: Annotated[User, Depends(get_current_user)],
) -> AuthUserResponse:
    return AuthUserResponse.model_validate(current_user)
