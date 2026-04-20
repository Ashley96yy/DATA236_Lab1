from __future__ import annotations

from typing import Literal
from datetime import datetime

from pydantic import BaseModel, Field

GenderType = Literal["male", "female", "non_binary", "other", "prefer_not_to_say"]
PriceRangeType = Literal["$", "$$", "$$$", "$$$$"]
SortPreferenceType = Literal["rating", "distance", "popularity", "price"]


from shared.schemas import LoginRequest  # noqa: F401 — re-exported for service use


class SignupRequest(BaseModel):
    name: str = Field(min_length=1, max_length=100)
    email: str = Field(min_length=5, max_length=255)
    password: str = Field(min_length=8, max_length=72)


class UserResponse(BaseModel):
    id: int
    name: str
    email: str
    phone: str | None = None
    about_me: str | None = None
    city: str | None = None
    state: str | None = None
    country: str | None = None
    languages: str | list[str] | None = None
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


class UserProfileUpdateRequest(BaseModel):
    name: str | None = Field(default=None, min_length=1, max_length=100)
    phone: str | None = Field(default=None, max_length=30)
    about_me: str | None = None
    city: str | None = Field(default=None, max_length=100)
    state: str | None = Field(default=None, max_length=50)
    country: str | None = Field(default=None, min_length=2, max_length=2)
    languages: str | list[str] | None = None
    gender: GenderType | None = None


class AvatarUploadResponse(BaseModel):
    avatar_url: str


class FavoriteEntry(BaseModel):
    restaurant_id: int
    name: str
    cuisine_type: str | None = None
    city: str | None = None
    state: str | None = None
    pricing_tier: str | None = None
    average_rating: float = 0.0
    review_count: int = 0


class FavoritesListResponse(BaseModel):
    items: list[FavoriteEntry]
    total: int
    page: int
    limit: int


class HistoryReviewEntry(BaseModel):
    review_id: int
    restaurant_id: int
    restaurant_name: str
    rating: int
    comment: str | None = None
    created_at: datetime | None = None


class UserHistoryResponse(BaseModel):
    my_reviews: list[HistoryReviewEntry] = Field(default_factory=list)
    my_restaurants_added: list[FavoriteEntry] = Field(default_factory=list)


class ConversationTurn(BaseModel):
    role: Literal["user", "assistant"]
    content: str


class AiAssistantChatRequest(BaseModel):
    message: str = Field(min_length=1, max_length=2000)
    conversation_history: list[ConversationTurn] = Field(default_factory=list)


class AiSuggestedRestaurant(BaseModel):
    id: int | None = None
    name: str
    cuisine_type: str | None = None
    pricing_tier: str | None = None
    average_rating: float = 0.0
    reason: str
    external_url: str | None = None
    is_external: bool = False


class AiAssistantChatResponse(BaseModel):
    reply: str
    suggested_restaurants: list[AiSuggestedRestaurant] = Field(default_factory=list)
