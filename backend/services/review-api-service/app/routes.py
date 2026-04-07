from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException, Query, status

from app.deps import get_current_user
from app.repository import (
    get_restaurant_by_id,
    get_review_by_id,
    get_review_by_restaurant_and_user,
    get_user_name,
    list_reviews_for_restaurant,
    reserve_next_review_id,
)
from app.schemas import ReviewCreate, ReviewEventAckResponse, ReviewListResponse, ReviewResponse, ReviewUpdate
from shared.kafka.events import build_review_event
from shared.kafka.producer import publish_message
from shared.kafka.topics import REVIEW_CREATED_TOPIC, REVIEW_DELETED_TOPIC, REVIEW_UPDATED_TOPIC

router = APIRouter()


def _serialize_review(review: dict, user_name: str) -> ReviewResponse:
    return ReviewResponse(
        id=int(review["_id"]),
        restaurant_id=int(review["restaurant_id"]),
        user_id=int(review["user_id"]),
        user_name=user_name,
        rating=int(review["rating"]),
        comment=review.get("comment"),
        status=review.get("status", "processed"),
        created_at=review["created_at"],
        updated_at=review["updated_at"],
    )


@router.post("/restaurants/{restaurant_id}/reviews", response_model=ReviewEventAckResponse, status_code=status.HTTP_202_ACCEPTED)
def create(
    restaurant_id: int,
    payload: ReviewCreate,
    current_user: dict = Depends(get_current_user),
) -> ReviewEventAckResponse:
    if get_restaurant_by_id(restaurant_id) is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Restaurant not found.")
    existing = get_review_by_restaurant_and_user(restaurant_id, int(current_user["_id"]))
    if existing is not None:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="You have already reviewed this restaurant.")
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
        raise HTTPException(status_code=status.HTTP_503_SERVICE_UNAVAILABLE, detail=f"Kafka publish failed: {exc}")
    return ReviewEventAckResponse(
        status="queued",
        topic=REVIEW_CREATED_TOPIC,
        review_id=review_id,
        event_id=event.event_id,
    )


@router.get("/restaurants/{restaurant_id}/reviews", response_model=ReviewListResponse)
def list_for_restaurant(
    restaurant_id: int,
    page: int = Query(default=1, ge=1),
    limit: int = Query(default=20, ge=1, le=100),
) -> ReviewListResponse:
    result = list_reviews_for_restaurant(restaurant_id, page=page, limit=limit)
    items = []
    for review in result["items"]:
        user_name = get_user_name(int(review["user_id"]))
        items.append(_serialize_review(review, user_name))
    return ReviewListResponse(items=items, total=result["total"], page=result["page"], limit=result["limit"])


@router.put("/reviews/{review_id}", response_model=ReviewEventAckResponse, status_code=status.HTTP_202_ACCEPTED)
def update(
    review_id: int,
    payload: ReviewUpdate,
    current_user: dict = Depends(get_current_user),
) -> ReviewEventAckResponse:
    review = get_review_by_id(review_id)
    if review is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Review not found.")
    if int(review["user_id"]) != int(current_user["_id"]):
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="You can only edit your own review.")
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
        raise HTTPException(status_code=status.HTTP_503_SERVICE_UNAVAILABLE, detail=f"Kafka publish failed: {exc}")
    return ReviewEventAckResponse(
        status="queued",
        topic=REVIEW_UPDATED_TOPIC,
        review_id=review_id,
        event_id=event.event_id,
    )


@router.delete("/reviews/{review_id}", response_model=ReviewEventAckResponse, status_code=status.HTTP_202_ACCEPTED)
def delete(review_id: int, current_user: dict = Depends(get_current_user)) -> ReviewEventAckResponse:
    review = get_review_by_id(review_id)
    if review is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Review not found.")
    if int(review["user_id"]) != int(current_user["_id"]):
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="You can only delete your own review.")
    event = build_review_event(
        event_type="review.deleted",
        restaurant_id=int(review["restaurant_id"]),
        user_id=int(current_user["_id"]),
        review_id=review_id,
    )
    try:
        publish_message(REVIEW_DELETED_TOPIC, event.model_dump(mode="json"))
    except Exception as exc:
        raise HTTPException(status_code=status.HTTP_503_SERVICE_UNAVAILABLE, detail=f"Kafka publish failed: {exc}")
    return ReviewEventAckResponse(
        status="queued",
        topic=REVIEW_DELETED_TOPIC,
        review_id=review_id,
        event_id=event.event_id,
    )
