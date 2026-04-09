from __future__ import annotations

import csv
from datetime import datetime, timezone
from pathlib import Path

from shared.auth.security import hash_password
from shared.db.collections import (
    ACTIVITY_LOGS,
    COUNTERS,
    RESTAURANTS,
    REVIEWS,
    USER_PREFERENCES,
    USERS,
)
from shared.db.mongo import get_mongo_database, ping_mongo

LOAD_TEST_USER_COUNT = 500
LOAD_TEST_PASSWORD = "Passw0rd!"
USER_ID_START = 1001
RESTAURANT_ID_START = 2001
CSV_PATH = Path(__file__).resolve().parents[2] / "jmeter" / "data" / "load_test_users.csv"


def _now() -> datetime:
    return datetime.now(timezone.utc)


def _sync_counter(db, collection_name: str, seq: int) -> None:
    db[COUNTERS].replace_one({"_id": collection_name}, {"_id": collection_name, "seq": seq}, upsert=True)


def seed_jmeter_users() -> None:
    ping_mongo()
    db = get_mongo_database()

    user_ids = list(range(USER_ID_START, USER_ID_START + LOAD_TEST_USER_COUNT))
    restaurant_ids = list(range(RESTAURANT_ID_START, RESTAURANT_ID_START + LOAD_TEST_USER_COUNT))

    db[REVIEWS].delete_many({"$or": [{"user_id": {"$in": user_ids}}, {"restaurant_id": {"$in": restaurant_ids}}]})
    db[USER_PREFERENCES].delete_many({"user_id": {"$in": user_ids}})
    db[ACTIVITY_LOGS].delete_many({"source": "jmeter_seed"})
    db[USERS].delete_many({"_id": {"$in": user_ids}})
    db[RESTAURANTS].delete_many({"_id": {"$in": restaurant_ids}})

    users = []
    restaurants = []
    now = _now()

    for index in range(LOAD_TEST_USER_COUNT):
      user_id = USER_ID_START + index
      restaurant_id = RESTAURANT_ID_START + index
      email = f"loaduser{index + 1:03d}@example.com"
      user = {
          "_id": user_id,
          "name": f"Load User {index + 1:03d}",
          "email": email,
          "password_hash": hash_password(LOAD_TEST_PASSWORD),
          "phone": None,
          "about_me": "JMeter load-testing account",
          "city": "San Jose",
          "state": "CA",
          "country": "US",
          "languages": ["English"],
          "gender": None,
          "avatar_url": None,
          "created_at": now,
          "updated_at": now,
      }
      restaurant = {
          "_id": restaurant_id,
          "name": f"Load Test Restaurant {index + 1:03d}",
          "cuisine_type": "American",
          "description": "Synthetic restaurant used for JMeter performance testing.",
          "address": {
              "street": f"{500 + index} Performance Ave",
              "city": "San Jose",
              "state": "CA",
              "zip_code": f"{95110 + (index % 50)}",
              "country": "US",
          },
          "latitude": None,
          "longitude": None,
          "phone": f"+1 408555{1000 + index:04d}",
          "email": f"restaurant{index + 1:03d}@example.com",
          "hours": {
              "Mon": "10am - 9pm",
              "Tue": "10am - 9pm",
              "Wed": "10am - 9pm",
              "Thu": "10am - 9pm",
              "Fri": "10am - 10pm",
              "Sat": "10am - 10pm",
              "Sun": "10am - 8pm",
          },
          "pricing_tier": "$$",
          "amenities": ["WiFi", "Takeout"],
          "created_by_user_id": user_id,
          "claimed_by_owner_id": None,
          "created_at": now,
          "updated_at": now,
      }
      users.append(user)
      restaurants.append(restaurant)

    if users:
        db[USERS].insert_many(users)
    if restaurants:
        db[RESTAURANTS].insert_many(restaurants)

    for index, user_id in enumerate(user_ids, start=1):
        db[USER_PREFERENCES].replace_one(
            {"user_id": user_id},
            {
                "_id": user_id,
                "user_id": user_id,
                "cuisines": ["American"],
                "price_range": "$$",
                "preferred_locations": ["San Jose"],
                "search_radius_km": 10,
                "dietary_needs": [],
                "ambiance": ["casual"],
                "sort_preference": "rating",
                "updated_at": now,
            },
            upsert=True,
        )
        db[ACTIVITY_LOGS].replace_one(
            {"_id": f"jmeter-user-{user_id}"},
            {
                "_id": f"jmeter-user-{user_id}",
                "user_id": user_id,
                "restaurant_id": restaurant_ids[index - 1],
                "action": "jmeter.seeded",
                "source": "jmeter_seed",
                "created_at": now,
            },
            upsert=True,
        )

    _sync_counter(db, USERS, max(user_ids))
    _sync_counter(db, RESTAURANTS, max(restaurant_ids))

    CSV_PATH.parent.mkdir(parents=True, exist_ok=True)
    with CSV_PATH.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.writer(handle)
        writer.writerow(["email", "password", "restaurant_id", "rating", "comment"])
        for index in range(LOAD_TEST_USER_COUNT):
            writer.writerow(
                [
                    f"loaduser{index + 1:03d}@example.com",
                    LOAD_TEST_PASSWORD,
                    RESTAURANT_ID_START + index,
                    5,
                    f"JMeter performance review {index + 1:03d}",
                ]
            )

    print("JMeter load-test seed complete.")
    print(f"users: {len(users)}")
    print(f"restaurants: {len(restaurants)}")
    print(f"csv: {CSV_PATH}")


def main() -> None:
    seed_jmeter_users()


if __name__ == "__main__":
    main()
