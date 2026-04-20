from __future__ import annotations

from datetime import datetime, timezone

from shared.auth.security import hash_password
from shared.db.collections import FAVORITES, RESTAURANTS, REVIEWS, USER_PREFERENCES, USERS
from shared.db.counters import get_next_sequence
from shared.db.mongo import get_mongo_database


def _db():
    return get_mongo_database()


def get_user_by_email(email: str) -> dict | None:
    return _db()[USERS].find_one({"email": email.strip().lower()})


def get_user_by_id(user_id: int) -> dict | None:
    return _db()[USERS].find_one({"_id": int(user_id)})


def _normalize_languages(value: str | list[str] | None) -> list[str]:
    if value is None:
        return []
    if isinstance(value, str):
        trimmed = value.strip()
        return [trimmed] if trimmed else []
    return [item.strip() for item in value if isinstance(item, str) and item.strip()]


def create_user(*, name: str, email: str, password: str) -> dict:
    user_id = get_next_sequence(USERS)
    document = {
        "_id": user_id,
        "name": name.strip(),
        "email": email.strip().lower(),
        "password_hash": hash_password(password),
        "phone": None,
        "about_me": None,
        "city": None,
        "state": None,
        "country": None,
        "languages": [],
        "gender": None,
        "avatar_url": None,
    }
    _db()[USERS].insert_one(document)
    return document


def update_user_profile(user_id: int, payload: dict) -> dict:
    updates = {}
    for field in ("name", "phone", "about_me", "city", "state", "gender"):
        if field in payload:
            value = payload[field]
            updates[field] = value.strip() if isinstance(value, str) else value

    if "country" in payload:
        value = payload["country"]
        updates["country"] = value.strip().upper() if isinstance(value, str) and value.strip() else None

    if "languages" in payload:
        updates["languages"] = _normalize_languages(payload["languages"])

    if updates:
        updates["updated_at"] = datetime.now(timezone.utc)
        _db()[USERS].update_one({"_id": int(user_id)}, {"$set": updates})
    return get_user_by_id(user_id)


def update_user_avatar(user_id: int, avatar_url: str) -> dict:
    _db()[USERS].update_one(
        {"_id": int(user_id)},
        {"$set": {"avatar_url": avatar_url, "updated_at": datetime.now(timezone.utc)}},
    )
    return get_user_by_id(user_id)


def get_preferences(user_id: int) -> dict:
    document = _db()[USER_PREFERENCES].find_one({"user_id": int(user_id)})
    if document is None:
        return {
            "user_id": int(user_id),
            "cuisines": [],
            "price_range": None,
            "preferred_locations": [],
            "search_radius_km": None,
            "dietary_needs": [],
            "ambiance": [],
            "sort_preference": "rating",
        }
    return document


def update_preferences(user_id: int, payload: dict) -> dict:
    existing = get_preferences(user_id)
    merged = {
        "user_id": int(user_id),
        "cuisines": payload.get("cuisines", existing.get("cuisines", [])),
        "price_range": payload.get("price_range", existing.get("price_range")),
        "preferred_locations": payload.get(
            "preferred_locations",
            existing.get("preferred_locations", []),
        ),
        "search_radius_km": payload.get(
            "search_radius_km",
            existing.get("search_radius_km"),
        ),
        "dietary_needs": payload.get("dietary_needs", existing.get("dietary_needs", [])),
        "ambiance": payload.get("ambiance", existing.get("ambiance", [])),
        "sort_preference": payload.get("sort_preference", existing.get("sort_preference", "rating")),
    }
    _db()[USER_PREFERENCES].replace_one({"user_id": int(user_id)}, merged, upsert=True)
    return merged


# --- Favorites ---

def get_favorites_page(user_id: int, page: int, limit: int) -> dict:
    db = _db()
    total = db[FAVORITES].count_documents({"user_id": int(user_id)})
    cursor = db[FAVORITES].find({"user_id": int(user_id)}).skip((page - 1) * limit).limit(limit)
    items = []
    for fav in cursor:
        restaurant = db[RESTAURANTS].find_one({"_id": int(fav["restaurant_id"])})
        if restaurant:
            address = restaurant.get("address", {})
            reviews = list(db["reviews"].find({"restaurant_id": int(restaurant["_id"])}))
            review_count = len(reviews)
            avg = round(sum(r.get("rating", 0) for r in reviews) / review_count, 2) if review_count else 0.0
            items.append({
                "restaurant_id": int(restaurant["_id"]),
                "name": restaurant["name"],
                "cuisine_type": restaurant.get("cuisine_type"),
                "city": address.get("city"),
                "state": address.get("state"),
                "pricing_tier": restaurant.get("pricing_tier"),
                "average_rating": avg,
                "review_count": review_count,
            })
    return {"items": items, "total": total, "page": page, "limit": limit}


def add_favorite(user_id: int, restaurant_id: int) -> None:
    doc = {"user_id": int(user_id), "restaurant_id": int(restaurant_id)}
    _db()[FAVORITES].replace_one(doc, doc, upsert=True)


def remove_favorite(user_id: int, restaurant_id: int) -> bool:
    result = _db()[FAVORITES].delete_one({"user_id": int(user_id), "restaurant_id": int(restaurant_id)})
    return result.deleted_count > 0


def get_favorite_by_user_and_restaurant(user_id: int, restaurant_id: int) -> dict | None:
    return _db()[FAVORITES].find_one({"user_id": int(user_id), "restaurant_id": int(restaurant_id)})


# --- History ---

def get_user_history(user_id: int) -> dict:
    db = _db()

    raw_reviews = list(db[REVIEWS].find({"user_id": int(user_id)}).sort("created_at", -1))
    my_reviews = []
    for review in raw_reviews:
        restaurant = db[RESTAURANTS].find_one({"_id": int(review["restaurant_id"])})
        my_reviews.append({
            "review_id": int(review["_id"]),
            "restaurant_id": int(review["restaurant_id"]),
            "restaurant_name": restaurant["name"] if restaurant else "Unknown",
            "rating": int(review["rating"]),
            "comment": review.get("comment"),
            "created_at": review.get("created_at"),
        })

    added_docs = list(db[RESTAURANTS].find({"created_by_user_id": int(user_id)}))
    my_restaurants_added = []
    for restaurant in added_docs:
        address = restaurant.get("address", {})
        all_reviews = list(db[REVIEWS].find({"restaurant_id": int(restaurant["_id"])}))
        review_count = len(all_reviews)
        avg = round(sum(r.get("rating", 0) for r in all_reviews) / review_count, 2) if review_count else 0.0
        my_restaurants_added.append({
            "restaurant_id": int(restaurant["_id"]),
            "name": restaurant["name"],
            "cuisine_type": restaurant.get("cuisine_type"),
            "city": address.get("city"),
            "state": address.get("state"),
            "pricing_tier": restaurant.get("pricing_tier"),
            "average_rating": avg,
            "review_count": review_count,
        })

    return {"my_reviews": my_reviews, "my_restaurants_added": my_restaurants_added}


def list_restaurants_for_ai() -> list[dict]:
    return list(_db()[RESTAURANTS].find({}))


def get_reviews_for_restaurant(restaurant_id: int) -> list[dict]:
    return list(_db()[REVIEWS].find({"restaurant_id": int(restaurant_id)}))
