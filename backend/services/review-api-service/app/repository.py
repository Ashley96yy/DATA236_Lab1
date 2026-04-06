from __future__ import annotations

from datetime import datetime, timezone

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


def create_review(*, restaurant_id: int, user_id: int, payload: dict) -> dict:
    review_id = get_next_sequence(REVIEWS)
    now = datetime.now(timezone.utc)
    document = {
        "_id": review_id,
        "restaurant_id": int(restaurant_id),
        "user_id": int(user_id),
        "rating": int(payload["rating"]),
        "comment": payload.get("comment"),
        "status": "processed",
        "created_at": now,
        "updated_at": now,
    }
    _db()[REVIEWS].insert_one(document)
    return document


def update_review(review_id: int, payload: dict) -> dict | None:
    updates = {"updated_at": datetime.now(timezone.utc)}
    if "rating" in payload:
        updates["rating"] = int(payload["rating"])
    if "comment" in payload:
        updates["comment"] = payload["comment"]
    _db()[REVIEWS].update_one({"_id": int(review_id)}, {"$set": updates})
    return get_review_by_id(review_id)


def delete_review(review_id: int) -> None:
    _db()[REVIEWS].delete_one({"_id": int(review_id)})


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
