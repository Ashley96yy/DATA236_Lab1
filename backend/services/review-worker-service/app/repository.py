from __future__ import annotations

from datetime import datetime, timezone

from shared.db.collections import REVIEWS, USERS
from shared.db.counters import get_next_sequence
from shared.db.mongo import get_mongo_database


def _db():
    return get_mongo_database()


def get_user_name(user_id: int) -> str:
    user = _db()[USERS].find_one({"_id": int(user_id)})
    return user["name"] if user else "Unknown User"


def create_review_from_event(event: dict) -> dict:
    review_id = int(event["review_id"]) if event.get("review_id") is not None else get_next_sequence(REVIEWS)
    now = datetime.now(timezone.utc)
    document = {
        "_id": review_id,
        "restaurant_id": int(event["restaurant_id"]),
        "user_id": int(event["user_id"]),
        "rating": int(event["rating"]),
        "comment": event.get("comment"),
        "status": "processed",
        "created_at": now,
        "updated_at": now,
    }
    _db()[REVIEWS].replace_one({"_id": review_id}, document, upsert=True)
    return document


def update_review_from_event(event: dict) -> dict | None:
    existing = _db()[REVIEWS].find_one({"_id": int(event["review_id"])})
    if existing is None:
        return None
    updates = {"updated_at": datetime.now(timezone.utc)}
    if event.get("rating") is not None:
        updates["rating"] = int(event["rating"])
    if "comment" in event:
        updates["comment"] = event.get("comment")
    _db()[REVIEWS].update_one({"_id": int(event["review_id"])}, {"$set": updates})
    return _db()[REVIEWS].find_one({"_id": int(event["review_id"])})


def delete_review_from_event(event: dict) -> bool:
    result = _db()[REVIEWS].delete_one({"_id": int(event["review_id"])})
    return result.deleted_count > 0
