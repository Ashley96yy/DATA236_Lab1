from __future__ import annotations

from datetime import datetime, timezone

from sqlalchemy.orm import Session

from app.db.session import SessionLocal
from app.models.favorite import Favorite
from app.models.owner import Owner
from app.models.restaurant import Restaurant
from app.models.restaurant_photo import RestaurantPhoto
from app.models.review import Review
from app.models.user import User
from app.models.user_preference import UserPreference
from shared.db.collections import (
    ACTIVITY_LOGS,
    FAVORITES,
    OWNERS,
    RESTAURANTS,
    RESTAURANT_PHOTOS,
    REVIEWS,
    USER_PREFERENCES,
    USERS,
)
from shared.db.indexes import ensure_lab2_indexes
from shared.db.mongo import get_mongo_database, ping_mongo


def _iso_or_none(value):
    return value if value is not None else None


def _user_doc(user: User) -> dict:
    return {
        "_id": int(user.id),
        "name": user.name,
        "email": user.email,
        "password_hash": user.password_hash,
        "phone": user.phone,
        "about_me": user.about_me,
        "city": user.city,
        "state": user.state,
        "country": user.country,
        "languages": user.languages or [],
        "gender": user.gender,
        "avatar_url": user.avatar_url,
        "created_at": _iso_or_none(user.created_at),
        "updated_at": _iso_or_none(user.updated_at),
    }


def _owner_doc(owner: Owner) -> dict:
    return {
        "_id": int(owner.id),
        "name": owner.name,
        "email": owner.email,
        "password_hash": owner.password_hash,
        "restaurant_location": owner.restaurant_location,
        "created_at": _iso_or_none(owner.created_at),
        "updated_at": _iso_or_none(owner.updated_at),
    }


def _preference_doc(pref: UserPreference) -> dict:
    return {
        "_id": int(pref.user_id),
        "user_id": int(pref.user_id),
        "cuisines": pref.cuisines or [],
        "price_range": pref.price_range,
        "preferred_locations": pref.preferred_locations or [],
        "search_radius_km": pref.search_radius_km,
        "dietary_needs": pref.dietary_needs or [],
        "ambiance": pref.ambiance or [],
        "sort_preference": pref.sort_preference,
        "updated_at": _iso_or_none(pref.updated_at),
    }


def _restaurant_doc(restaurant: Restaurant) -> dict:
    return {
        "_id": int(restaurant.id),
        "name": restaurant.name,
        "cuisine_type": restaurant.cuisine_type,
        "description": restaurant.description,
        "address": {
            "street": restaurant.street,
            "city": restaurant.city,
            "state": restaurant.state,
            "zip_code": restaurant.zip_code,
            "country": restaurant.country,
        },
        "legacy_address": restaurant.legacy_address,
        "legacy_contact_info": restaurant.legacy_contact_info,
        "legacy_hours": restaurant.legacy_hours,
        "latitude": restaurant.latitude,
        "longitude": restaurant.longitude,
        "phone": restaurant.phone,
        "email": restaurant.email,
        "hours": restaurant.hours_json or {},
        "pricing_tier": restaurant.pricing_tier,
        "amenities": restaurant.amenities or [],
        "created_by_user_id": int(restaurant.created_by_user_id) if restaurant.created_by_user_id else None,
        "claimed_by_owner_id": int(restaurant.claimed_by_owner_id) if restaurant.claimed_by_owner_id else None,
        "created_at": _iso_or_none(restaurant.created_at),
        "updated_at": _iso_or_none(restaurant.updated_at),
    }


def _review_doc(review: Review) -> dict:
    return {
        "_id": int(review.id),
        "restaurant_id": int(review.restaurant_id),
        "user_id": int(review.user_id),
        "rating": review.rating,
        "comment": review.comment,
        "status": "processed",
        "created_at": _iso_or_none(review.created_at),
        "updated_at": _iso_or_none(review.updated_at),
    }


