from __future__ import annotations

from fastapi import APIRouter, Depends, status

from app.deps import get_current_user
from app.repository import (
    get_restaurant_by_id,
    get_review_by_id,
    get_review_by_restaurant_and_user,
    reserve_next_review_id,
)
from app.schemas import ReviewCreate, ReviewEventAckResponse, ReviewUpdate
from shared.kafka.events import build_review_event
from shared.kafka.producer import publish_message
from shared.kafka.topics import REVIEW_CREATED_TOPIC, REVIEW_DELETED_TOPIC, REVIEW_UPDATED_TOPIC
from shared.utils import conflict, forbidden, not_found, service_unavailable

router = APIRouter()


@router.post("/restaurants/{restaurant_id}/reviews", response_model=ReviewEventAckResponse, status_code=status.HTTP_202_ACCEPTED)
def create(
    restaurant_id: int,
    payload: ReviewCreate,
    current_user: dict = Depends(get_current_user),
) -> ReviewEventAckResponse:
    if get_restaurant_by_id(restaurant_id) is None:
        raise not_found("Restaurant not found.")
    if get_review_by_restaurant_and_user(restaurant_id, int(current_user["_id"])) is not None:
        raise conflict("You have already reviewed this restaurant.")
    review_id = reserve_next_review_id()
    event = build_review_event(
        event_type="review.created",
        restaurant_id=restaurant_id,
        user_id=int(current_user["_id"]),
        rating=payload.rating,
        comment=payload.comment,
        review_id=review_id,
    )
    try:
        publish_message(REVIEW_CREATED_TOPIC, event.model_dump(mode="json"))
    except Exception as exc:
        raise service_unavailable(f"Kafka publish failed: {exc}")
    return ReviewEventAckResponse(status="queued", topic=REVIEW_CREATED_TOPIC, review_id=review_id, event_id=event.event_id)


@router.put("/reviews/{review_id}", response_model=ReviewEventAckResponse, status_code=status.HTTP_202_ACCEPTED)
def update(
    review_id: int,
    payload: ReviewUpdate,
    current_user: dict = Depends(get_current_user),
) -> ReviewEventAckResponse:
    review = get_review_by_id(review_id)
    if review is None:
        raise not_found("Review not found.")
    if int(review["user_id"]) != int(current_user["_id"]):
        raise forbidden("You can only edit your own review.")
    event = build_review_event(
        event_type="review.updated",
        restaurant_id=int(review["restaurant_id"]),
        user_id=int(current_user["_id"]),
        rating=payload.rating,
        comment=payload.comment,
        review_id=review_id,
    )
    try:
        publish_message(REVIEW_UPDATED_TOPIC, event.model_dump(mode="json"))
    except Exception as exc:
        raise service_unavailable(f"Kafka publish failed: {exc}")
    return ReviewEventAckResponse(status="queued", topic=REVIEW_UPDATED_TOPIC, review_id=review_id, event_id=event.event_id)


@router.delete("/reviews/{review_id}", response_model=ReviewEventAckResponse, status_code=status.HTTP_202_ACCEPTED)
def delete(review_id: int, current_user: dict = Depends(get_current_user)) -> ReviewEventAckResponse:
    review = get_review_by_id(review_id)
    if review is None:
        raise not_found("Review not found.")
    if int(review["user_id"]) != int(current_user["_id"]):
        raise forbidden("You can only delete your own review.")
    event = build_review_event(
        event_type="review.deleted",
        restaurant_id=int(review["restaurant_id"]),
        user_id=int(current_user["_id"]),
        review_id=review_id,
    )
    try:
        publish_message(REVIEW_DELETED_TOPIC, event.model_dump(mode="json"))
    except Exception as exc:
        raise service_unavailable(f"Kafka publish failed: {exc}")
    return ReviewEventAckResponse(status="queued", topic=REVIEW_DELETED_TOPIC, review_id=review_id, event_id=event.event_id)
