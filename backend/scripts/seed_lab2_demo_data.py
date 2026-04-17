from __future__ import annotations

import base64
import json
import os
from datetime import datetime, timezone
from pathlib import Path

from shared.auth.security import hash_password
from shared.db.collections import (
    ACTIVITY_LOGS,
    COUNTERS,
    FAVORITES,
    OWNERS,
    RESTAURANTS,
    RESTAURANT_PHOTOS,
    REVIEWS,
    USER_PREFERENCES,
    USERS,
)
from shared.db.mongo import get_mongo_database, ping_mongo

FIXTURE_PATH = Path(__file__).resolve().with_name("lab2_seed_fixture.json")


def _now() -> datetime:
    return datetime.now(timezone.utc)


def _svg_data_uri(label: str, *, bg: str, fg: str) -> str:
    svg = f"""
    <svg xmlns="http://www.w3.org/2000/svg" width="320" height="220" viewBox="0 0 320 220">
      <rect width="320" height="220" rx="24" fill="{bg}" />
      <text x="50%" y="50%" dominant-baseline="middle" text-anchor="middle"
            font-family="Arial, sans-serif" font-size="26" fill="{fg}">{label}</text>
    </svg>
    """.strip()
    encoded = base64.b64encode(svg.encode("utf-8")).decode("utf-8")
    return f"data:image/svg+xml;base64,{encoded}"


def _seed_users(db) -> list[dict]:
    users = [
        {
            "_id": 1,
            "name": "Ashley",
            "email": "ashley@example.com",
            "password_hash": hash_password("Passw0rd!"),
            "phone": "+1 4085550101",
            "about_me": "I like trying cozy and highly rated restaurants around San Jose.",
            "city": "San Jose",
            "state": "CA",
            "country": "US",
            "languages": ["English"],
            "gender": "female",
            "avatar_url": _svg_data_uri("Ashley", bg="#fde68a", fg="#7c2d12"),
            "created_at": _now(),
            "updated_at": _now(),
        },
        {
            "_id": 2,
            "name": "Lily",
            "email": "lily@example.com",
            "password_hash": hash_password("Passw0rd!"),
            "phone": "+1 4085550102",
            "about_me": "I usually look for casual places with good vegetarian options.",
            "city": "Santa Clara",
            "state": "CA",
            "country": "US",
            "languages": ["English"],
            "gender": "female",
            "avatar_url": _svg_data_uri("Lily", bg="#bfdbfe", fg="#1e3a8a"),
            "created_at": _now(),
            "updated_at": _now(),
        },
    ]
    for user in users:
        db[USERS].replace_one({"_id": user["_id"]}, user, upsert=True)
    return users


def _seed_owner(db) -> dict:
    owner = {
        "_id": 1,
        "name": "Black",
        "email": "owner@example.com",
        "password_hash": hash_password("Passw0rd!"),
        "restaurant_location": "Santa Clara, CA",
        "created_at": _now(),
        "updated_at": _now(),
    }
    db[OWNERS].replace_one({"_id": owner["_id"]}, owner, upsert=True)
    return owner


def _seed_preferences(db) -> list[dict]:
    preferences = [
        {
            "_id": 1,
            "user_id": 1,
            "cuisines": ["Chinese", "Japanese", "Italian"],
            "price_range": "$$",
            "preferred_locations": ["San Jose"],
            "search_radius_km": 10,
            "dietary_needs": [],
            "ambiance": ["quiet", "casual"],
            "sort_preference": "rating",
            "updated_at": _now(),
        },
        {
            "_id": 2,
            "user_id": 2,
            "cuisines": ["Vegan", "Mediterranean"],
            "price_range": "$$",
            "preferred_locations": ["Santa Clara"],
            "search_radius_km": 8,
            "dietary_needs": ["vegetarian"],
            "ambiance": ["family", "casual"],
            "sort_preference": "rating",
            "updated_at": _now(),
        },
    ]
    for preference in preferences:
        db[USER_PREFERENCES].replace_one({"user_id": preference["user_id"]}, preference, upsert=True)
    return preferences


