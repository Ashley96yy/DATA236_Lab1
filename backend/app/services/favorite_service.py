"""
Favorite service — all DB access and business rules for Phase 5.

Functions:
    add_favorite       — favorite a restaurant (unique per user)
    remove_favorite    — unfavorite; raises ServiceNotFound if not favorited
    get_favorites      — paginated list of user's favorited restaurants
    get_user_history   — user's reviews + restaurants they added
"""
from __future__ import annotations

from sqlalchemy import func, select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session, selectinload

from app.models.favorite import Favorite
from app.models.restaurant import Restaurant
from app.models.review import Review
from app.schemas.favorite import (
    FavoriteStatusResponse,
    FavoritesListResponse,
    ReviewHistoryItem,
    UserHistoryResponse,
)
from app.schemas.restaurant import RestaurantCard
from app.services.errors import ServiceConflict, ServiceNotFound
from app.services.restaurant_service import _fetch_ratings, _orm_to_card


# ---------------------------------------------------------------------------
# Add favorite
# ---------------------------------------------------------------------------

def add_favorite(
    db: Session,
    restaurant_id: int,
    user_id: int,
) -> FavoriteStatusResponse:
    """
    Favorite a restaurant for the given user.
    Raises ServiceNotFound if the restaurant does not exist.
    Raises ServiceConflict if already favorited.
    Returns FavoriteStatusResponse(restaurant_id=..., favorited=True).
    """
    # Verify restaurant exists
    exists = db.execute(
        select(Restaurant.id).where(Restaurant.id == restaurant_id)
    ).scalar_one_or_none()
    if exists is None:
        raise ServiceNotFound(f"Restaurant {restaurant_id} not found.")

    # Check duplicate
    already = db.execute(
        select(Favorite).where(
            Favorite.user_id == user_id,
            Favorite.restaurant_id == restaurant_id,
        )
    ).scalar_one_or_none()
    if already is not None:
        raise ServiceConflict("Restaurant is already in your favorites.")

    fav = Favorite(user_id=user_id, restaurant_id=restaurant_id)
    db.add(fav)
    try:
        db.commit()
    except IntegrityError:
        db.rollback()
        raise ServiceConflict("Restaurant is already in your favorites.")

    return FavoriteStatusResponse(restaurant_id=restaurant_id, favorited=True)


# ---------------------------------------------------------------------------
# Remove favorite
# ---------------------------------------------------------------------------

def remove_favorite(
    db: Session,
    restaurant_id: int,
    user_id: int,
) -> None:
    """
    Unfavorite a restaurant.
    Raises ServiceNotFound if this restaurant is not in the user's favorites.
    """
    fav = db.execute(
        select(Favorite).where(
            Favorite.user_id == user_id,
            Favorite.restaurant_id == restaurant_id,
        )
    ).scalar_one_or_none()

    if fav is None:
        raise ServiceNotFound("This restaurant is not in your favorites.")

    db.delete(fav)
    db.commit()


# ---------------------------------------------------------------------------
# List favorites
# ---------------------------------------------------------------------------

def get_favorites(
    db: Session,
    user_id: int,
    page: int = 1,
    limit: int = 20,
) -> FavoritesListResponse:
    """
    Return paginated RestaurantCard list for restaurants the user has favorited,
    ordered by most recently favorited first.
    """
    # Get favorited restaurant IDs (paginated, newest first)
    fav_stmt = (
        select(Favorite.restaurant_id)
        .where(Favorite.user_id == user_id)
        .order_by(Favorite.created_at.desc(), Favorite.id.desc())
    )

    total: int = db.execute(
        select(func.count()).select_from(fav_stmt.subquery())
    ).scalar_one()

    fav_ids = db.execute(
        fav_stmt.offset((page - 1) * limit).limit(limit)
    ).scalars().all()

    if not fav_ids:
        return FavoritesListResponse(items=[], total=total)

    # Fetch restaurant rows (preserving favorite order)
    restaurants = db.execute(
        select(Restaurant)
        .options(selectinload(Restaurant.photos))
        .where(Restaurant.id.in_(fav_ids))
    ).scalars().all()

    # Preserve the favorites order (newest-favorited first)
    order_map = {rid: idx for idx, rid in enumerate(fav_ids)}
    restaurants.sort(key=lambda r: order_map.get(r.id, 9999))

    ratings = _fetch_ratings(db, [r.id for r in restaurants])
    items = [_orm_to_card(r, *ratings.get(r.id, (0.0, 0))) for r in restaurants]

    return FavoritesListResponse(items=items, total=total)


# ---------------------------------------------------------------------------
# User history
# ---------------------------------------------------------------------------

def get_user_history(db: Session, user_id: int) -> UserHistoryResponse:
    """
    Return:
      my_reviews            — all reviews written by this user, with restaurant name
      my_restaurants_added  — all restaurants created by this user (as RestaurantCard)
    """
    # ── My reviews (joined with restaurant name) ──────────────────────────────
    review_rows = db.execute(
        select(
            Review.id,
            Review.restaurant_id,
            Restaurant.name.label("restaurant_name"),
            Review.rating,
            Review.comment,
            Review.created_at,
            Review.updated_at,
        )
        .join(Restaurant, Restaurant.id == Review.restaurant_id)
        .where(Review.user_id == user_id)
        .order_by(Review.created_at.desc(), Review.id.desc())
    ).all()

    my_reviews = [
        ReviewHistoryItem(
            id=row.id,
            restaurant_id=row.restaurant_id,
            restaurant_name=row.restaurant_name,
            rating=row.rating,
            comment=row.comment,
            created_at=row.created_at,
            updated_at=row.updated_at,
        )
        for row in review_rows
    ]

    # ── Restaurants I added ───────────────────────────────────────────────────
    added = db.execute(
        select(Restaurant)
        .options(selectinload(Restaurant.photos))
        .where(Restaurant.created_by_user_id == user_id)
        .order_by(Restaurant.created_at.desc())
    ).scalars().all()

    rids = [r.id for r in added]
    ratings = _fetch_ratings(db, rids)
    my_restaurants_added = [
        _orm_to_card(r, *ratings.get(r.id, (0.0, 0))) for r in added
    ]

    return UserHistoryResponse(
        my_reviews=my_reviews,
        my_restaurants_added=my_restaurants_added,
    )
