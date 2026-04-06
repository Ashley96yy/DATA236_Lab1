from __future__ import annotations

from typing import Literal

from pydantic import BaseModel, Field

GenderType = Literal["male", "female", "non_binary", "other", "prefer_not_to_say"]
PriceRangeType = Literal["$", "$$", "$$$", "$$$$"]
SortPreferenceType = Literal["rating", "distance", "popularity", "price"]


class SignupRequest(BaseModel):
    name: str = Field(min_length=1, max_length=100)
    email: str = Field(min_length=5, max_length=255)
    password: str = Field(min_length=8, max_length=72)


class LoginRequest(BaseModel):
    email: str = Field(min_length=5, max_length=255)
    password: str = Field(min_length=1, max_length=72)


class UserResponse(BaseModel):
    id: int
    name: str
    email: str
    phone: str | None = None
    about_me: str | None = None
    city: str | None = None
    state: str | None = None
    country: str | None = None
    languages: list[str] = Field(default_factory=list)
    gender: GenderType | None = None
    avatar_url: str | None = None


class LoginResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"
    user: UserResponse


class UserPreferencesResponse(BaseModel):
    cuisines: list[str] = Field(default_factory=list)
    price_range: PriceRangeType | None = None
    preferred_locations: list[str] = Field(default_factory=list)
    search_radius_km: int | None = None
    dietary_needs: list[str] = Field(default_factory=list)
    ambiance: list[str] = Field(default_factory=list)
    sort_preference: SortPreferenceType = "rating"


class UserPreferencesUpdateRequest(BaseModel):
    cuisines: list[str] | None = None
    price_range: PriceRangeType | None = None
    preferred_locations: list[str] | None = None
    search_radius_km: int | None = Field(default=None, ge=0)
    dietary_needs: list[str] | None = None
    ambiance: list[str] | None = None
    sort_preference: SortPreferenceType | None = None
