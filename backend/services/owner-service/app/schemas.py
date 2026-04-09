from __future__ import annotations

from datetime import datetime

from pydantic import BaseModel, Field


from shared.schemas import LoginRequest  # noqa: F401 — re-exported for service use


class OwnerSignupRequest(BaseModel):
    name: str = Field(min_length=1, max_length=100)
    email: str = Field(min_length=5, max_length=255)
    password: str = Field(min_length=8, max_length=72)
    restaurant_location: str = Field(min_length=1, max_length=255)


class OwnerResponse(BaseModel):
    id: int
    name: str
    email: str
    restaurant_location: str


class OwnerProfileUpdateRequest(BaseModel):
    name: str | None = Field(default=None, min_length=1, max_length=100)
    restaurant_location: str | None = Field(default=None, min_length=1, max_length=255)


class OwnerLoginResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"
    owner: OwnerResponse


class ClaimedRestaurantCard(BaseModel):
    id: int
    name: str
    cuisine_type: str | None = None
    city: str | None = None
    state: str | None = None
    pricing_tier: str | None = None
    avg_rating: float = 0.0
    review_count: int = 0


class OwnerDashboardResponse(BaseModel):
    claimed_count: int
    total_reviews: int
    avg_rating: float
    rating_distribution: dict[int, int]
    claimed_restaurants: list[ClaimedRestaurantCard] = Field(default_factory=list)


class ClaimRestaurantResponse(BaseModel):
    restaurant_id: int
    claimed_by_owner_id: int
    status: str = "claimed"


class OwnerRestaurantCreateRequest(BaseModel):
    name: str = Field(min_length=1, max_length=200)
    cuisine_type: str | None = Field(default=None, max_length=100)
    description: str | None = None
    street: str | None = Field(default=None, max_length=255)
    city: str = Field(min_length=1, max_length=100)
    state: str | None = Field(default=None, max_length=50)
    zip_code: str | None = Field(default=None, max_length=20)
    country: str | None = Field(default=None, max_length=100)
    latitude: float | None = None
    longitude: float | None = None
    phone: str | None = Field(default=None, max_length=30)
    email: str | None = Field(default=None, max_length=255)
    pricing_tier: str | None = None
    amenities: list[str] | None = None
    hours_json: dict | None = None
    hours: dict | None = None


class OwnerRestaurantUpdateRequest(BaseModel):
    name: str | None = Field(default=None, min_length=1, max_length=200)
    cuisine_type: str | None = Field(default=None, max_length=100)
    description: str | None = None
    street: str | None = Field(default=None, max_length=255)
    city: str | None = Field(default=None, min_length=1, max_length=100)
    state: str | None = Field(default=None, max_length=50)
    zip_code: str | None = Field(default=None, max_length=20)
    country: str | None = Field(default=None, max_length=100)
    latitude: float | None = None
    longitude: float | None = None
    phone: str | None = Field(default=None, max_length=30)
    email: str | None = Field(default=None, max_length=255)
    pricing_tier: str | None = None
    amenities: list[str] | None = None
    hours_json: dict | None = None
    hours: dict | None = None


class OwnerRestaurantResponse(BaseModel):
    id: int
    name: str
    cuisine_type: str | None = None
    description: str | None = None
    street: str | None = None
    city: str
    state: str | None = None
    zip_code: str | None = None
    country: str | None = None
    latitude: float | None = None
    longitude: float | None = None
    phone: str | None = None
    email: str | None = None
    hours: dict | None = None
    hours_json: dict | None = None
    pricing_tier: str | None = None
    amenities: list[str] = Field(default_factory=list)
    created_by_user_id: int | None = None
    claimed_by_owner_id: int | None = None


class OwnerRestaurantReviewResponse(BaseModel):
    id: int
    restaurant_id: int
    user_id: int
    user_name: str
    rating: int
    comment: str | None = None
    status: str = "processed"
    created_at: datetime
    updated_at: datetime


class OwnerRestaurantReviewListResponse(BaseModel):
    items: list[OwnerRestaurantReviewResponse] = Field(default_factory=list)
    total: int
    page: int
    limit: int
