from __future__ import annotations

from shared.db.collections import RESTAURANTS, REVIEWS, USERS
from shared.db.counters import get_next_sequence
from shared.db.mongo import get_mongo_database


def _db():
    return get_mongo_database()


def get_user_by_id(user_id: int) -> dict | None:
    return _db()[USERS].find_one({"_id": int(user_id)})


def get_restaurant_by_id(restaurant_id: int) -> dict | None:
    return _db()[RESTAURANTS].find_one({"_id": int(restaurant_id)})


def get_review_by_id(review_id: int) -> dict | None:
    return _db()[REVIEWS].find_one({"_id": int(review_id)})


def get_review_by_restaurant_and_user(restaurant_id: int, user_id: int) -> dict | None:
    return _db()[REVIEWS].find_one({"restaurant_id": int(restaurant_id), "user_id": int(user_id)})


def reserve_next_review_id() -> int:
    return get_next_sequence(REVIEWS)


def get_user_name(user_id: int) -> str:
    user = get_user_by_id(user_id)
    return user["name"] if user else "Unknown User"


def list_reviews_for_restaurant(restaurant_id: int, page: int, limit: int) -> dict:
    cursor = (
        _db()[REVIEWS]
        .find({"restaurant_id": int(restaurant_id)})
        .sort("created_at", -1)
        .skip((page - 1) * limit)
        .limit(limit)
    )
    items = list(cursor)
    total = _db()[REVIEWS].count_documents({"restaurant_id": int(restaurant_id)})
    return {"items": items, "total": total, "page": page, "limit": limit}
