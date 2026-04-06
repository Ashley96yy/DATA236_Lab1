from __future__ import annotations

from typing import Literal

from pydantic import BaseModel, Field

PricingTier = Literal["$", "$$", "$$$", "$$$$"]


class RestaurantCreate(BaseModel):
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
    hours: dict | None = None
    pricing_tier: PricingTier | None = None
    amenities: list[str] | None = None


class RestaurantPhotoResponse(BaseModel):
    id: int
    photo_url: str
    uploaded_by_user_id: int | None = None
    uploaded_by_owner_id: int | None = None


class RestaurantCard(BaseModel):
    id: int
    name: str
    cuisine_type: str | None = None
    description: str | None = None
    city: str
    state: str | None = None
    pricing_tier: str | None = None
    amenities: list[str] = Field(default_factory=list)
    average_rating: float = 0.0
    review_count: int = 0
    cover_photo_url: str | None = None


class RestaurantResponse(BaseModel):
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
    pricing_tier: str | None = None
    amenities: list[str] = Field(default_factory=list)
    created_by_user_id: int | None = None
    claimed_by_owner_id: int | None = None
    average_rating: float = 0.0
    review_count: int = 0
    photos: list[RestaurantPhotoResponse] = Field(default_factory=list)


class RestaurantSearchResponse(BaseModel):
    items: list[RestaurantCard]
    total: int
    page: int
    limit: int
