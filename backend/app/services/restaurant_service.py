"""
Restaurant service — all DB access and business rules for Phase 3.

Functions:
    create_restaurant     — validate + persist a new listing
    get_restaurant_by_id  — fetch single restaurant with photos
    search_restaurants    — filter / sort / paginate
    upload_photos         — dual-auth, quota enforcement, file I/O, DB insert
"""
from __future__ import annotations

import uuid
from pathlib import Path
from typing import Optional

from fastapi import UploadFile
from sqlalchemy import cast, func, or_, select, String
from sqlalchemy.orm import Session, selectinload

from app.core.config import get_settings
from app.models.owner import Owner
from app.models.restaurant import Restaurant
from app.models.restaurant_photo import RestaurantPhoto
from app.models.review import Review
from app.models.user import User
from app.schemas.restaurant import (
    PhotoResponse,
    RestaurantCard,
    RestaurantCreate,
    RestaurantResponse,
    RestaurantSearchResponse,
)
from app.services.errors import (
    ServiceBadRequest,
    ServiceForbidden,
    ServiceNotFound,
    ServiceUnauthorized,
)

settings = get_settings()
_photos_dir: Path = settings.uploads_dir / "restaurant_photos"
_photos_dir.mkdir(parents=True, exist_ok=True)

_ALLOWED_EXTENSIONS = {".jpg", ".jpeg", ".png", ".webp"}
_ALLOWED_MIME_TYPES = {"image/jpeg", "image/png", "image/webp"}
_MAX_PHOTO_BYTES = 10 * 1024 * 1024   # 10 MB
_MAX_PHOTOS_TOTAL = 5


# ---------------------------------------------------------------------------
# Private helpers
# ---------------------------------------------------------------------------

def _build_photo_url(base_url: str, filename: str) -> str:
    return f"{base_url.rstrip('/')}/uploads/restaurant_photos/{filename}"


def _orm_to_response(
    r: Restaurant,
    average_rating: float = 0.0,
    review_count: int = 0,
) -> RestaurantResponse:
    photos = [
        PhotoResponse(
            id=p.id,
            photo_url=p.photo_url,
            uploaded_by_user_id=p.uploaded_by_user_id,
            uploaded_by_owner_id=p.uploaded_by_owner_id,
            created_at=p.created_at,
        )
        for p in (r.photos or [])
    ]
    return RestaurantResponse(
        id=r.id,
        name=r.name,
        cuisine_type=r.cuisine_type,
        description=r.description,
        street=r.street,
        city=r.city,
        state=r.state,
        zip_code=r.zip_code,
        country=r.country,
        latitude=r.latitude,
        longitude=r.longitude,
        phone=r.phone,
        email=r.email,
        hours_json=r.hours_json,
        pricing_tier=r.pricing_tier,
        amenities=r.amenities,
        created_by_user_id=r.created_by_user_id,
        claimed_by_owner_id=r.claimed_by_owner_id,
        average_rating=average_rating,
        review_count=review_count,
        photos=photos,
        created_at=r.created_at,
        updated_at=r.updated_at,
    )


def _orm_to_card(
    r: Restaurant,
    average_rating: float = 0.0,
    review_count: int = 0,
) -> RestaurantCard:
    cover = r.photos[0].photo_url if r.photos else None
    return RestaurantCard(
        id=r.id,
        name=r.name,
        cuisine_type=r.cuisine_type,
        description=r.description,
        city=r.city,
        state=r.state,
        pricing_tier=r.pricing_tier,
        amenities=r.amenities,
        average_rating=average_rating,
        review_count=review_count,
        cover_photo_url=cover,
    )


def _fetch_ratings(db: Session, restaurant_ids: list[int]) -> dict[int, tuple[float, int]]:
    """Return {restaurant_id: (avg_rating, review_count)} for a batch of IDs."""
    if not restaurant_ids:
        return {}
    rows = db.execute(
        select(
            Review.restaurant_id,
            func.avg(Review.rating).label("avg"),
            func.count(Review.id).label("cnt"),
        )
        .where(Review.restaurant_id.in_(restaurant_ids))
        .group_by(Review.restaurant_id)
    ).all()
    return {row.restaurant_id: (round(float(row.avg), 2), int(row.cnt)) for row in rows}