def _seed_restaurants(db) -> list[dict]:
    restaurants = [
        {
            "_id": 1,
            "name": "Hunan Impression",
            "cuisine_type": "Chinese",
            "description": "Spicy Sichuan dishes with a cozy dinner atmosphere.",
            "address": {
                "street": "5152 Moorpark Ave Ste 30",
                "city": "San Jose",
                "state": "CA",
                "zip_code": "95129",
                "country": "US",
            },
            "latitude": None,
            "longitude": None,
            "phone": "+1 4088739982",
            "email": "hunan@restaurant.com",
            "hours": {
                "Mon": "11am - 8pm",
                "Tue": "Closed",
                "Wed": "11am - 8pm",
                "Thu": "11am - 8pm",
                "Fri": "11am - 8pm",
                "Sat": "11am - 8pm",
                "Sun": "11am - 8pm",
            },
            "pricing_tier": "$$",
            "amenities": ["WiFi", "Parking", "Takeout", "Delivery", "Reservations"],
            "created_by_user_id": 1,
            "claimed_by_owner_id": 1,
            "created_at": _now(),
            "updated_at": _now(),
        },
        {
            "_id": 2,
            "name": "Liuyishou Hot Pot",
            "cuisine_type": "Chinese",
            "description": "Hot pot restaurant with group seating and late dinner hours.",
            "address": {
                "street": "1199 S De Anza Blvd Ste 10",
                "city": "San Jose",
                "state": "CA",
                "zip_code": "95129",
                "country": "US",
            },
            "latitude": None,
            "longitude": None,
            "phone": "+1 4082178108",
            "email": "liuyishou@gmail.com",
            "hours": {
                "Mon": "11am - 11pm",
                "Tue": "11am - 11pm",
                "Wed": "11am - 11pm",
                "Thu": "11am - 11pm",
                "Fri": "11am - 11pm",
                "Sat": "11am - 11pm",
                "Sun": "11am - 11pm",
            },
            "pricing_tier": "$$$",
            "amenities": ["WiFi", "Takeout", "Wheelchair Accessible", "Parking", "Delivery"],
            "created_by_user_id": 1,
            "claimed_by_owner_id": None,
            "created_at": _now(),
            "updated_at": _now(),
        },
        {
            "_id": 3,
            "name": "Green Leaf Cafe",
            "cuisine_type": "Vegan",
            "description": "Casual plant-based dining with fast lunch service.",
            "address": {
                "street": "200 El Camino Real",
                "city": "Santa Clara",
                "state": "CA",
                "zip_code": "95050",
                "country": "US",
            },
            "latitude": None,
            "longitude": None,
            "phone": "+1 4085550130",
            "email": "hello@greenleaf.example",
            "hours": {
                "Mon": "10am - 8pm",
                "Tue": "10am - 8pm",
                "Wed": "10am - 8pm",
                "Thu": "10am - 8pm",
                "Fri": "10am - 8pm",
                "Sat": "10am - 9pm",
                "Sun": "10am - 9pm",
            },
            "pricing_tier": "$$",
            "amenities": ["WiFi", "Vegan Options", "Outdoor Seating"],
            "created_by_user_id": 2,
            "claimed_by_owner_id": None,
            "created_at": _now(),
            "updated_at": _now(),
        },
    ]
    for restaurant in restaurants:
        db[RESTAURANTS].replace_one({"_id": restaurant["_id"]}, restaurant, upsert=True)
    return restaurants


