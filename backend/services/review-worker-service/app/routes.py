from __future__ import annotations

from fastapi import APIRouter
from pydantic import BaseModel, Field

from app.processor import process_review_event
from shared.kafka.events import ReviewEvent
from shared.kafka.topics import REVIEW_CREATED_TOPIC, REVIEW_DELETED_TOPIC, REVIEW_UPDATED_TOPIC

router = APIRouter()


class ReviewWorkerRequest(BaseModel):
    topic: str = Field(pattern="^(review\\.created|review\\.updated|review\\.deleted)$")
    event: ReviewEvent


@router.post("/internal/process-review-event")
def process_event(payload: ReviewWorkerRequest) -> dict:
    return process_review_event(payload.topic, payload.event.model_dump())


@router.get("/topics")
def topics() -> dict:
    return {
        "review_topics": [
            REVIEW_CREATED_TOPIC,
            REVIEW_UPDATED_TOPIC,
            REVIEW_DELETED_TOPIC,
        ]
    }