# ---------------------------------------------------------------------------
# Create
# ---------------------------------------------------------------------------

def create_restaurant(
    db: Session,
    data: RestaurantCreate,
    created_by_user_id: int,
) -> RestaurantResponse:
    """Persist a new restaurant listing created by an authenticated user."""
    restaurant = Restaurant(
        name=data.name,
        cuisine_type=data.cuisine_type,
        description=data.description,
        street=data.street,
        city=data.city,
        state=data.state,
        zip_code=data.zip_code,
        country=data.country,
        latitude=data.latitude,
        longitude=data.longitude,
        phone=data.phone,
        email=data.email,
        hours_json=data.hours_json,
        pricing_tier=data.pricing_tier,
        amenities=data.amenities,
        created_by_user_id=created_by_user_id,
    )
    db.add(restaurant)
    db.commit()
    db.refresh(restaurant)
    restaurant.photos = []   # avoid lazy-load on fresh object
    return _orm_to_response(restaurant, average_rating=0.0, review_count=0)


# ---------------------------------------------------------------------------
# Read / Search
# ---------------------------------------------------------------------------

def get_restaurant_by_id(db: Session, restaurant_id: int) -> RestaurantResponse:
    """Return a single restaurant with photos + real rating; raise ServiceNotFound if absent."""
    restaurant = db.execute(
        select(Restaurant)
        .options(selectinload(Restaurant.photos))
        .where(Restaurant.id == restaurant_id)
    ).scalar_one_or_none()

    if restaurant is None:
        raise ServiceNotFound(f"Restaurant {restaurant_id} not found.")

    ratings = _fetch_ratings(db, [restaurant_id])
    avg, cnt = ratings.get(restaurant_id, (0.0, 0))
    return _orm_to_response(restaurant, average_rating=avg, review_count=cnt)


def search_restaurants(
    db: Session,
    *,
    name: Optional[str] = None,
    cuisine: Optional[str] = None,
    keywords: Optional[str] = None,
    city: Optional[str] = None,
    zip_code: Optional[str] = None,
    sort: Optional[str] = "name",
    page: int = 1,
    limit: int = 10,
) -> RestaurantSearchResponse:
    """
    Filter, sort, and paginate restaurants.

    keywords is matched against name, description, and the amenities JSON
    column (cast to string for a LIKE search so "wifi" matches ["WiFi",...]).
    """
    stmt = select(Restaurant).options(selectinload(Restaurant.photos))

    if name:
        stmt = stmt.where(Restaurant.name.ilike(f"%{name}%"))
    if cuisine:
        stmt = stmt.where(Restaurant.cuisine_type.ilike(f"%{cuisine}%"))
    if city:
        stmt = stmt.where(Restaurant.city.ilike(f"%{city}%"))
    if zip_code:
        stmt = stmt.where(Restaurant.zip_code == zip_code)
    if keywords:
        kw = f"%{keywords}%"
        stmt = stmt.where(
            or_(
                Restaurant.name.ilike(kw),
                Restaurant.description.ilike(kw),
                cast(Restaurant.amenities, String).ilike(kw),
            )
        )

    # Sorting — Phase 4 will replace with real AVG(rating) subquery
    if sort in ("name", "rating", "review_count"):
        stmt = stmt.order_by(Restaurant.name.asc())

    # Count total before applying pagination
    count_stmt = select(func.count()).select_from(stmt.subquery())
    total: int = db.execute(count_stmt).scalar_one()

    stmt = stmt.offset((page - 1) * limit).limit(limit)
    restaurants = db.execute(stmt).scalars().all()

    rids = [r.id for r in restaurants]
    ratings = _fetch_ratings(db, rids)

    return RestaurantSearchResponse(
        items=[
            _orm_to_card(r, *ratings.get(r.id, (0.0, 0)))
            for r in restaurants
        ],
        total=total,
        page=page,
        limit=limit,
    )


# ---------------------------------------------------------------------------
# Photos
# ---------------------------------------------------------------------------

