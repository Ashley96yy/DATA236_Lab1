"""
Pydantic schemas for Phase 3 restaurant endpoints.

Stubs only — validation logic and optional/required rules will be
finalised after model/schema approval.
"""
from __future__ import annotations

from datetime import datetime
from typing import Literal, Optional

from pydantic import BaseModel, ConfigDict, Field

PricingTier = Literal["$", "$$", "$$$", "$$$$"]


# ---------------------------------------------------------------------------
# Shared / nested
# ---------------------------------------------------------------------------

class PhotoResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    photo_url: str
    uploaded_by_user_id: Optional[int] = None
    uploaded_by_owner_id: Optional[int] = None
    created_at: datetime


# ---------------------------------------------------------------------------
# Create
# ---------------------------------------------------------------------------

class RestaurantCreate(BaseModel):
    name: str = Field(min_length=1, max_length=200)
    cuisine_type: Optional[str] = Field(default=None, max_length=100)
    description: Optional[str] = None

    # Address
    street: Optional[str] = Field(default=None, max_length=255)
    city: str = Field(min_length=1, max_length=100)
    state: Optional[str] = Field(default=None, max_length=50)
    zip_code: Optional[str] = Field(default=None, max_length=20)
    country: Optional[str] = Field(default=None, max_length=100)

    # Contact
    phone: Optional[str] = Field(default=None, max_length=30)
    email: Optional[str] = Field(default=None, max_length=255)

    # Rich data
    hours_json: Optional[dict] = None         # e.g. {"Mon": "9am-10pm", ...}
    pricing_tier: Optional[PricingTier] = None
    amenities: Optional[list[str]] = None     # e.g. ["WiFi", "Parking"]


# ---------------------------------------------------------------------------
# Response (single restaurant detail)
# ---------------------------------------------------------------------------

class RestaurantResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    name: str
    cuisine_type: Optional[str] = None
    description: Optional[str] = None

    street: Optional[str] = None
    city: str
    state: Optional[str] = None
    zip_code: Optional[str] = None
    country: Optional[str] = None

    latitude: Optional[float] = None
    longitude: Optional[float] = None

    phone: Optional[str] = None
    email: Optional[str] = None

    hours_json: Optional[dict] = None
    pricing_tier: Optional[PricingTier] = None
    amenities: Optional[list[str]] = None

    created_by_user_id: Optional[int] = None
    claimed_by_owner_id: Optional[int] = None

    # Aggregated (computed in service, injected before response)
    avg_rating: Optional[float] = None
    review_count: int = 0

    photos: list[PhotoResponse] = []

    created_at: datetime
    updated_at: datetime


# ---------------------------------------------------------------------------
# Response (list / search card — lighter weight)
# ---------------------------------------------------------------------------

class RestaurantCard(BaseModel):
    """Minimal shape returned in search results list."""
    model_config = ConfigDict(from_attributes=True)

    id: int
    name: str
    cuisine_type: Optional[str] = None
    city: str
    pricing_tier: Optional[PricingTier] = None
    avg_rating: Optional[float] = None
    review_count: int = 0
    # First photo for card thumbnail (None if no photos)
    cover_photo_url: Optional[str] = None


class RestaurantSearchResponse(BaseModel):
    results: list[RestaurantCard]
    total: int
    page: int
    limit: int
