from __future__ import annotations

from datetime import datetime, timedelta, timezone

from shared.config.settings import get_settings
from shared.db.collections import SESSIONS
from shared.db.mongo import get_mongo_database


def build_session_document(*, subject_id: int, role: str, token: str) -> dict:
    settings = get_settings()
    expires_at = datetime.now(timezone.utc) + timedelta(hours=settings.session_ttl_hours)
    return {
        "subject_id": subject_id,
        "role": role,
        "token": token,
        "expires_at": expires_at,
        "created_at": datetime.now(timezone.utc),
    }


def store_session(document: dict) -> None:
    db = get_mongo_database()
    db[SESSIONS].replace_one({"token": document["token"]}, document, upsert=True)


def get_session_by_token(token: str) -> dict | None:
    db = get_mongo_database()
    return db[SESSIONS].find_one({"token": token})
