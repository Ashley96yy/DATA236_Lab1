import uuid
from typing import Annotated

from fastapi import APIRouter, Depends, File, HTTPException, Request, UploadFile, status
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.api.deps import get_current_user
from app.core.config import get_settings
from app.db.session import get_db
from app.models.user import User
from app.models.user_preference import UserPreference
from app.schemas.user import (
    AvatarUploadResponse,
    UserPreferencesResponse,
    UserPreferencesUpdateRequest,
    UserProfileResponse,
    UserProfileUpdateRequest,
)

router = APIRouter(prefix="/users", tags=["users"])
settings = get_settings()
avatars_dir = settings.uploads_dir / "avatars"
avatars_dir.mkdir(parents=True, exist_ok=True)
allowed_avatar_extensions = {".jpg", ".jpeg", ".png", ".webp", ".gif"}
max_avatar_size_bytes = 5 * 1024 * 1024


def _serialize_languages(languages: list[str] | None) -> str | None:
    if not languages:
        return None
    return ",".join(languages)


def _parse_languages(languages: str | None) -> list[str] | None:
    if languages is None:
        return None
    cleaned = [item.strip() for item in languages.split(",") if item.strip()]
    return cleaned


def _to_profile_response(user: User) -> UserProfileResponse:
    return UserProfileResponse(
        id=user.id,
        name=user.name,
        email=user.email,
        phone=user.phone,
        about_me=user.about_me,
        city=user.city,
        state=user.state,
        country=user.country,
        languages=_serialize_languages(user.languages),
        gender=user.gender,
        avatar_url=user.avatar_url,
    )


def _to_preferences_response(preferences: UserPreference | None) -> UserPreferencesResponse:
    if preferences is None:
        return UserPreferencesResponse()

    return UserPreferencesResponse(
        cuisines=preferences.cuisines or [],
        price_range=preferences.price_range,
        preferred_locations=preferences.preferred_locations or [],
        search_radius_km=preferences.search_radius_km,
        dietary_needs=preferences.dietary_needs or [],
        ambiance=preferences.ambiance or [],
        sort_preference=preferences.sort_preference or "rating",
    )


def _build_avatar_url(request: Request, filename: str) -> str:
    base_url = str(request.base_url).rstrip("/")
    return f"{base_url}/uploads/avatars/{filename}"


@router.get("/me", response_model=UserProfileResponse)
def get_me(current_user: Annotated[User, Depends(get_current_user)]) -> UserProfileResponse:
    return _to_profile_response(current_user)


@router.put("/me", response_model=UserProfileResponse)
def update_me(
    payload: UserProfileUpdateRequest,
    db: Annotated[Session, Depends(get_db)],
    current_user: Annotated[User, Depends(get_current_user)],
) -> UserProfileResponse:
    updates = payload.model_dump(exclude_unset=True)

    if "languages" in updates:
        current_user.languages = _parse_languages(updates.pop("languages"))

    for field, value in updates.items():
        setattr(current_user, field, value)

    db.add(current_user)
    db.commit()
    db.refresh(current_user)
    return _to_profile_response(current_user)


@router.get("/me/preferences", response_model=UserPreferencesResponse)
def get_my_preferences(
    db: Annotated[Session, Depends(get_db)],
    current_user: Annotated[User, Depends(get_current_user)],
) -> UserPreferencesResponse:
    preferences = db.execute(
        select(UserPreference).where(UserPreference.user_id == current_user.id)
    ).scalar_one_or_none()
    return _to_preferences_response(preferences)


@router.put("/me/preferences", response_model=UserPreferencesResponse)
def update_my_preferences(
    payload: UserPreferencesUpdateRequest,
    db: Annotated[Session, Depends(get_db)],
    current_user: Annotated[User, Depends(get_current_user)],
) -> UserPreferencesResponse:
    preferences = db.execute(
        select(UserPreference).where(UserPreference.user_id == current_user.id)
    ).scalar_one_or_none()
    if preferences is None:
        preferences = UserPreference(user_id=current_user.id, sort_preference="rating")

    updates = payload.model_dump(exclude_unset=True)
    for field, value in updates.items():
        setattr(preferences, field, value)

    db.add(preferences)
    db.commit()
    db.refresh(preferences)
    return _to_preferences_response(preferences)


@router.post("/me/avatar", response_model=AvatarUploadResponse, status_code=status.HTTP_201_CREATED)
async def upload_my_avatar(
    request: Request,
    file: UploadFile = File(...),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> AvatarUploadResponse:
    if not file.filename:
        raise HTTPException(status_code=400, detail="No file selected.")

    extension = f".{file.filename.rsplit('.', 1)[-1].lower()}" if "." in file.filename else ""
    if extension not in allowed_avatar_extensions:
        raise HTTPException(status_code=400, detail="Unsupported image format.")

    if not (file.content_type and file.content_type.startswith("image/")):
        raise HTTPException(status_code=400, detail="File must be an image.")

    file_bytes = await file.read()
    if len(file_bytes) > max_avatar_size_bytes:
        raise HTTPException(status_code=413, detail="Image size must be 5MB or less.")

    filename = f"user-{current_user.id}-{uuid.uuid4().hex}{extension}"
    destination_path = avatars_dir / filename
    destination_path.write_bytes(file_bytes)

    current_user.avatar_url = _build_avatar_url(request, filename)
    db.add(current_user)
    db.commit()
    db.refresh(current_user)

    return AvatarUploadResponse(avatar_url=current_user.avatar_url)
