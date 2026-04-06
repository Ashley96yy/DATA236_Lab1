from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import OAuth2PasswordRequestForm

from app.deps import get_current_user
from app.repository import create_user, get_preferences, get_user_by_email, update_preferences
from app.schemas import (
    LoginRequest,
    LoginResponse,
    SignupRequest,
    UserPreferencesResponse,
    UserPreferencesUpdateRequest,
    UserResponse,
)
from shared.auth.security import create_access_token, verify_password
from shared.db.session_store import build_session_document, store_session

router = APIRouter()


def _serialize_user(user: dict) -> UserResponse:
    return UserResponse(
        id=int(user["_id"]),
        name=user["name"],
        email=user["email"],
        phone=user.get("phone"),
        about_me=user.get("about_me"),
        city=user.get("city"),
        state=user.get("state"),
        country=user.get("country"),
        languages=user.get("languages", []),
        gender=user.get("gender"),
        avatar_url=user.get("avatar_url"),
    )


@router.post("/auth/signup", response_model=UserResponse, status_code=status.HTTP_201_CREATED)
def signup(payload: SignupRequest) -> UserResponse:
    existing = get_user_by_email(payload.email)
    if existing is not None:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="Email already exists.")
    user = create_user(name=payload.name, email=payload.email, password=payload.password)
    return _serialize_user(user)


@router.post("/auth/login", response_model=LoginResponse)
def login(payload: LoginRequest) -> LoginResponse:
    user = get_user_by_email(payload.email)
    if user is None or not verify_password(payload.password, user["password_hash"]):
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid email or password.")

    token = create_access_token(subject=str(user["_id"]), token_type="user")
    store_session(build_session_document(subject_id=int(user["_id"]), role="user", token=token))
    return LoginResponse(access_token=token, user=_serialize_user(user))


@router.post("/auth/token", response_model=LoginResponse, include_in_schema=False)
def login_token(form_data: OAuth2PasswordRequestForm = Depends()) -> LoginResponse:
    return login(LoginRequest(email=form_data.username, password=form_data.password))


@router.get("/users/me", response_model=UserResponse)
def read_me(current_user: dict = Depends(get_current_user)) -> UserResponse:
    return _serialize_user(current_user)


@router.get("/users/me/preferences", response_model=UserPreferencesResponse)
def read_preferences(current_user: dict = Depends(get_current_user)) -> UserPreferencesResponse:
    preferences = get_preferences(int(current_user["_id"]))
    return UserPreferencesResponse(**preferences)


@router.put("/users/me/preferences", response_model=UserPreferencesResponse)
def save_preferences(
    payload: UserPreferencesUpdateRequest,
    current_user: dict = Depends(get_current_user),
) -> UserPreferencesResponse:
    preferences = update_preferences(int(current_user["_id"]), payload.model_dump(exclude_none=True))
    return UserPreferencesResponse(**preferences)
