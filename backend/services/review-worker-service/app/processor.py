from __future__ import annotations

from fastapi import HTTPException, status

from app.repository import create_review_from_event, delete_review_from_event, update_review_from_event
from shared.kafka.topics import REVIEW_CREATED_TOPIC, REVIEW_DELETED_TOPIC, REVIEW_UPDATED_TOPIC


def process_review_event(topic: str, payload: dict) -> dict:
    if topic == REVIEW_CREATED_TOPIC:
        review = create_review_from_event(payload)
        return {"status": "processed", "operation": "create", "review_id": int(review["_id"])}

    if topic == REVIEW_UPDATED_TOPIC:
        review = update_review_from_event(payload)
        if review is None:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Review not found for update.")
        return {"status": "processed", "operation": "update", "review_id": int(review["_id"])}

    if topic == REVIEW_DELETED_TOPIC:
        deleted = delete_review_from_event(payload)
        if not deleted:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Review not found for delete.")
        return {"status": "processed", "operation": "delete", "review_id": int(payload["review_id"])}

    raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Unsupported review topic.")
