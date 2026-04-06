from __future__ import annotations

from functools import lru_cache

from pymongo import MongoClient

from shared.config.settings import get_settings


@lru_cache(maxsize=1)
def get_mongo_client() -> MongoClient:
    settings = get_settings()
    return MongoClient(settings.mongodb_url)


def get_mongo_database():
    settings = get_settings()
    return get_mongo_client()[settings.mongodb_db_name]


def ping_mongo() -> bool:
    get_mongo_client().admin.command("ping")
    return True
