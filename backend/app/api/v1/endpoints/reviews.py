"""
Phase 4 — Review endpoints (thin controllers).

All DB access and business rules live in app/services/review_service.py.

POST   /api/v1/restaurants/{id}/reviews   create (User JWT)
GET    /api/v1/restaurants/{id}/reviews   list, paginated (public)
PUT    /api/v1/reviews/{id}               edit own review (User JWT)
DELETE /api/v1/reviews/{id}               delete own review (User JWT)
"""
from __future__ import annotations

from typing import Annotated, List

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session

from app.api.deps import get_current_user
from app.db.session import get_db
from app.models.user import User
from app.schemas.review import ReviewCreate, ReviewResponse, ReviewUpdate
from app.services import review_service
from app.services.errors import (
    ServiceConflict,
    ServiceForbidden,
    ServiceNotFound,
)

router = APIRouter(tags=["reviews"])


# ---------------------------------------------------------------------------
# POST /api/v1/restaurants/{restaurant_id}/reviews  — Create
# ---------------------------------------------------------------------------

@router.post(
    "/restaurants/{restaurant_id}/reviews",
    response_model=ReviewResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Submit a review for a restaurant",
)
def create_review(
    restaurant_id: int,
    payload: ReviewCreate,
    db: Annotated[Session, Depends(get_db)],
    current_user: Annotated[User, Depends(get_current_user)],
) -> ReviewResponse:
    try:
        return review_service.create_review(db, restaurant_id, payload, current_user.id)
    except ServiceConflict as exc:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail=str(exc))


# ---------------------------------------------------------------------------
# GET /api/v1/restaurants/{restaurant_id}/reviews  — List (public)
# ---------------------------------------------------------------------------

@router.get(
    "/restaurants/{restaurant_id}/reviews",
    summary="List reviews for a restaurant",
)
def list_reviews(
    restaurant_id: int,
    db: Annotated[Session, Depends(get_db)],
    page: int = Query(default=1, ge=1),
    limit: int = Query(default=20, ge=1, le=100),
) -> dict:
    return review_service.get_reviews_for_restaurant(db, restaurant_id, page=page, limit=limit)


# ---------------------------------------------------------------------------
# PUT /api/v1/reviews/{review_id}  — Edit own review
# ---------------------------------------------------------------------------

@router.put(
    "/reviews/{review_id}",
    response_model=ReviewResponse,
    summary="Edit your own review",
)
def update_review(
    review_id: int,
    payload: ReviewUpdate,
    db: Annotated[Session, Depends(get_db)],
    current_user: Annotated[User, Depends(get_current_user)],
) -> ReviewResponse:
    try:
        return review_service.update_review(db, review_id, payload, current_user.id)
    except ServiceNotFound as exc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(exc))
    except ServiceForbidden as exc:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail=str(exc))


# ---------------------------------------------------------------------------
# DELETE /api/v1/reviews/{review_id}  — Delete own review
# ---------------------------------------------------------------------------

@router.delete(
    "/reviews/{review_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Delete your own review",
)
def delete_review(
    review_id: int,
    db: Annotated[Session, Depends(get_db)],
    current_user: Annotated[User, Depends(get_current_user)],
) -> None:
    try:
        review_service.delete_review(db, review_id, current_user.id)
    except ServiceNotFound as exc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(exc))
    except ServiceForbidden as exc:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail=str(exc))
