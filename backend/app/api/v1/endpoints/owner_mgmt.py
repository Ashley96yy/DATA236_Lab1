"""
Phase 6 — Owner restaurant-management endpoints (thin controllers).

All DB access and business rules live in app/services/owner_service.py.

POST   /api/v1/owner/restaurants                  create restaurant (Owner JWT)
PUT    /api/v1/owner/restaurants/{id}             update claimed restaurant (Owner JWT)
POST   /api/v1/owner/restaurants/{id}/claim       claim restaurant (Owner JWT)
GET    /api/v1/owner/restaurants/{id}/reviews     list reviews (Owner JWT)
GET    /api/v1/owner/dashboard                    aggregate stats (Owner JWT)
"""
from __future__ import annotations

from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session

from app.api.deps import get_current_owner
from app.db.session import get_db
from app.models.owner import Owner
from app.schemas.owner import (
    ClaimResponse,
    OwnerDashboardResponse,
    OwnerRestaurantUpdate,
)
from app.schemas.restaurant import RestaurantCreate, RestaurantResponse
from app.services import owner_service
from app.services.errors import (
    ServiceConflict,
    ServiceForbidden,
    ServiceNotFound,
)

router = APIRouter(prefix="/owner", tags=["owner-management"])


# ---------------------------------------------------------------------------
# POST /api/v1/owner/restaurants  — Create restaurant
# ---------------------------------------------------------------------------

@router.post(
    "/restaurants",
    response_model=RestaurantResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Create a restaurant claimed by this owner",
)
def create_restaurant(
    payload: RestaurantCreate,
    db: Annotated[Session, Depends(get_db)],
    current_owner: Annotated[Owner, Depends(get_current_owner)],
) -> RestaurantResponse:
    return owner_service.create_owner_restaurant(db, payload, current_owner.id)


# ---------------------------------------------------------------------------
# PUT /api/v1/owner/restaurants/{restaurant_id}  — Update claimed restaurant
# ---------------------------------------------------------------------------

@router.put(
    "/restaurants/{restaurant_id}",
    response_model=RestaurantResponse,
    summary="Update a restaurant you have claimed",
)
def update_restaurant(
    restaurant_id: int,
    payload: OwnerRestaurantUpdate,
    db: Annotated[Session, Depends(get_db)],
    current_owner: Annotated[Owner, Depends(get_current_owner)],
) -> RestaurantResponse:
    try:
        return owner_service.update_owner_restaurant(db, restaurant_id, payload, current_owner.id)
    except ServiceNotFound as exc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(exc))
    except ServiceForbidden as exc:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail=str(exc))


# ---------------------------------------------------------------------------
# POST /api/v1/owner/restaurants/{restaurant_id}/claim  — Claim restaurant
# ---------------------------------------------------------------------------

@router.post(
    "/restaurants/{restaurant_id}/claim",
    response_model=ClaimResponse,
    status_code=status.HTTP_200_OK,
    summary="Claim an unclaimed restaurant",
)
def claim_restaurant(
    restaurant_id: int,
    db: Annotated[Session, Depends(get_db)],
    current_owner: Annotated[Owner, Depends(get_current_owner)],
) -> ClaimResponse:
    try:
        return owner_service.claim_restaurant(db, restaurant_id, current_owner.id)
    except ServiceNotFound as exc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(exc))
    except ServiceConflict as exc:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail=str(exc))


# ---------------------------------------------------------------------------
# GET /api/v1/owner/restaurants/{restaurant_id}/reviews  — Read reviews
# ---------------------------------------------------------------------------

@router.get(
    "/restaurants/{restaurant_id}/reviews",
    summary="List reviews for a restaurant you have claimed",
)
def list_restaurant_reviews(
    restaurant_id: int,
    db: Annotated[Session, Depends(get_db)],
    current_owner: Annotated[Owner, Depends(get_current_owner)],
    page: int = Query(default=1, ge=1),
    limit: int = Query(default=20, ge=1, le=100),
) -> dict:
    try:
        return owner_service.get_owner_restaurant_reviews(
            db, restaurant_id, current_owner.id, page=page, limit=limit
        )
    except ServiceNotFound as exc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(exc))
    except ServiceForbidden as exc:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail=str(exc))


# ---------------------------------------------------------------------------
# GET /api/v1/owner/dashboard  — Aggregate stats
# ---------------------------------------------------------------------------

@router.get(
    "/dashboard",
    response_model=OwnerDashboardResponse,
    summary="Aggregate stats for all your claimed restaurants",
)
def owner_dashboard(
    db: Annotated[Session, Depends(get_db)],
    current_owner: Annotated[Owner, Depends(get_current_owner)],
) -> OwnerDashboardResponse:
    return owner_service.get_owner_dashboard(db, current_owner.id)
