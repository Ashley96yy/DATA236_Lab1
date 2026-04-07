from __future__ import annotations

from datetime import datetime, timezone
from typing import Literal
from uuid import uuid4

from pydantic import BaseModel, Field


ReviewEventType = Literal["review.created", "review.updated", "review.deleted"]


class ReviewEvent(BaseModel):
    event_id: str = Field(default_factory=lambda: str(uuid4()))
    event_type: ReviewEventType
    restaurant_id: int
    user_id: int
    rating: int | None = None
    comment: str | None = None
    review_id: int | None = None
    timestamp: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))


def build_review_event(
    *,
    event_type: ReviewEventType,
    restaurant_id: int,
    user_id: int,
    rating: int | None = None,
    comment: str | None = None,
    review_id: int | None = None,
) -> ReviewEvent:
    return ReviewEvent(
        event_type=event_type,
        restaurant_id=restaurant_id,
        user_id=user_id,
        rating=rating,
        comment=comment,
        review_id=review_id,
    )
