from __future__ import annotations

from pymongo import ASCENDING

from shared.config.settings import get_settings
from shared.db.collections import (
    ACTIVITY_LOGS,
    COUNTERS,
    FAVORITES,
    OWNERS,
    RESTAURANTS,
    RESTAURANT_PHOTOS,
    REVIEWS,
    SESSIONS,
    USER_PREFERENCES,
    USERS,
)
from shared.db.mongo import get_mongo_database


def ensure_lab2_indexes() -> None:
    settings = get_settings()
    db = get_mongo_database()

    db[USERS].create_index([("email", ASCENDING)], unique=True, name="users_email_unique")
    db[OWNERS].create_index([("email", ASCENDING)], unique=True, name="owners_email_unique")
    db[USER_PREFERENCES].create_index(
        [("user_id", ASCENDING)],
        unique=True,
        name="user_preferences_user_id_unique",
    )
    db[FAVORITES].create_index(
        [("user_id", ASCENDING), ("restaurant_id", ASCENDING)],
        unique=True,
        name="favorites_user_restaurant_unique",
    )
    db[REVIEWS].create_index(
        [("restaurant_id", ASCENDING), ("user_id", ASCENDING)],
        unique=True,
        name="reviews_restaurant_user_unique",
    )
    db[REVIEWS].create_index([("restaurant_id", ASCENDING)], name="reviews_restaurant_id_idx")
    db[RESTAURANTS].create_index([("city", ASCENDING)], name="restaurants_city_idx")
    db[RESTAURANTS].create_index([("name", ASCENDING)], name="restaurants_name_idx")
    db[RESTAURANTS].create_index([("cuisine_type", ASCENDING)], name="restaurants_cuisine_idx")
    db[RESTAURANT_PHOTOS].create_index(
        [("restaurant_id", ASCENDING)],
        name="restaurant_photos_restaurant_id_idx",
    )
    db[ACTIVITY_LOGS].create_index([("user_id", ASCENDING)], name="activity_logs_user_id_idx")
    db[SESSIONS].create_index(
        [("token", ASCENDING)],
        unique=True,
        name="sessions_token_unique",
    )
    db[SESSIONS].create_index(
        [("expires_at", ASCENDING)],
        expireAfterSeconds=0,
        name=f"sessions_ttl_{settings.session_ttl_hours}h",
    )
    db[COUNTERS].create_index([("_id", ASCENDING)], unique=True, name="counters_id_unique")
