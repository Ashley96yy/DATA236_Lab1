from __future__ import annotations

import logging

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.routes import router
from shared.db.mongo import ping_mongo

logger = logging.getLogger(__name__)

app = FastAPI(title="Lab 2 User Service")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(router)


@app.get("/health")
def health() -> dict[str, str]:
    return {"status": "ok", "service": "user-service"}


@app.on_event("startup")
def startup_check() -> None:
    try:
        ping_mongo()
        logger.info("user-service: MongoDB ping OK.")
    except Exception as exc:
        logger.warning("user-service: MongoDB ping failed: %s", exc)