def _favorite_doc(favorite: Favorite) -> dict:
    return {
        "_id": int(favorite.id),
        "user_id": int(favorite.user_id),
        "restaurant_id": int(favorite.restaurant_id),
        "created_at": _iso_or_none(favorite.created_at),
    }


def _photo_doc(photo: RestaurantPhoto) -> dict:
    return {
        "_id": int(photo.id),
        "restaurant_id": int(photo.restaurant_id),
        "photo_url": photo.photo_url,
        "uploaded_by_user_id": int(photo.uploaded_by_user_id) if photo.uploaded_by_user_id else None,
        "uploaded_by_owner_id": int(photo.uploaded_by_owner_id) if photo.uploaded_by_owner_id else None,
        "created_at": _iso_or_none(photo.created_at),
    }


def _activity_log_docs(*, reviews: list[Review], restaurants: list[Restaurant]) -> list[dict]:
    documents: list[dict] = []
    now = datetime.now(timezone.utc)

    for review in reviews:
        documents.append(
            {
                "_id": f"review-{review.id}",
                "user_id": int(review.user_id),
                "restaurant_id": int(review.restaurant_id),
                "action": "review.created",
                "source": "mysql_migration",
                "created_at": _iso_or_none(review.created_at) or now,
            }
        )

    for restaurant in restaurants:
        if restaurant.created_by_user_id:
            documents.append(
                {
                    "_id": f"restaurant-{restaurant.id}",
                    "user_id": int(restaurant.created_by_user_id),
                    "restaurant_id": int(restaurant.id),
                    "action": "restaurant.created",
                    "source": "mysql_migration",
                    "created_at": _iso_or_none(restaurant.created_at) or now,
                }
            )

    return documents


def migrate(db_session: Session) -> dict[str, int]:
    ping_mongo()
    mongo = get_mongo_database()
    ensure_lab2_indexes()

    users = db_session.query(User).all()
    owners = db_session.query(Owner).all()
    preferences = db_session.query(UserPreference).all()
    restaurants = db_session.query(Restaurant).all()
    reviews = db_session.query(Review).all()
    favorites = db_session.query(Favorite).all()
    photos = db_session.query(RestaurantPhoto).all()

    for user in users:
        mongo[USERS].replace_one({"_id": int(user.id)}, _user_doc(user), upsert=True)
    for owner in owners:
        mongo[OWNERS].replace_one({"_id": int(owner.id)}, _owner_doc(owner), upsert=True)
    for pref in preferences:
        mongo[USER_PREFERENCES].replace_one({"_id": int(pref.user_id)}, _preference_doc(pref), upsert=True)
    for restaurant in restaurants:
        mongo[RESTAURANTS].replace_one(
            {"_id": int(restaurant.id)},
            _restaurant_doc(restaurant),
            upsert=True,
        )
    for review in reviews:
        mongo[REVIEWS].replace_one({"_id": int(review.id)}, _review_doc(review), upsert=True)
    for favorite in favorites:
        mongo[FAVORITES].replace_one({"_id": int(favorite.id)}, _favorite_doc(favorite), upsert=True)
    for photo in photos:
        mongo[RESTAURANT_PHOTOS].replace_one({"_id": int(photo.id)}, _photo_doc(photo), upsert=True)

    activity_logs = _activity_log_docs(reviews=reviews, restaurants=restaurants)
    for log in activity_logs:
        mongo[ACTIVITY_LOGS].replace_one({"_id": log["_id"]}, log, upsert=True)

    return {
        "users": len(users),
        "owners": len(owners),
        "user_preferences": len(preferences),
        "restaurants": len(restaurants),
        "reviews": len(reviews),
        "favorites": len(favorites),
        "restaurant_photos": len(photos),
        "activity_logs": len(activity_logs),
    }


def main() -> None:
    db_session = SessionLocal()
    try:
        summary = migrate(db_session)
    finally:
        db_session.close()

    print("MySQL to MongoDB migration complete.")
    for key, value in summary.items():
        print(f"{key}: {value}")


if __name__ == "__main__":
    main()
