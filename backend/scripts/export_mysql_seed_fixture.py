from __future__ import annotations

import json
import mimetypes
from base64 import b64encode
from pathlib import Path
from urllib.parse import urlparse

from app.db.session import SessionLocal
from app.models.favorite import Favorite
from app.models.owner import Owner
from app.models.restaurant import Restaurant
from app.models.restaurant_photo import RestaurantPhoto
from app.models.review import Review
from app.models.user import User
from app.models.user_preference import UserPreference
from migrate_mysql_to_mongo import (
    _activity_log_docs,
    _favorite_doc,
    _owner_doc,
    _photo_doc,
    _preference_doc,
    _restaurant_doc,
    _review_doc,
    _user_doc,
)

FIXTURE_PATH = Path(__file__).resolve().with_name("lab2_seed_fixture.json")
BACKEND_DIR = Path(__file__).resolve().parents[1]
UPLOADS_PREFIXES = (
    "http://127.0.0.1:8000/uploads/",
    "http://localhost:8000/uploads/",
)


def _json_safe(value):
    if isinstance(value, dict):
        return {key: _json_safe(item) for key, item in value.items()}
    if isinstance(value, list):
        return [_json_safe(item) for item in value]
    if hasattr(value, "isoformat"):
        return value.isoformat()
    return value


def _local_upload_url_to_data_uri(value):
    if not isinstance(value, str):
        return value
    if not any(value.startswith(prefix) for prefix in UPLOADS_PREFIXES):
        return value

    parsed = urlparse(value)
    relative_path = parsed.path.lstrip("/")
    local_path = BACKEND_DIR / relative_path
    if not local_path.is_file():
        return value

    mime_type, _ = mimetypes.guess_type(local_path.name)
    mime_type = mime_type or "application/octet-stream"
    encoded = b64encode(local_path.read_bytes()).decode("utf-8")
    return f"data:{mime_type};base64,{encoded}"


def _normalize_fixture_media(value):
    if isinstance(value, dict):
        return {key: _normalize_fixture_media(item) for key, item in value.items()}
    if isinstance(value, list):
        return [_normalize_fixture_media(item) for item in value]
    return _local_upload_url_to_data_uri(value)


def export_fixture() -> dict[str, list[dict]]:
    db_session = SessionLocal()
    try:
        users = db_session.query(User).all()
        owners = db_session.query(Owner).all()
        preferences = db_session.query(UserPreference).all()
        restaurants = db_session.query(Restaurant).all()
        reviews = db_session.query(Review).all()
        favorites = db_session.query(Favorite).all()
        photos = db_session.query(RestaurantPhoto).all()

        payload = {
            "users": [_json_safe(_user_doc(user)) for user in users],
            "owners": [_json_safe(_owner_doc(owner)) for owner in owners],
            "user_preferences": [_json_safe(_preference_doc(pref)) for pref in preferences],
            "restaurants": [_json_safe(_restaurant_doc(restaurant)) for restaurant in restaurants],
            "reviews": [_json_safe(_review_doc(review)) for review in reviews],
            "favorites": [_json_safe(_favorite_doc(favorite)) for favorite in favorites],
            "restaurant_photos": [_json_safe(_photo_doc(photo)) for photo in photos],
            "activity_logs": [_json_safe(log) for log in _activity_log_docs(reviews=reviews, restaurants=restaurants)],
        }
    finally:
        db_session.close()

    payload = _normalize_fixture_media(payload)
    FIXTURE_PATH.write_text(json.dumps(payload, indent=2), encoding="utf-8")
    return payload


def main() -> None:
    payload = export_fixture()
    print(f"Wrote fixture to {FIXTURE_PATH}")
    for key, value in payload.items():
        print(f"{key}: {len(value)}")


if __name__ == "__main__":
    main()
