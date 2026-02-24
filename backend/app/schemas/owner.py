"""
Pydantic schemas for Phase 6 owner-management endpoints.
"""
from __future__ import annotations

from typing import Literal, Optional

from pydantic import BaseModel, ConfigDict, Field

from app.schemas.restaurant import RestaurantCard

PricingTier = Literal["$", "$$", "$$$", "$$$$"]


# ---------------------------------------------------------------------------
# Owner profile update
# ---------------------------------------------------------------------------

class OwnerProfileUpdate(BaseModel):
    """PUT /owners/me — all fields optional; only provided fields are updated."""
    name: Optional[str] = Field(default=None, min_length=1, max_length=100)
    restaurant_location: Optional[str] = Field(default=None, min_length=1, max_length=255)


class OwnerProfileResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    name: str
    email: str
    restaurant_location: str


# ---------------------------------------------------------------------------
# Owner restaurant management
# ---------------------------------------------------------------------------

class OwnerRestaurantUpdate(BaseModel):
    """
    PUT /owner/restaurants/{id} — partial update.
    Only fields provided (non-None) are written to the DB.
    """
    name: Optional[str] = Field(default=None, min_length=1, max_length=200)
    cuisine_type: Optional[str] = Field(default=None, max_length=100)
    description: Optional[str] = None

    street: Optional[str] = Field(default=None, max_length=255)
    city: Optional[str] = Field(default=None, min_length=1, max_length=100)
    state: Optional[str] = Field(default=None, max_length=50)
    zip_code: Optional[str] = Field(default=None, max_length=20)
    country: Optional[str] = Field(default=None, max_length=100)

    latitude: Optional[float] = None
    longitude: Optional[float] = None

    phone: Optional[str] = Field(default=None, max_length=30)
    email: Optional[str] = Field(default=None, max_length=255)

    hours_json: Optional[dict] = None
    pricing_tier: Optional[PricingTier] = None
    amenities: Optional[list[str]] = None


class ClaimResponse(BaseModel):
    """Response for POST /owner/restaurants/{id}/claim."""
    restaurant_id: int
    claimed_by_owner_id: int
    message: str = "Restaurant claimed successfully."


# ---------------------------------------------------------------------------
# Owner dashboard
# ---------------------------------------------------------------------------

class OwnerDashboardResponse(BaseModel):
    """Response for GET /owner/dashboard."""
    claimed_count: int
    total_reviews: int
    avg_rating: float
    # {1: count, 2: count, 3: count, 4: count, 5: count}
    rating_distribution: dict[int, int]
    claimed_restaurants: list[RestaurantCard]
