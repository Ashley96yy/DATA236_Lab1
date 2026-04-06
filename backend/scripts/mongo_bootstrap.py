from shared.db.collections import ALL_COLLECTIONS
from shared.db.indexes import ensure_lab2_indexes
from shared.db.mongo import get_mongo_database, ping_mongo


def main() -> None:
    ping_mongo()
    db = get_mongo_database()
    existing = set(db.list_collection_names())
    for collection_name in ALL_COLLECTIONS:
        if collection_name not in existing:
            db.create_collection(collection_name)
    ensure_lab2_indexes()
    print(f"MongoDB bootstrap complete for database '{db.name}'.")


if __name__ == "__main__":
    main()
