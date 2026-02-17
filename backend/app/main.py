from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from sqlalchemy import text

from app.api.v1.router import api_router
from app.core.config import get_settings
from app.core.errors import register_exception_handlers
from app.db.session import engine

settings = get_settings()
settings.uploads_dir.mkdir(parents=True, exist_ok=True)
app = FastAPI(title=settings.app_name, version="0.1.0")
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins_list,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
app.mount("/uploads", StaticFiles(directory=settings.uploads_dir), name="uploads")
app.include_router(api_router, prefix=settings.api_v1_prefix)
register_exception_handlers(app)


@app.on_event("startup")
def ping_database_on_startup() -> None:
    with engine.connect() as connection:
        connection.execute(text("SELECT 1"))
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
