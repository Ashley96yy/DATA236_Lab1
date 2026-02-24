"""
Review service — all DB access and business rules for Phase 4.

Functions:
    create_review          — validate + persist a new review
    update_review          — owner-only edit of rating/comment
    delete_review          — owner-only deletion
    get_reviews_for_restaurant — paginated list with joined user_name
    get_avg_rating         — (average_rating, review_count) for a restaurant
"""
from __future__ import annotations

from typing import Optional

from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.models.review import Review
from app.models.user import User
from app.schemas.review import ReviewCreate, ReviewResponse, ReviewUpdate
from app.services.errors import (
    ServiceConflict,
    ServiceForbidden,
    ServiceNotFound,
)


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _to_response(review: Review, user_name: str) -> ReviewResponse:
    return ReviewResponse(
        id=review.id,
        restaurant_id=review.restaurant_id,
        rating=review.rating,
        comment=review.comment,
        user_name=user_name,
        created_at=review.created_at,
        updated_at=review.updated_at,
    )


# ---------------------------------------------------------------------------
# Create
# ---------------------------------------------------------------------------

def create_review(
    db: Session,
    restaurant_id: int,
    data: ReviewCreate,
    user_id: int,
) -> ReviewResponse:
    """
    Persist a new review.
    Raises ServiceConflict if this user already reviewed this restaurant.
    """
    existing = db.execute(
        select(Review).where(
            Review.restaurant_id == restaurant_id,
            Review.user_id == user_id,
        )
    ).scalar_one_or_none()

    if existing is not None:
        raise ServiceConflict("You have already reviewed this restaurant.")

    review = Review(
        restaurant_id=restaurant_id,
        user_id=user_id,
        rating=data.rating,
        comment=data.comment,
    )
    db.add(review)
    db.commit()
    db.refresh(review)

    user = db.execute(select(User).where(User.id == user_id)).scalar_one()
    return _to_response(review, user.name)


# ---------------------------------------------------------------------------
# Update
# ---------------------------------------------------------------------------

def update_review(
    db: Session,
    review_id: int,
    data: ReviewUpdate,
    user_id: int,
) -> ReviewResponse:
    """
    Edit rating and/or comment. Only the review author may update.
    Raises ServiceNotFound or ServiceForbidden.
    """
    review = db.execute(
        select(Review).where(Review.id == review_id)
    ).scalar_one_or_none()

    if review is None:
        raise ServiceNotFound(f"Review {review_id} not found.")
    if review.user_id != user_id:
        raise ServiceForbidden("You can only edit your own reviews.")

    if data.rating is not None:
        review.rating = data.rating
    if data.comment is not None:
        review.comment = data.comment

    db.commit()
    db.refresh(review)

    user = db.execute(select(User).where(User.id == user_id)).scalar_one()
    return _to_response(review, user.name)


# ---------------------------------------------------------------------------
# Delete
# ---------------------------------------------------------------------------

def delete_review(db: Session, review_id: int, user_id: int) -> None:
    """
    Delete a review. Only the review author may delete.
    Raises ServiceNotFound or ServiceForbidden.
    """
    review = db.execute(
        select(Review).where(Review.id == review_id)
    ).scalar_one_or_none()

    if review is None:
        raise ServiceNotFound(f"Review {review_id} not found.")
    if review.user_id != user_id:
        raise ServiceForbidden("You can only delete your own reviews.")

    db.delete(review)
    db.commit()


# ---------------------------------------------------------------------------
# List
# ---------------------------------------------------------------------------

def get_reviews_for_restaurant(
    db: Session,
    restaurant_id: int,
    page: int = 1,
    limit: int = 20,
) -> dict:
    """
    Return paginated reviews for a restaurant with user_name joined from users.
    Response: {"items": [...], "total": int, "page": int, "limit": int}
    """
    base_stmt = (
        select(Review, User.name.label("user_name"))
        .join(User, User.id == Review.user_id)
        .where(Review.restaurant_id == restaurant_id)
        .order_by(Review.created_at.desc(), Review.id.desc())
    )

    total: int = db.execute(
        select(func.count()).select_from(
            select(Review).where(Review.restaurant_id == restaurant_id).subquery()
        )
    ).scalar_one()

    rows = db.execute(base_stmt.offset((page - 1) * limit).limit(limit)).all()

    items = [_to_response(row.Review, row.user_name) for row in rows]
    return {"items": items, "total": total, "page": page, "limit": limit}


# ---------------------------------------------------------------------------
# Rating aggregation
# ---------------------------------------------------------------------------

def get_avg_rating(db: Session, restaurant_id: int) -> tuple[float, int]:
    """
    Return (average_rating, review_count) for a restaurant.
    average_rating is 0.0 if no reviews exist.
    """
    row = db.execute(
        select(
            func.avg(Review.rating).label("avg"),
            func.count(Review.id).label("cnt"),
        ).where(Review.restaurant_id == restaurant_id)
    ).one()

    avg = float(row.avg) if row.avg is not None else 0.0
    cnt = int(row.cnt)
    return round(avg, 2), cnt
