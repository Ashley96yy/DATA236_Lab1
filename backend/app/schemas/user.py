from typing import Literal, Optional

from pydantic import BaseModel, Field

GenderType = Literal["male", "female", "non_binary", "other", "prefer_not_to_say"]
PriceRangeType = Literal["$", "$$", "$$$", "$$$$"]
SortPreferenceType = Literal["rating", "distance", "popularity", "price"]


class UserProfileResponse(BaseModel):
    id: int
    name: str
    email: str
    phone: Optional[str] = None
    about_me: Optional[str] = None
    city: Optional[str] = None
    state: Optional[str] = None
    country: Optional[str] = None
    languages: Optional[str] = None
    gender: Optional[GenderType] = None
    avatar_url: Optional[str] = None


class UserProfileUpdateRequest(BaseModel):
    name: Optional[str] = Field(default=None, min_length=1, max_length=100)
    phone: Optional[str] = Field(default=None, max_length=30)
    about_me: Optional[str] = None
    city: Optional[str] = Field(default=None, max_length=100)
    state: Optional[str] = Field(default=None, max_length=10)
    country: Optional[str] = Field(default=None, min_length=2, max_length=2)
    languages: Optional[str] = None
    gender: Optional[GenderType] = None


class UserPreferencesResponse(BaseModel):
    cuisines: list[str] = Field(default_factory=list)
    price_range: Optional[PriceRangeType] = None
    preferred_locations: list[str] = Field(default_factory=list)
    search_radius_km: Optional[int] = Field(default=None, ge=0)
    dietary_needs: list[str] = Field(default_factory=list)
    ambiance: list[str] = Field(default_factory=list)
    sort_preference: SortPreferenceType = "rating"


class UserPreferencesUpdateRequest(BaseModel):
    cuisines: Optional[list[str]] = None
    price_range: Optional[PriceRangeType] = None
    preferred_locations: Optional[list[str]] = None
    search_radius_km: Optional[int] = Field(default=None, ge=0)
    dietary_needs: Optional[list[str]] = None
    ambiance: Optional[list[str]] = None
    sort_preference: Optional[SortPreferenceType] = None


class AvatarUploadResponse(BaseModel):
    avatar_url: str
