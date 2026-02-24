"""
Favorites + History endpoints — Phase 5.

Routes:
    POST   /favorites/{restaurant_id}   → add favorite          (User JWT, 201)
    DELETE /favorites/{restaurant_id}   → remove favorite        (User JWT, 204)
    GET    /users/me/favorites          → list favorited restaurants (User JWT, 200)
    GET    /users/me/history            → my reviews + restaurants added (User JWT, 200)

Design notes:
    - All DB/business logic lives in favorite_service (service-layer rule).
    - DELETE returns 404 if the favorite does not exist.
    - GET /users/me/favorites supports optional ?page=&limit= pagination.
"""
from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session

from app.api.deps import get_current_user
from app.db.session import get_db
from app.models.user import User
from app.schemas.favorite import (
    FavoriteStatusResponse,
    FavoritesListResponse,
    UserHistoryResponse,
)
from app.services import favorite_service
from app.services.errors import ServiceConflict, ServiceNotFound

router = APIRouter(tags=["favorites"])


@router.post(
    "/favorites/{restaurant_id}",
    response_model=FavoriteStatusResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Add a restaurant to favorites",
)
def add_favorite(
    restaurant_id: int,
    db: Annotated[Session, Depends(get_db)],
    current_user: Annotated[User, Depends(get_current_user)],
) -> FavoriteStatusResponse:
    try:
        return favorite_service.add_favorite(db, restaurant_id, current_user.id)
    except ServiceNotFound as exc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(exc))
    except ServiceConflict as exc:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail=str(exc))


@router.delete(
    "/favorites/{restaurant_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Remove a restaurant from favorites",
)
def remove_favorite(
    restaurant_id: int,
    db: Annotated[Session, Depends(get_db)],
    current_user: Annotated[User, Depends(get_current_user)],
) -> None:
    """Returns 404 if the restaurant is not currently in the user's favorites."""
    try:
        favorite_service.remove_favorite(db, restaurant_id, current_user.id)
    except ServiceNotFound as exc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(exc))


@router.get(
    "/users/me/favorites",
    response_model=FavoritesListResponse,
    summary="List my favorite restaurants",
)
def list_favorites(
    db: Annotated[Session, Depends(get_db)],
    current_user: Annotated[User, Depends(get_current_user)],
    page: int = Query(default=1, ge=1),
    limit: int = Query(default=20, ge=1, le=100),
) -> FavoritesListResponse:
    return favorite_service.get_favorites(db, current_user.id, page=page, limit=limit)


@router.get(
    "/users/me/history",
    response_model=UserHistoryResponse,
    summary="My activity history (reviews written + restaurants added)",
)
def get_history(
    db: Annotated[Session, Depends(get_db)],
    current_user: Annotated[User, Depends(get_current_user)],
) -> UserHistoryResponse:
    return favorite_service.get_user_history(db, current_user.id)
