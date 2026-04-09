from __future__ import annotations

from app.repository import create_review_from_event, delete_review_from_event, update_review_from_event
from app.state import record_failure, record_processed
from shared.kafka.topics import REVIEW_CREATED_TOPIC, REVIEW_DELETED_TOPIC, REVIEW_UPDATED_TOPIC


def process_review_event(topic: str, payload: dict) -> dict:
    if topic == REVIEW_CREATED_TOPIC:
        review = create_review_from_event(payload)
        result = {"status": "processed", "operation": "create", "review_id": int(review["_id"])}
        record_processed(topic=topic, payload=payload, result=result)
        return result

    if topic == REVIEW_UPDATED_TOPIC:
        review = update_review_from_event(payload)
        if review is None:
            error = f"Review not found for update: review_id={payload.get('review_id')}"
            record_failure(topic=topic, payload=payload, error=error)
            raise ValueError(error)
        result = {"status": "processed", "operation": "update", "review_id": int(review["_id"])}
        record_processed(topic=topic, payload=payload, result=result)
        return result

    if topic == REVIEW_DELETED_TOPIC:
        deleted = delete_review_from_event(payload)
        if not deleted:
            error = f"Review not found for delete: review_id={payload.get('review_id')}"
            record_failure(topic=topic, payload=payload, error=error)
            raise ValueError(error)
        result = {"status": "processed", "operation": "delete", "review_id": int(payload["review_id"])}
        record_processed(topic=topic, payload=payload, result=result)
        return result

    error = f"Unsupported review topic: {topic}"
    record_failure(topic=topic, payload=payload, error=error)
    raise ValueError(error)
