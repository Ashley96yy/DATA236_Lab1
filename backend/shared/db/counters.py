from __future__ import annotations

from pymongo import ReturnDocument

from shared.db.collections import COUNTERS
from shared.db.mongo import get_mongo_database


def get_next_sequence(name: str) -> int:
    db = get_mongo_database()
    document = db[COUNTERS].find_one_and_update(
        {"_id": name},
        {"$inc": {"seq": 1}},
        upsert=True,
        return_document=ReturnDocument.AFTER,
    )
    return int(document["seq"])
