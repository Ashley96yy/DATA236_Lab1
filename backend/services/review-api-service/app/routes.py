from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException, Query, status

from app.deps import get_current_user
from app.repository import (
    create_review,
    delete_review,
    get_restaurant_by_id,
    get_review_by_id,
    get_review_by_restaurant_and_user,
    list_reviews_for_restaurant,
    update_review,
)
from app.schemas import ReviewCreate, ReviewListResponse, ReviewResponse, ReviewUpdate

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


@router.post("/restaurants/{restaurant_id}/reviews", response_model=ReviewResponse, status_code=status.HTTP_201_CREATED)
def create(
    restaurant_id: int,
    payload: ReviewCreate,
    current_user: dict = Depends(get_current_user),
) -> ReviewResponse:
    if get_restaurant_by_id(restaurant_id) is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Restaurant not found.")
    existing = get_review_by_restaurant_and_user(restaurant_id, int(current_user["_id"]))
    if existing is not None:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="You have already reviewed this restaurant.")
    review = create_review(
        restaurant_id=restaurant_id,
        user_id=int(current_user["_id"]),
        payload=payload.model_dump(exclude_none=True),
    )
    return _serialize_review(review, current_user["name"])


@router.get("/restaurants/{restaurant_id}/reviews", response_model=ReviewListResponse)
def list_for_restaurant(
    restaurant_id: int,
    page: int = Query(default=1, ge=1),
    limit: int = Query(default=20, ge=1, le=100),
) -> ReviewListResponse:
    result = list_reviews_for_restaurant(restaurant_id, page=page, limit=limit)
    items = []
    for review in result["items"]:
        user_name = "Unknown User"
        items.append(_serialize_review(review, user_name))
    return ReviewListResponse(items=items, total=result["total"], page=result["page"], limit=result["limit"])


@router.put("/reviews/{review_id}", response_model=ReviewResponse)
def update(
    review_id: int,
    payload: ReviewUpdate,
    current_user: dict = Depends(get_current_user),
) -> ReviewResponse:
    review = get_review_by_id(review_id)
    if review is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Review not found.")
    if int(review["user_id"]) != int(current_user["_id"]):
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="You can only edit your own review.")
    updated = update_review(review_id, payload.model_dump(exclude_none=True))
    return _serialize_review(updated, current_user["name"])


@router.delete("/reviews/{review_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete(review_id: int, current_user: dict = Depends(get_current_user)) -> None:
    review = get_review_by_id(review_id)
    if review is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Review not found.")
    if int(review["user_id"]) != int(current_user["_id"]):
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="You can only delete your own review.")
    delete_review(review_id)
