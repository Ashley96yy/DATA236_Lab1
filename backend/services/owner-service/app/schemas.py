from __future__ import annotations

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
