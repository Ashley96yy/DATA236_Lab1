import uuid
from pathlib import Path
import sys

from sqlalchemy import delete, select

PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from app.db.session import SessionLocal
from app.models.user import User


def main() -> None:
    temp_email = f"smoke_{uuid.uuid4().hex[:10]}@example.com"

    with SessionLocal() as db:
        temp_user = User(
            name="DB Smoke",
            email=temp_email,
            password_hash="not-a-real-hash",
        )
        db.add(temp_user)
        db.commit()
        db.refresh(temp_user)

        fetched_user = db.execute(select(User).where(User.email == temp_email)).scalar_one_or_none()
        if fetched_user is None:
            raise RuntimeError("Smoke test failed: inserted user was not found.")

        db.execute(delete(User).where(User.id == fetched_user.id))
        db.commit()

    print("DB smoke test passed (insert + read + delete).")


if __name__ == "__main__":
    main()