def _seed_reviews(db) -> list[dict]:
    reviews = [
        {
            "_id": 1,
            "restaurant_id": 1,
            "user_id": 2,
            "rating": 5,
            "comment": "Great flavor and cozy vibe. Service was fast.",
            "status": "processed",
            "created_at": _now(),
            "updated_at": _now(),
        },
        {
            "_id": 2,
            "restaurant_id": 2,
            "user_id": 1,
            "rating": 4,
            "comment": "Fun hot pot place for groups with lots of options.",
            "status": "processed",
            "created_at": _now(),
            "updated_at": _now(),
        },
        {
            "_id": 3,
            "restaurant_id": 3,
            "user_id": 2,
            "rating": 4,
            "comment": "Nice casual vegan lunch spot.",
            "status": "processed",
            "created_at": _now(),
            "updated_at": _now(),
        },
    ]
    for review in reviews:
        db[REVIEWS].replace_one({"_id": review["_id"]}, review, upsert=True)
    return reviews


def _seed_favorites(db) -> list[dict]:
    favorites = [
        {"_id": 1, "user_id": 1, "restaurant_id": 1, "created_at": _now()},
        {"_id": 2, "user_id": 1, "restaurant_id": 2, "created_at": _now()},
        {"_id": 3, "user_id": 2, "restaurant_id": 3, "created_at": _now()},
    ]
    for favorite in favorites:
        db[FAVORITES].replace_one({"_id": favorite["_id"]}, favorite, upsert=True)
    return favorites


def _seed_photos(db) -> list[dict]:
    photos = [
        {
            "_id": 1,
            "restaurant_id": 1,
            "photo_url": _svg_data_uri("Hunan", bg="#fecaca", fg="#7f1d1d"),
            "uploaded_by_user_id": 1,
            "uploaded_by_owner_id": None,
            "created_at": _now(),
        },
        {
            "_id": 2,
            "restaurant_id": 2,
            "photo_url": _svg_data_uri("Hot Pot", bg="#fed7aa", fg="#9a3412"),
            "uploaded_by_user_id": 1,
            "uploaded_by_owner_id": None,
            "created_at": _now(),
        },
        {
            "_id": 3,
            "restaurant_id": 3,
            "photo_url": _svg_data_uri("Green Leaf", bg="#bbf7d0", fg="#14532d"),
            "uploaded_by_user_id": 2,
            "uploaded_by_owner_id": None,
            "created_at": _now(),
        },
    ]
    for photo in photos:
        db[RESTAURANT_PHOTOS].replace_one({"_id": photo["_id"]}, photo, upsert=True)
    return photos


def _seed_activity_logs(db) -> list[dict]:
    logs = [
        {
            "_id": "restaurant-created-1",
            "user_id": 1,
            "restaurant_id": 1,
            "action": "restaurant.created",
            "source": "compose_seed",
            "created_at": _now(),
        },
        {
            "_id": "restaurant-created-2",
            "user_id": 1,
            "restaurant_id": 2,
            "action": "restaurant.created",
            "source": "compose_seed",
            "created_at": _now(),
        },
        {
            "_id": "restaurant-created-3",
            "user_id": 2,
            "restaurant_id": 3,
            "action": "restaurant.created",
            "source": "compose_seed",
            "created_at": _now(),
        },
        {
            "_id": "review-created-1",
            "user_id": 2,
            "restaurant_id": 1,
            "action": "review.created",
            "source": "compose_seed",
            "created_at": _now(),
        },
    ]
    for log in logs:
        db[ACTIVITY_LOGS].replace_one({"_id": log["_id"]}, log, upsert=True)
    return logs


def _sync_counters(db) -> None:
    counters = {
        USERS: 2,
        OWNERS: 1,
        RESTAURANTS: 3,
        REVIEWS: 3,
        FAVORITES: 3,
        RESTAURANT_PHOTOS: 3,
    }
    for collection_name, seq in counters.items():
        db[COUNTERS].replace_one({"_id": collection_name}, {"_id": collection_name, "seq": seq}, upsert=True)


def _load_fixture() -> dict | None:
    if not FIXTURE_PATH.exists():
        return None
    raw = FIXTURE_PATH.read_text(encoding="utf-8").strip()
    if not raw or raw == "{}":
        return None
    return json.loads(raw)


