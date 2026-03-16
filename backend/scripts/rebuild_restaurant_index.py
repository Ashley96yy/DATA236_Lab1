from __future__ import annotations

from app.db.session import SessionLocal
from app.services.restaurant_vector_service import rebuild_restaurant_index


def main() -> None:
    db = SessionLocal()
    try:
        count = rebuild_restaurant_index(db)
    finally:
        db.close()

    print(f"Indexed {count} restaurant document(s).")


if __name__ == "__main__":
    main()
