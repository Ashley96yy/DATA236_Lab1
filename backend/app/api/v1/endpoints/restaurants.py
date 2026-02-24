"""
Phase 3 — Restaurant endpoints (thin controllers).

All DB access and business rules live in app/services/restaurant_service.py.

POST   /api/v1/restaurants              create (User JWT)
GET    /api/v1/restaurants              search + filter + pagination (public)
GET    /api/v1/restaurants/{id}         details (public)
POST   /api/v1/restaurants/{id}/photos  upload photos (User OR Owner JWT)
"""
from __future__ import annotations

from typing import Annotated, Optional

import jwt as pyjwt
from fastapi import (
    APIRouter,
    Depends,
    File,
    HTTPException,
    Query,
    Request,
    UploadFile,
    status,
)
from sqlalchemy.orm import Session

from app.api.deps import get_current_user
from app.core.security import decode_access_token
from app.db.session import get_db
from app.models.user import User
from app.schemas.restaurant import (
    RestaurantCreate,
    RestaurantResponse,
    RestaurantSearchResponse,
)
from app.services import restaurant_service
from app.services.errors import (
    ServiceBadRequest,
    ServiceForbidden,
    ServiceNotFound,
    ServiceUnauthorized,
)

router = APIRouter(prefix="/restaurants", tags=["restaurants"])


# ---------------------------------------------------------------------------
# 1. POST /api/v1/restaurants  — Create (User JWT required)
# ---------------------------------------------------------------------------

@router.post(
    "",
    response_model=RestaurantResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Create a restaurant listing",
)
def create_restaurant(
    payload: RestaurantCreate,
    db: Annotated[Session, Depends(get_db)],
    current_user: Annotated[User, Depends(get_current_user)],
) -> RestaurantResponse:
    return restaurant_service.create_restaurant(db, payload, current_user.id)


# ---------------------------------------------------------------------------
# 2. GET /api/v1/restaurants   — Search / filter / paginate (public)
# ---------------------------------------------------------------------------

@router.get(
    "",
    response_model=RestaurantSearchResponse,
    summary="Search and filter restaurants",
)
def search_restaurants(
    db: Annotated[Session, Depends(get_db)],
    name: Optional[str] = Query(default=None, description="Filter by name (partial match)"),
    cuisine: Optional[str] = Query(default=None, description="Filter by cuisine type"),
    keywords: Optional[str] = Query(
        default=None,
        description="Match name OR description OR amenities JSON",
    ),
    city: Optional[str] = Query(default=None, description="Filter by city (partial match)"),
    zip: Optional[str] = Query(default=None, description="Filter by exact zip code"),
    sort: Optional[str] = Query(
        default="name",
        description="Sort order: rating | review_count | name",
        pattern="^(rating|review_count|name)$",
    ),
    page: int = Query(default=1, ge=1),
    limit: int = Query(default=10, ge=1, le=50),
) -> RestaurantSearchResponse:
    return restaurant_service.search_restaurants(
        db,
        name=name,
        cuisine=cuisine,
        keywords=keywords,
        city=city,
        zip_code=zip,
        sort=sort,
        page=page,
        limit=limit,
    )


# ---------------------------------------------------------------------------
# 3. GET /api/v1/restaurants/{id}  — Details (public)
# ---------------------------------------------------------------------------

@router.get(
    "/{restaurant_id}",
    response_model=RestaurantResponse,
    summary="Get restaurant details",
)
def get_restaurant(
    restaurant_id: int,
    db: Annotated[Session, Depends(get_db)],
) -> RestaurantResponse:
    try:
        return restaurant_service.get_restaurant_by_id(db, restaurant_id)
    except ServiceNotFound as exc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(exc))


# ---------------------------------------------------------------------------
# 4. POST /api/v1/restaurants/{id}/photos  — Upload photos (User OR Owner)
# ---------------------------------------------------------------------------

@router.post(
    "/{restaurant_id}/photos",
    status_code=status.HTTP_201_CREATED,
    summary="Upload photos for a restaurant (owner or creator)",
)
async def upload_restaurant_photos(
    restaurant_id: int,
    request: Request,
    db: Annotated[Session, Depends(get_db)],
    files: list[UploadFile] = File(..., description="Up to 5 image files"),
) -> dict:
    # ── Decode JWT (HTTP-layer concern; stays in endpoint) ───────────────────
    auth_header = request.headers.get("Authorization", "")
    if not auth_header.startswith("Bearer "):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Not authenticated.",
            headers={"WWW-Authenticate": "Bearer"},
        )
    raw_token = auth_header[7:]
    try:
        token_payload = decode_access_token(raw_token)
    except pyjwt.PyJWTError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid or expired token.",
        )

    # ── Delegate to service ──────────────────────────────────────────────────
    try:
        photos = await restaurant_service.upload_photos(
            db,
            restaurant_id,
            files,
            token_payload,
            str(request.base_url),
        )
    except ServiceNotFound as exc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(exc))
    except ServiceUnauthorized as exc:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail=str(exc))
    except ServiceForbidden as exc:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail=str(exc))
    except ServiceBadRequest as exc:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(exc))

    return {"photos": [{"id": p.id, "photo_url": p.photo_url} for p in photos]}