def _seed_from_fixture(db, fixture: dict) -> dict[str, int]:
    collections = {
        USERS: fixture.get("users", []),
        OWNERS: fixture.get("owners", []),
        USER_PREFERENCES: fixture.get("user_preferences", []),
        RESTAURANTS: fixture.get("restaurants", []),
        REVIEWS: fixture.get("reviews", []),
        FAVORITES: fixture.get("favorites", []),
        RESTAURANT_PHOTOS: fixture.get("restaurant_photos", []),
        ACTIVITY_LOGS: fixture.get("activity_logs", []),
    }

    for collection_name, documents in collections.items():
        for document in documents:
            db[collection_name].replace_one({"_id": document["_id"]}, document, upsert=True)

    counters = {
        USERS: max((doc["_id"] for doc in collections[USERS]), default=0),
        OWNERS: max((doc["_id"] for doc in collections[OWNERS]), default=0),
        RESTAURANTS: max((doc["_id"] for doc in collections[RESTAURANTS]), default=0),
        REVIEWS: max((doc["_id"] for doc in collections[REVIEWS]), default=0),
        FAVORITES: max((doc["_id"] for doc in collections[FAVORITES]), default=0),
        RESTAURANT_PHOTOS: max((doc["_id"] for doc in collections[RESTAURANT_PHOTOS]), default=0),
    }
    for collection_name, seq in counters.items():
        db[COUNTERS].replace_one({"_id": collection_name}, {"_id": collection_name, "seq": seq}, upsert=True)

    return {
        "users": len(collections[USERS]),
        "owners": len(collections[OWNERS]),
        "user_preferences": len(collections[USER_PREFERENCES]),
        "restaurants": len(collections[RESTAURANTS]),
        "reviews": len(collections[REVIEWS]),
        "favorites": len(collections[FAVORITES]),
        "restaurant_photos": len(collections[RESTAURANT_PHOTOS]),
        "activity_logs": len(collections[ACTIVITY_LOGS]),
    }


def seed_demo_data() -> None:
    ping_mongo()
    db = get_mongo_database()
    force_seed = os.getenv("LAB2_FORCE_SEED", "").lower() in {"1", "true", "yes"}

    if not force_seed and (db[USERS].count_documents({}) > 0 or db[RESTAURANTS].count_documents({}) > 0):
        print("MongoDB already contains application data. Skipping demo seed.")
        return

    fixture = _load_fixture()
    if fixture:
        summary = _seed_from_fixture(db, fixture)
        print(f"MongoDB fixture seed complete from {FIXTURE_PATH.name}.")
        for key, value in summary.items():
            print(f"{key}: {value}")
        demo_user = next((user for user in fixture.get("users", []) if user.get("email")), None)
        demo_owner = next((owner for owner in fixture.get("owners", []) if owner.get("email")), None)
        if demo_user:
            print(f"demo user login: {demo_user['email']} / use existing MySQL password")
        if demo_owner:
            print(f"demo owner login: {demo_owner['email']} / use existing MySQL password")
        return

    users = _seed_users(db)
    owner = _seed_owner(db)
    preferences = _seed_preferences(db)
    restaurants = _seed_restaurants(db)
    reviews = _seed_reviews(db)
    favorites = _seed_favorites(db)
    photos = _seed_photos(db)
    logs = _seed_activity_logs(db)
    _sync_counters(db)

    print("MongoDB demo seed complete.")
    print(f"users: {len(users)}")
    print("owners: 1")
    print(f"user_preferences: {len(preferences)}")
    print(f"restaurants: {len(restaurants)}")
    print(f"reviews: {len(reviews)}")
    print(f"favorites: {len(favorites)}")
    print(f"restaurant_photos: {len(photos)}")
    print(f"activity_logs: {len(logs)}")
    print("demo user login: ashley@example.com / Passw0rd!")
    print("demo owner login: owner@example.com / Passw0rd!")


def main() -> None:
    seed_demo_data()


if __name__ == "__main__":
    main()
