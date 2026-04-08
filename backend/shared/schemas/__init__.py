"""
Shared Pydantic schemas reused across services.
Services import from here to avoid duplication.
"""
from __future__ import annotations

from pydantic import BaseModel, Field


# --- Auth ---

class LoginRequest(BaseModel):
    email: str = Field(min_length=5, max_length=255)
    password: str = Field(min_length=1, max_length=72)


class TokenResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"


# --- Pagination ---

class PaginationMeta(BaseModel):
    total: int
    page: int
    limit: int


# --- Reviews (shared read schema) ---

class ReviewBase(BaseModel):
    rating: int = Field(..., ge=1, le=5)
    comment: str | None = None


class ReviewCreate(ReviewBase):
    pass


class ReviewUpdate(BaseModel):
    rating: int | None = Field(default=None, ge=1, le=5)
    comment: str | None = None
