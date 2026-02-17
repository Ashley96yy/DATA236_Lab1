from pathlib import Path
import sys

from sqlalchemy import text

PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from app.db.base import Base
from app.db.session import engine
from app.models.user import User


def main() -> None:
    Base.metadata.create_all(bind=engine, tables=[User.__table__])
    with engine.begin() as connection:
        has_state_column = connection.execute(
            text(
                """
                SELECT 1
                FROM information_schema.COLUMNS
                WHERE TABLE_SCHEMA = DATABASE()
                  AND TABLE_NAME = 'users'
                  AND COLUMN_NAME = 'state'
                LIMIT 1
                """
            )
        ).scalar_one_or_none()
        if has_state_column is None:
            connection.execute(text("ALTER TABLE users ADD COLUMN state VARCHAR(10) NULL AFTER city"))
    print("users table is ready")


if __name__ == "__main__":
    main()