async def upload_photos(
    db: Session,
    restaurant_id: int,
    files: list[UploadFile],
    token_payload: dict,
    base_url: str,
) -> list[PhotoResponse]:
    """
    Dual-auth photo upload.

    token_payload must already be decoded by the endpoint (HTTP layer).
    Raises ServiceNotFound, ServiceUnauthorized, ServiceForbidden, or
    ServiceBadRequest on failure.
    """
    # ── Fetch restaurant ─────────────────────────────────────────────────────
    restaurant = db.execute(
        select(Restaurant).where(Restaurant.id == restaurant_id)
    ).scalar_one_or_none()

    if restaurant is None:
        raise ServiceNotFound(f"Restaurant {restaurant_id} not found.")

    # ── Resolve uploader identity ─────────────────────────────────────────────
    token_type: str = token_payload.get("token_type", "")
    subject: str = token_payload.get("sub", "")
    uploader_user_id: Optional[int] = None
    uploader_owner_id: Optional[int] = None

    if token_type == "user":
        try:
            uid = int(subject)
        except (TypeError, ValueError):
            raise ServiceUnauthorized("Invalid token subject.")
        u = db.execute(select(User).where(User.id == uid)).scalar_one_or_none()
        if u is None:
            raise ServiceUnauthorized("Invalid token.")
        if restaurant.created_by_user_id != u.id:
            raise ServiceForbidden("You are not the creator of this restaurant.")
        uploader_user_id = u.id

    elif token_type == "owner":
        try:
            oid = int(subject)
        except (TypeError, ValueError):
            raise ServiceUnauthorized("Invalid token subject.")
        o = db.execute(select(Owner).where(Owner.id == oid)).scalar_one_or_none()
        if o is None:
            raise ServiceUnauthorized("Invalid token.")
        if restaurant.claimed_by_owner_id != o.id:
            raise ServiceForbidden("You are not the claimed owner of this restaurant.")
        uploader_owner_id = o.id

    else:
        raise ServiceUnauthorized("Invalid token type.")

    # ── Validate file count ───────────────────────────────────────────────────
    if len(files) == 0:
        raise ServiceBadRequest("No files provided.")
    if len(files) > _MAX_PHOTOS_TOTAL:
        raise ServiceBadRequest(
            f"You may upload at most {_MAX_PHOTOS_TOTAL} photos at once."
        )

    existing_count: int = db.execute(
        select(func.count()).where(RestaurantPhoto.restaurant_id == restaurant_id)
    ).scalar_one()

    if existing_count + len(files) > _MAX_PHOTOS_TOTAL:
        remaining = _MAX_PHOTOS_TOTAL - existing_count
        raise ServiceBadRequest(
            f"Restaurant already has {existing_count} photo(s). "
            f"You can add at most {remaining} more."
        )

    # ── Validate and persist each file ───────────────────────────────────────
    saved: list[PhotoResponse] = []

    for f in files:
        if not f.filename:
            raise ServiceBadRequest("Empty filename.")

        ext = f".{f.filename.rsplit('.', 1)[-1].lower()}" if "." in f.filename else ""
        if ext not in _ALLOWED_EXTENSIONS:
            raise ServiceBadRequest(
                f"Unsupported format '{ext}'. Use JPEG, PNG, or WEBP."
            )
        if f.content_type not in _ALLOWED_MIME_TYPES:
            raise ServiceBadRequest("Only JPEG, PNG, and WEBP images are accepted.")

        data = await f.read()
        if len(data) > _MAX_PHOTO_BYTES:
            raise ServiceBadRequest("Each image must be 10 MB or less.")

        filename = f"restaurant-{restaurant_id}-{uuid.uuid4().hex}{ext}"
        (_photos_dir / filename).write_bytes(data)

        photo = RestaurantPhoto(
            restaurant_id=restaurant_id,
            photo_url=_build_photo_url(base_url, filename),
            uploaded_by_user_id=uploader_user_id,
            uploaded_by_owner_id=uploader_owner_id,
        )
        db.add(photo)
        db.flush()   # populate photo.id before commit
        saved.append(
            PhotoResponse(
                id=photo.id,
                photo_url=photo.photo_url,
                uploaded_by_user_id=photo.uploaded_by_user_id,
                uploaded_by_owner_id=photo.uploaded_by_owner_id,
                created_at=photo.created_at,
            )
        )

    db.commit()
    return saved
