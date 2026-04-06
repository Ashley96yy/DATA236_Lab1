from __future__ import annotations

from shared.auth.security import hash_password
from shared.db.collections import USER_PREFERENCES, USERS
from shared.db.counters import get_next_sequence
from shared.db.mongo import get_mongo_database


def _db():
    return get_mongo_database()


def get_user_by_email(email: str) -> dict | None:
    return _db()[USERS].find_one({"email": email.strip().lower()})


def get_user_by_id(user_id: int) -> dict | None:
    return _db()[USERS].find_one({"_id": int(user_id)})


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
