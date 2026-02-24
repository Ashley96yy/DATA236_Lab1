"""Pydantic schemas for the reviews endpoints (Phase 4)."""
from __future__ import annotations

from datetime import datetime
from typing import Optional

from pydantic import BaseModel, ConfigDict, Field


class ReviewCreate(BaseModel):
    rating: int = Field(..., ge=1, le=5, description="Star rating 1–5")
    comment: Optional[str] = Field(default=None, description="Review text (optional)")


class ReviewUpdate(BaseModel):
    rating: Optional[int] = Field(default=None, ge=1, le=5)
    comment: Optional[str] = Field(default=None)


class ReviewResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    restaurant_id: int
    rating: int
    comment: Optional[str]
    # joined from users table — do not expose user_id directly
    user_name: str
    created_at: datetime
    updated_at: datetime
