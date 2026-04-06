from __future__ import annotations

from pymongo import MongoClient

from backend.shared.config.settings import get_settings


def get_mongo_client() -> MongoClient:
    settings = get_settings()
    return MongoClient(settings.mongodb_url)
