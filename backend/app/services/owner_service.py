"""
Owner service — all DB access and business rules for Phase 6.

Functions:
    update_owner_profile       — partial update of owner name / location
    create_owner_restaurant    — create a restaurant claimed by this owner
    update_owner_restaurant    — partial update; owner must have claimed it
    claim_restaurant           — claim an unclaimed restaurant; 409 if taken
    get_owner_restaurant_reviews — paginated reviews; owner must have claimed restaurant
    get_owner_dashboard        — aggregate stats + rating distribution
"""
from __future__ import annotations

from typing import Optional

from sqlalchemy import func, select
from sqlalchemy.orm import Session, selectinload

from app.models.owner import Owner
from app.models.restaurant import Restaurant
from app.models.review import Review
from app.models.user import User
from app.schemas.owner import (
    ClaimResponse,
    OwnerDashboardResponse,
    OwnerProfileResponse,
    OwnerProfileUpdate,
    OwnerRestaurantUpdate,
)
from app.schemas.restaurant import RestaurantCreate, RestaurantResponse
from app.schemas.review import ReviewResponse
from app.services.errors import (
    ServiceConflict,
    ServiceForbidden,
    ServiceNotFound,
)
from app.services.restaurant_service import (
    _fetch_ratings,
    _orm_to_card,
    _orm_to_response,
)


# ---------------------------------------------------------------------------
# Update owner profile
# ---------------------------------------------------------------------------

def update_owner_profile(
    db: Session,
    owner: Owner,
    data: OwnerProfileUpdate,
) -> OwnerProfileResponse:
    """
    Partially update owner name and/or restaurant_location.
    Only fields explicitly provided (non-None) are written.
    """
    updates = data.model_dump(exclude_unset=True)
    for field, value in updates.items():
        setattr(owner, field, value)

    db.add(owner)
    db.commit()
    db.refresh(owner)
    return OwnerProfileResponse.model_validate(owner)


# ---------------------------------------------------------------------------
# Create a restaurant (directly claimed by owner)
# ---------------------------------------------------------------------------

def create_owner_restaurant(
    db: Session,
    data: RestaurantCreate,
    owner_id: int,
) -> RestaurantResponse:
    """
    Create a new restaurant and immediately claim it for this owner.
    created_by_user_id is left NULL (owner did not use a user account).
    """
    restaurant = Restaurant(
        name=data.name,
        cuisine_type=data.cuisine_type,
        description=data.description,
        street=data.street,
        city=data.city,
        state=data.state,
        zip_code=data.zip_code,
        country=data.country,
        latitude=data.latitude,
        longitude=data.longitude,
        phone=data.phone,
        email=data.email,
        hours_json=data.hours_json,
        pricing_tier=data.pricing_tier,
        amenities=data.amenities,
        claimed_by_owner_id=owner_id,
    )
    db.add(restaurant)
    db.commit()
    db.refresh(restaurant)
    restaurant.photos = []
    return _orm_to_response(restaurant, average_rating=0.0, review_count=0)


# ---------------------------------------------------------------------------
# Update a claimed restaurant (partial)
# ---------------------------------------------------------------------------

def update_owner_restaurant(
    db: Session,
    restaurant_id: int,
    data: OwnerRestaurantUpdate,
    owner_id: int,
) -> RestaurantResponse:
    """
    Partially update a restaurant the owner has claimed.
    Raises ServiceNotFound or ServiceForbidden.
    """
    restaurant = db.execute(
        select(Restaurant)
        .options(selectinload(Restaurant.photos))
        .where(Restaurant.id == restaurant_id)
    ).scalar_one_or_none()

    if restaurant is None:
        raise ServiceNotFound(f"Restaurant {restaurant_id} not found.")
    if restaurant.claimed_by_owner_id != owner_id:
        raise ServiceForbidden("You have not claimed this restaurant.")

    updates = data.model_dump(exclude_unset=True)
    for field, value in updates.items():
        setattr(restaurant, field, value)

    db.add(restaurant)
    db.commit()
    db.refresh(restaurant)

    ratings = _fetch_ratings(db, [restaurant_id])
    avg, cnt = ratings.get(restaurant_id, (0.0, 0))
    return _orm_to_response(restaurant, average_rating=avg, review_count=cnt)


# ---------------------------------------------------------------------------
# Claim an unclaimed restaurant
# ---------------------------------------------------------------------------

