from __future__ import annotations

import re
from datetime import datetime, timezone

from shared.db.collections import OWNERS, RESTAURANTS, RESTAURANT_PHOTOS, REVIEWS, USERS
from shared.db.counters import get_next_sequence
from shared.db.mongo import get_mongo_database


def _db():
    return get_mongo_database()


def get_user_by_id(user_id: int) -> dict | None:
    return _db()[USERS].find_one({"_id": int(user_id)})


def get_owner_by_id(owner_id: int) -> dict | None:
    return _db()[OWNERS].find_one({"_id": int(owner_id)})


def create_restaurant(*, payload: dict, created_by_user_id: int) -> dict:
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
        "hours": payload.get("hours") or {},
        "pricing_tier": payload.get("pricing_tier"),
        "amenities": payload.get("amenities") or [],
        "created_by_user_id": int(created_by_user_id),
        "claimed_by_owner_id": None,
    }
    _db()[RESTAURANTS].insert_one(document)
    return document


def get_restaurant_by_id(restaurant_id: int) -> dict | None:
    return _db()[RESTAURANTS].find_one({"_id": int(restaurant_id)})


def get_restaurant_photos(restaurant_id: int) -> list[dict]:
    return list(_db()[RESTAURANT_PHOTOS].find({"restaurant_id": int(restaurant_id)}))


def add_restaurant_photos(
    restaurant_id: int,
    photo_urls: list[str],
    *,
    uploaded_by_user_id: int | None = None,
    uploaded_by_owner_id: int | None = None,
) -> list[dict]:
    db = _db()
    created = []
    for photo_url in photo_urls:
        photo_id = get_next_sequence(RESTAURANT_PHOTOS)
        document = {
            "_id": photo_id,
            "restaurant_id": int(restaurant_id),
            "photo_url": photo_url,
            "uploaded_by_user_id": uploaded_by_user_id,
            "uploaded_by_owner_id": uploaded_by_owner_id,
            "created_at": datetime.now(timezone.utc),
        }
        db[RESTAURANT_PHOTOS].insert_one(document)
        created.append(document)
    return created


def get_restaurant_reviews(restaurant_id: int) -> list[dict]:
    return list(_db()[REVIEWS].find({"restaurant_id": int(restaurant_id)}))


def list_reviews_paginated(restaurant_id: int, page: int, limit: int) -> dict:
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


def get_user_name(user_id: int) -> str:
    user = _db()[USERS].find_one({"_id": int(user_id)})
    return user["name"] if user else "Unknown User"


def search_restaurants(
    *,
    name: str | None,
    cuisine: str | None,
    keywords: str | None,
    city: str | None,
    zip_code: str | None,
    sort: str,
    page: int,
    limit: int,
) -> dict:
    query: dict = {}

    if name:
        query["name"] = {"$regex": re.escape(name), "$options": "i"}
    if cuisine:
        query["cuisine_type"] = {"$regex": re.escape(cuisine), "$options": "i"}
    if city:
        query["address.city"] = {"$regex": re.escape(city), "$options": "i"}
    if zip_code:
        query["address.zip_code"] = zip_code

    keyword_filter = None
    if keywords:
        keyword_regex = {"$regex": re.escape(keywords), "$options": "i"}
        keyword_filter = {
            "$or": [
                {"name": keyword_regex},
                {"description": keyword_regex},
                {"amenities": {"$elemMatch": keyword_regex}},
            ]
        }

    final_query = query if keyword_filter is None else {"$and": [query, keyword_filter]} if query else keyword_filter

    restaurants = list(_db()[RESTAURANTS].find(final_query))
    enriched = []
    for restaurant in restaurants:
        reviews = get_restaurant_reviews(int(restaurant["_id"]))
        photos = get_restaurant_photos(int(restaurant["_id"]))
        review_count = len(reviews)
        average_rating = round(sum(r.get("rating", 0) for r in reviews) / review_count, 2) if review_count else 0.0
        enriched.append(
            {
                **restaurant,
                "review_count": review_count,
                "average_rating": average_rating,
                "cover_photo_url": photos[0]["photo_url"] if photos else None,
            }
        )

    if sort == "rating":
        enriched.sort(key=lambda item: (-item["average_rating"], item["name"].lower()))
    elif sort == "review_count":
        enriched.sort(key=lambda item: (-item["review_count"], item["name"].lower()))
    else:
        enriched.sort(key=lambda item: item["name"].lower())

    total = len(enriched)
    start = (page - 1) * limit
    end = start + limit
    return {"items": enriched[start:end], "total": total, "page": page, "limit": limit}
