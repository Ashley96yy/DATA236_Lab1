from __future__ import annotations

from fastapi import APIRouter, Depends, Query, status
from fastapi.security import OAuth2PasswordRequestForm

from app.deps import get_current_user
from app.repository import (
    add_favorite,
    create_user,
    get_favorite_by_user_and_restaurant,
    get_favorites_page,
    get_preferences,
    get_user_by_email,
    get_user_history,
    remove_favorite,
    update_preferences,
)
from app.schemas import (
    FavoritesListResponse,
    LoginResponse,
    SignupRequest,
    UserHistoryResponse,
    UserPreferencesResponse,
    UserPreferencesUpdateRequest,
    UserResponse,
)
from shared.auth.security import create_access_token, verify_password
from shared.db.session_store import build_session_document, store_session
from shared.schemas import LoginRequest
from shared.utils import conflict, not_found, unauthorized

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
    if get_user_by_email(payload.email) is not None:
        raise conflict("Email already exists.")
    user = create_user(name=payload.name, email=payload.email, password=payload.password)
    return _serialize_user(user)


@router.post("/auth/login", response_model=LoginResponse)
def login(payload: LoginRequest) -> LoginResponse:
    user = get_user_by_email(payload.email)
    if user is None or not verify_password(payload.password, user["password_hash"]):
        raise unauthorized("Invalid email or password.")
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
    return UserPreferencesResponse(**get_preferences(int(current_user["_id"])))


@router.put("/users/me/preferences", response_model=UserPreferencesResponse)
def save_preferences(
    payload: UserPreferencesUpdateRequest,
    current_user: dict = Depends(get_current_user),
) -> UserPreferencesResponse:
    return UserPreferencesResponse(
        **update_preferences(int(current_user["_id"]), payload.model_dump(exclude_none=True))
    )


@router.get("/users/me/favorites", response_model=FavoritesListResponse)
def list_favorites(
    page: int = Query(default=1, ge=1),
    limit: int = Query(default=20, ge=1, le=100),
    current_user: dict = Depends(get_current_user),
) -> FavoritesListResponse:
    return FavoritesListResponse(**get_favorites_page(int(current_user["_id"]), page=page, limit=limit))


@router.post("/users/me/favorites/{restaurant_id}", status_code=status.HTTP_201_CREATED)
def add_to_favorites(
    restaurant_id: int,
    current_user: dict = Depends(get_current_user),
) -> dict:
    if get_favorite_by_user_and_restaurant(int(current_user["_id"]), restaurant_id) is not None:
        raise conflict("Already in favorites.")
    add_favorite(int(current_user["_id"]), restaurant_id)
    return {"status": "added", "restaurant_id": restaurant_id}


@router.delete("/users/me/favorites/{restaurant_id}", status_code=status.HTTP_204_NO_CONTENT)
def remove_from_favorites(
    restaurant_id: int,
    current_user: dict = Depends(get_current_user),
) -> None:
    if not remove_favorite(int(current_user["_id"]), restaurant_id):
        raise not_found("Favorite not found.")


@router.get("/users/me/history", response_model=UserHistoryResponse)
def user_history(current_user: dict = Depends(get_current_user)) -> UserHistoryResponse:
    return UserHistoryResponse(**get_user_history(int(current_user["_id"])))