def claim_restaurant(
    db: Session,
    restaurant_id: int,
    owner_id: int,
) -> ClaimResponse:
    """
    Claim a restaurant for this owner.
    Raises ServiceNotFound if restaurant doesn't exist.
    Raises ServiceConflict if already claimed (by any owner).
    """
    restaurant = db.execute(
        select(Restaurant).where(Restaurant.id == restaurant_id)
    ).scalar_one_or_none()

    if restaurant is None:
        raise ServiceNotFound(f"Restaurant {restaurant_id} not found.")
    if restaurant.claimed_by_owner_id is not None:
        raise ServiceConflict("This restaurant has already been claimed.")

    restaurant.claimed_by_owner_id = owner_id
    db.add(restaurant)
    db.commit()

    return ClaimResponse(
        restaurant_id=restaurant_id,
        claimed_by_owner_id=owner_id,
    )


# ---------------------------------------------------------------------------
# Get reviews for an owned restaurant (read-only)
# ---------------------------------------------------------------------------

def get_owner_restaurant_reviews(
    db: Session,
    restaurant_id: int,
    owner_id: int,
    page: int = 1,
    limit: int = 20,
) -> dict:
    """
    Return paginated reviews for a restaurant the owner has claimed.
    Raises ServiceNotFound or ServiceForbidden.
    Response: {"items": [...], "total": int, "page": int, "limit": int}
    """
    restaurant = db.execute(
        select(Restaurant.id, Restaurant.claimed_by_owner_id)
        .where(Restaurant.id == restaurant_id)
    ).one_or_none()

    if restaurant is None:
        raise ServiceNotFound(f"Restaurant {restaurant_id} not found.")
    if restaurant.claimed_by_owner_id != owner_id:
        raise ServiceForbidden("You have not claimed this restaurant.")

    total: int = db.execute(
        select(func.count(Review.id)).where(Review.restaurant_id == restaurant_id)
    ).scalar_one()

    rows = db.execute(
        select(Review, User.name.label("user_name"))
        .join(User, User.id == Review.user_id)
        .where(Review.restaurant_id == restaurant_id)
        .order_by(Review.created_at.desc(), Review.id.desc())
        .offset((page - 1) * limit)
        .limit(limit)
    ).all()

    items = [
        ReviewResponse(
            id=row.Review.id,
            restaurant_id=row.Review.restaurant_id,
            rating=row.Review.rating,
            comment=row.Review.comment,
            user_name=row.user_name,
            created_at=row.Review.created_at,
            updated_at=row.Review.updated_at,
        )
        for row in rows
    ]
    return {"items": items, "total": total, "page": page, "limit": limit}


# ---------------------------------------------------------------------------
# Owner dashboard
# ---------------------------------------------------------------------------

def get_owner_dashboard(db: Session, owner_id: int) -> OwnerDashboardResponse:
    """
    Return aggregate stats for all restaurants claimed by this owner:
      claimed_count        — number of claimed restaurants
      total_reviews        — total reviews across all claimed restaurants
      avg_rating           — overall average (0.0 if no reviews)
      rating_distribution  — {1: n, 2: n, 3: n, 4: n, 5: n}
      claimed_restaurants  — list of RestaurantCard for each claimed restaurant
    """
    # Fetch all claimed restaurants with photos
    restaurants = db.execute(
        select(Restaurant)
        .options(selectinload(Restaurant.photos))
        .where(Restaurant.claimed_by_owner_id == owner_id)
        .order_by(Restaurant.created_at.desc())
    ).scalars().all()

    rids = [r.id for r in restaurants]

    # Aggregate stats across all claimed restaurants
    if rids:
        agg_row = db.execute(
            select(
                func.count(Review.id).label("total"),
                func.avg(Review.rating).label("avg"),
            ).where(Review.restaurant_id.in_(rids))
        ).one()

        dist_rows = db.execute(
            select(Review.rating, func.count(Review.id).label("cnt"))
            .where(Review.restaurant_id.in_(rids))
            .group_by(Review.rating)
        ).all()
    else:
        agg_row = type("Row", (), {"total": 0, "avg": None})()
        dist_rows = []

    total_reviews = int(agg_row.total or 0)
    avg_rating = round(float(agg_row.avg), 2) if agg_row.avg is not None else 0.0

    # Build full distribution (fill missing ratings with 0)
    rating_distribution: dict[int, int] = {1: 0, 2: 0, 3: 0, 4: 0, 5: 0}
    for row in dist_rows:
        rating_distribution[int(row.rating)] = int(row.cnt)

    ratings = _fetch_ratings(db, rids)
    claimed_restaurants = [
        _orm_to_card(r, *ratings.get(r.id, (0.0, 0))) for r in restaurants
    ]

    return OwnerDashboardResponse(
        claimed_count=len(restaurants),
        total_reviews=total_reviews,
        avg_rating=avg_rating,
        rating_distribution=rating_distribution,
        claimed_restaurants=claimed_restaurants,
    )
