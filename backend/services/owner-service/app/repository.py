from __future__ import annotations

from datetime import datetime, timezone

from shared.auth.security import hash_password
from shared.db.collections import OWNERS, RESTAURANTS, REVIEWS, USERS
from shared.db.counters import get_next_sequence
from shared.db.mongo import get_mongo_database


def _db():
    return get_mongo_database()


def get_owner_by_email(email: str) -> dict | None:
    return _db()[OWNERS].find_one({"email": email.strip().lower()})


def get_owner_by_id(owner_id: int) -> dict | None:
    return _db()[OWNERS].find_one({"_id": int(owner_id)})


def create_owner(*, name: str, email: str, password: str, restaurant_location: str) -> dict:
    owner_id = get_next_sequence(OWNERS)
    document = {
        "_id": owner_id,
        "name": name.strip(),
        "email": email.strip().lower(),
        "password_hash": hash_password(password),
        "restaurant_location": restaurant_location.strip(),
    }
    _db()[OWNERS].insert_one(document)
    return document


def update_owner_profile(owner_id: int, payload: dict) -> dict:
    updates = {}
    if "name" in payload:
        updates["name"] = payload["name"].strip()
    if "restaurant_location" in payload:
        updates["restaurant_location"] = payload["restaurant_location"].strip()

    if updates:
        _db()[OWNERS].update_one({"_id": int(owner_id)}, {"$set": updates})
    return get_owner_by_id(owner_id)


def get_restaurant_by_id(restaurant_id: int) -> dict | None:
    return _db()[RESTAURANTS].find_one({"_id": int(restaurant_id)})


def claim_restaurant(owner_id: int, restaurant_id: int) -> dict | None:
    existing = get_restaurant_by_id(restaurant_id)
    if existing is None:
        return None
    _db()[RESTAURANTS].update_one(
        {"_id": int(restaurant_id)},
        {"$set": {"claimed_by_owner_id": int(owner_id)}},
    )
    return get_restaurant_by_id(restaurant_id)


def _effective_hours(payload: dict) -> dict:
    hours = payload.get("hours_json")
    if hours is None:
        hours = payload.get("hours")
    return hours or {}


def create_restaurant_for_owner(owner_id: int, payload: dict) -> dict:
    restaurant_id = get_next_sequence(RESTAURANTS)
    document = {
        "_id": restaurant_id,
        "name": payload["name"].strip(),
        "cuisine_type": payload.get("cuisine_type"),
        "description": payload.get("description"),
        "address": {
            "street": payload.get("street"),
            "city": payload["city"].strip(),
            "state": payload.get("state"),
            "zip_code": payload.get("zip_code"),
            "country": payload.get("country"),
        },
        "latitude": payload.get("latitude"),
        "longitude": payload.get("longitude"),
        "phone": payload.get("phone"),
        "email": payload.get("email"),
        "hours": _effective_hours(payload),
        "pricing_tier": payload.get("pricing_tier"),
        "amenities": payload.get("amenities") or [],
        "created_by_user_id": None,
        "claimed_by_owner_id": int(owner_id),
        "updated_at": datetime.now(timezone.utc),
    }
    _db()[RESTAURANTS].insert_one(document)
    return document


def update_restaurant_for_owner(owner_id: int, restaurant_id: int, payload: dict) -> dict | None:
    restaurant = get_restaurant_by_id(restaurant_id)
    if restaurant is None:
        return None

    address = {**(restaurant.get("address") or {})}
    for address_field, key in (
        ("street", "street"),
        ("city", "city"),
        ("state", "state"),
        ("zip_code", "zip_code"),
        ("country", "country"),
    ):
        if key in payload:
            address[address_field] = payload[key]

    updates = {}
    for field in (
        "name",
        "cuisine_type",
        "description",
        "latitude",
        "longitude",
        "phone",
        "email",
        "pricing_tier",
        "amenities",
    ):
        if field in payload:
            updates[field] = payload[field]

    if any(key in payload for key in ("street", "city", "state", "zip_code", "country")):
        updates["address"] = address

    if "hours_json" in payload or "hours" in payload:
        updates["hours"] = _effective_hours(payload)

    if updates:
        updates["updated_at"] = datetime.now(timezone.utc)
        _db()[RESTAURANTS].update_one(
            {"_id": int(restaurant_id), "claimed_by_owner_id": int(owner_id)},
            {"$set": updates},
        )
    return get_restaurant_by_id(restaurant_id)


def get_user_name(user_id: int) -> str:
    user = _db()[USERS].find_one({"_id": int(user_id)})
    return user["name"] if user else "Unknown User"


def list_restaurant_reviews_for_owner(owner_id: int, restaurant_id: int, page: int, limit: int) -> dict:
    restaurant = get_restaurant_by_id(restaurant_id)
    if restaurant is None:
        return {"restaurant": None, "items": [], "total": 0, "page": page, "limit": limit}

    cursor = (
        _db()[REVIEWS]
        .find({"restaurant_id": int(restaurant_id)})
        .sort("created_at", -1)
        .skip((page - 1) * limit)
        .limit(limit)
    )
    items = list(cursor)
    total = _db()[REVIEWS].count_documents({"restaurant_id": int(restaurant_id)})
    return {"restaurant": restaurant, "items": items, "total": total, "page": page, "limit": limit}


def get_owner_dashboard(owner_id: int) -> dict:
    db = _db()
    restaurants = list(db[RESTAURANTS].find({"claimed_by_owner_id": int(owner_id)}))
    restaurant_ids = [doc["_id"] for doc in restaurants]
    reviews = list(db[REVIEWS].find({"restaurant_id": {"$in": restaurant_ids}})) if restaurant_ids else []

    total_reviews = len(reviews)
    avg_rating = (
        round(sum(review.get("rating", 0) for review in reviews) / total_reviews, 2)
        if total_reviews
        else 0.0
    )

    rating_distribution = {1: 0, 2: 0, 3: 0, 4: 0, 5: 0}
    for review in reviews:
        rating = int(review.get("rating", 0))
        if rating in rating_distribution:
            rating_distribution[rating] += 1

    per_restaurant = {}
    for review in reviews:
        restaurant_id = int(review["restaurant_id"])
        bucket = per_restaurant.setdefault(restaurant_id, {"count": 0, "sum": 0})
        bucket["count"] += 1
        bucket["sum"] += int(review.get("rating", 0))

    cards = []
    for restaurant in restaurants:
        restaurant_id = int(restaurant["_id"])
        metrics = per_restaurant.get(restaurant_id, {"count": 0, "sum": 0})
        review_count = metrics["count"]
        restaurant_avg = round(metrics["sum"] / review_count, 2) if review_count else 0.0
        address = restaurant.get("address", {})
        cards.append(
            {
                "id": restaurant_id,
                "name": restaurant["name"],
                "cuisine_type": restaurant.get("cuisine_type"),
                "city": address.get("city"),
                "state": address.get("state"),
                "pricing_tier": restaurant.get("pricing_tier"),
                "avg_rating": restaurant_avg,
                "review_count": review_count,
            }
        )

    return {
        "claimed_count": len(restaurants),
        "total_reviews": total_reviews,
        "avg_rating": avg_rating,
        "rating_distribution": rating_distribution,
        "claimed_restaurants": cards,
    }
