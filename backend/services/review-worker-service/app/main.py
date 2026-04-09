from __future__ import annotations

import logging
import time
import threading

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.routes import router
from app.processor import process_review_event
from shared.db.mongo import ping_mongo
from shared.kafka.consumer import start_consumer
from shared.kafka.topics import REVIEW_CREATED_TOPIC, REVIEW_DELETED_TOPIC, REVIEW_UPDATED_TOPIC

logger = logging.getLogger(__name__)

app = FastAPI(title="Lab 2 Review Worker Service")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(router, prefix="/api/v1")


@app.get("/health")
def health() -> dict[str, str]:
    return {"status": "ok", "service": "review-worker-service"}


@app.on_event("startup")
def startup_check() -> None:
    try:
        ping_mongo()
        logger.info("review-worker-service: MongoDB ping OK.")
        
        def _run_worker():
            topics = [REVIEW_CREATED_TOPIC, REVIEW_UPDATED_TOPIC, REVIEW_DELETED_TOPIC]
            while True:
                try:
                    start_consumer(topics, process_review_event)
                except Exception as e:
                    logger.error("Consumer loop exited: %s. Retrying in 5s...", e)
                    time.sleep(5)

        thread = threading.Thread(target=_run_worker, daemon=True)
        thread.start()
        
    except Exception as exc:
        logger.warning("review-worker-service: MongoDB ping failed: %s", exc)
