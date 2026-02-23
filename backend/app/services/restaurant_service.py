"""
Restaurant service — all DB access and business rules for Phase 3.

Stubs only. Implementations will be added after model/schema approval.
"""
from __future__ import annotations

from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from sqlalchemy.orm import Session
    from app.models.restaurant import Restaurant
    from app.models.restaurant_photo import RestaurantPhoto


# ---------------------------------------------------------------------------
# Create
# ---------------------------------------------------------------------------

def create_restaurant(db: "Session", data, created_by_user_id: int) -> "Restaurant":
    """Validate and persist a new restaurant listing created by a user."""
    raise NotImplementedError


# ---------------------------------------------------------------------------
# Read / Search
# ---------------------------------------------------------------------------

def get_restaurant_by_id(db: "Session", restaurant_id: int) -> "Restaurant | None":
    """Return a single restaurant by PK, or None if not found."""
    raise NotImplementedError


def search_restaurants(
    db: "Session",
    *,
    name: str | None = None,
    cuisine: str | None = None,
    keywords: str | None = None,
    city: str | None = None,
    zip_code: str | None = None,
    sort: str = "rating",
    page: int = 1,
    limit: int = 20,
) -> tuple[list["Restaurant"], int]:
    """
    Return (results, total_count) matching the given filters.

    keywords matches against name, description, and the amenities JSON column.
    """
    raise NotImplementedError


# ---------------------------------------------------------------------------
# Photos
# ---------------------------------------------------------------------------

def add_photo(
    db: "Session",
    restaurant_id: int,
    photo_url: str,
    *,
    uploaded_by_user_id: int | None = None,
    uploaded_by_owner_id: int | None = None,
) -> "RestaurantPhoto":
    """
    Persist a new photo record.

    Exactly one of uploaded_by_user_id / uploaded_by_owner_id must be set.
    The caller (endpoint) is responsible for verifying ownership before calling this.
    """
    raise NotImplementedError


def get_photos_for_restaurant(
    db: "Session", restaurant_id: int
) -> list["RestaurantPhoto"]:
    """Return all photos for a restaurant ordered by created_at asc."""
    raise NotImplementedError
