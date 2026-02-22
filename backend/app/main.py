import logging

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from sqlalchemy import text
from sqlalchemy.exc import SQLAlchemyError

from app.api.v1.router import api_router
from app.core.config import get_settings
from app.core.errors import register_exception_handlers
from app.db.session import engine

settings = get_settings()
settings.uploads_dir.mkdir(parents=True, exist_ok=True)
logger = logging.getLogger(__name__)
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


@app.get("/health")
def health_root() -> dict[str, str]:
    return {"status": "ok"}


@app.on_event("startup")
def ping_database_on_startup() -> None:
    if not settings.startup_db_check_enabled:
        logger.info("Startup DB check skipped (STARTUP_DB_CHECK_ENABLED=false).")
        return

    try:
        with engine.connect() as connection:
            connection.execute(text("SELECT 1"))
        logger.info("Startup DB check passed.")
    except SQLAlchemyError as exc:
        logger.warning("Startup DB check failed: %s", exc)
        if settings.startup_db_check_strict:
            raise
