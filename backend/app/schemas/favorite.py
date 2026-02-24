"""
Pydantic schemas for Phase 5 favorites + history endpoints.
"""
from __future__ import annotations

from datetime import datetime
from typing import Optional

from pydantic import BaseModel, ConfigDict

from app.schemas.restaurant import RestaurantCard


# ---------------------------------------------------------------------------
# Favorites
# ---------------------------------------------------------------------------

class FavoriteStatusResponse(BaseModel):
    """Response body for POST /favorites/{restaurant_id}."""
    restaurant_id: int
    favorited: bool


class FavoritesListResponse(BaseModel):
    """Response body for GET /users/me/favorites."""
    items: list[RestaurantCard]
    total: int


# ---------------------------------------------------------------------------
# History
# ---------------------------------------------------------------------------

class ReviewHistoryItem(BaseModel):
    """A review the user wrote, enriched with the restaurant name."""
    model_config = ConfigDict(from_attributes=True)

    id: int
    restaurant_id: int
    restaurant_name: str
    rating: int
    comment: Optional[str] = None
    created_at: datetime
    updated_at: datetime


class UserHistoryResponse(BaseModel):
    """Response body for GET /users/me/history."""
    my_reviews: list[ReviewHistoryItem]
    my_restaurants_added: list[RestaurantCard]
