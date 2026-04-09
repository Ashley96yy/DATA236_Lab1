from __future__ import annotations

import base64

from fastapi import APIRouter, Depends, File, Query, UploadFile, status

from app.deps import get_current_actor, get_current_user
from app.repository import (
    add_restaurant_photos,
    create_restaurant,
    get_restaurant_by_id,
    get_owner_by_id,
    get_restaurant_photos,
    get_restaurant_reviews,
    get_user_name,
    list_reviews_paginated,
    search_restaurants,
)
from app.schemas import (
    RestaurantCard,
    RestaurantCreate,
    RestaurantPhotoResponse,
    RestaurantResponse,
    RestaurantSearchResponse,
    ReviewListResponse,
    ReviewResponse,
)

from shared.utils import bad_request, forbidden, not_found

router = APIRouter()


def _serialize_restaurant(document: dict) -> RestaurantResponse:
    address = document.get("address", {})
    photos = get_restaurant_photos(int(document["_id"]))
    reviews = get_restaurant_reviews(int(document["_id"]))
    review_count = len(reviews)
    average_rating = round(sum(r.get("rating", 0) for r in reviews) / review_count, 2) if review_count else 0.0

    return RestaurantResponse(
        id=int(document["_id"]),
        name=document["name"],
        cuisine_type=document.get("cuisine_type"),
        description=document.get("description"),
        street=address.get("street"),
        city=address.get("city"),
        state=address.get("state"),
        zip_code=address.get("zip_code"),
        country=address.get("country"),
        latitude=document.get("latitude"),
        longitude=document.get("longitude"),
        phone=document.get("phone"),
        email=document.get("email"),
        hours=document.get("hours", {}),
        pricing_tier=document.get("pricing_tier"),
        amenities=document.get("amenities", []),
        created_by_user_id=document.get("created_by_user_id"),
        claimed_by_owner_id=document.get("claimed_by_owner_id"),
        average_rating=average_rating,
        review_count=review_count,
        photos=[
            RestaurantPhotoResponse(
                id=int(photo["_id"]),
                photo_url=photo["photo_url"],
                uploaded_by_user_id=photo.get("uploaded_by_user_id"),
                uploaded_by_owner_id=photo.get("uploaded_by_owner_id"),
            )
            for photo in photos
        ],
    )


@router.post("/restaurants", response_model=RestaurantResponse, status_code=status.HTTP_201_CREATED)
def create(payload: RestaurantCreate, current_user: dict = Depends(get_current_user)) -> RestaurantResponse:
    restaurant = create_restaurant(
        payload=payload.model_dump(exclude_none=True),
        created_by_user_id=int(current_user["_id"]),
    )
    return _serialize_restaurant(restaurant)


@router.get("/restaurants", response_model=RestaurantSearchResponse)
def search(
    name: str | None = Query(default=None),
    cuisine: str | None = Query(default=None),
    keywords: str | None = Query(default=None),
    city: str | None = Query(default=None),
    zip: str | None = Query(default=None),
    sort: str = Query(default="name", pattern="^(rating|review_count|name)$"),
    page: int = Query(default=1, ge=1),
    limit: int = Query(default=10, ge=1, le=50),
) -> RestaurantSearchResponse:
    result = search_restaurants(
        name=name,
        cuisine=cuisine,
        keywords=keywords,
        city=city,
        zip_code=zip,
        sort=sort,
        page=page,
        limit=limit,
    )
    items = []
    for document in result["items"]:
        address = document.get("address", {})
        items.append(
            RestaurantCard(
                id=int(document["_id"]),
                name=document["name"],
                cuisine_type=document.get("cuisine_type"),
                description=document.get("description"),
                city=address.get("city"),
                state=address.get("state"),
                pricing_tier=document.get("pricing_tier"),
                amenities=document.get("amenities", []),
                average_rating=document.get("average_rating", 0.0),
                review_count=document.get("review_count", 0),
                cover_photo_url=document.get("cover_photo_url"),
            )
        )
    return RestaurantSearchResponse(items=items, total=result["total"], page=result["page"], limit=result["limit"])


@router.get("/restaurants/{restaurant_id}", response_model=RestaurantResponse)
def read_detail(restaurant_id: int) -> RestaurantResponse:
    restaurant = get_restaurant_by_id(restaurant_id)
    if restaurant is None:
        raise not_found("Restaurant not found.")
    return _serialize_restaurant(restaurant)


@router.get("/restaurants/{restaurant_id}/reviews", response_model=ReviewListResponse)
def read_reviews(
    restaurant_id: int,
    page: int = Query(default=1, ge=1),
    limit: int = Query(default=20, ge=1, le=100),
) -> ReviewListResponse:
    if get_restaurant_by_id(restaurant_id) is None:
        raise not_found("Restaurant not found.")
    result = list_reviews_paginated(restaurant_id, page=page, limit=limit)
    items = []
    for review in result["items"]:
        items.append(ReviewResponse(
            id=int(review["_id"]),
            restaurant_id=int(review["restaurant_id"]),
            user_id=int(review["user_id"]),
            user_name=get_user_name(int(review["user_id"])),
            rating=int(review["rating"]),
            comment=review.get("comment"),
            status=review.get("status", "processed"),
            created_at=review["created_at"],
            updated_at=review["updated_at"],
        ))
    return ReviewListResponse(items=items, total=result["total"], page=result["page"], limit=result["limit"])


@router.get("/restaurants/{restaurant_id}/photos", response_model=list[RestaurantPhotoResponse])
def read_photos(restaurant_id: int) -> list[RestaurantPhotoResponse]:
    if get_restaurant_by_id(restaurant_id) is None:
        raise not_found("Restaurant not found.")
    photos = get_restaurant_photos(restaurant_id)
    return [
        RestaurantPhotoResponse(
            id=int(photo["_id"]),
            photo_url=photo["photo_url"],
            uploaded_by_user_id=photo.get("uploaded_by_user_id"),
            uploaded_by_owner_id=photo.get("uploaded_by_owner_id"),
        )
        for photo in photos
    ]


@router.post("/restaurants/{restaurant_id}/photos", response_model=list[RestaurantPhotoResponse], status_code=status.HTTP_201_CREATED)
async def upload_photos(
    restaurant_id: int,
    files: list[UploadFile] = File(...),
    current_actor: dict = Depends(get_current_actor),
) -> list[RestaurantPhotoResponse]:
    restaurant = get_restaurant_by_id(restaurant_id)
    if restaurant is None:
        raise not_found("Restaurant not found.")

    actor_id = int(current_actor["id"])
    if current_actor["role"] == "user":
        if int(restaurant.get("created_by_user_id") or 0) != actor_id:
            raise forbidden("You can only upload photos for restaurants you created.")
        uploaded_by_user_id = actor_id
        uploaded_by_owner_id = None
    else:
        if int(restaurant.get("claimed_by_owner_id") or 0) != actor_id:
            raise forbidden("You can only upload photos for restaurants you manage.")
        uploaded_by_user_id = None
        uploaded_by_owner_id = actor_id

    photo_urls = []
    for file in files:
        raw = await file.read()
        if not raw:
            continue
        content_type = file.content_type or "image/jpeg"
        if not content_type.startswith("image/"):
            raise bad_request("Only image uploads are supported.")
        encoded = base64.b64encode(raw).decode("utf-8")
        photo_urls.append(f"data:{content_type};base64,{encoded}")

    if not photo_urls:
        raise bad_request("No valid image files were uploaded.")

    photos = add_restaurant_photos(
        restaurant_id,
        photo_urls,
        uploaded_by_user_id=uploaded_by_user_id,
        uploaded_by_owner_id=uploaded_by_owner_id,
    )
    return [
        RestaurantPhotoResponse(
            id=int(photo["_id"]),
            photo_url=photo["photo_url"],
            uploaded_by_user_id=photo.get("uploaded_by_user_id"),
            uploaded_by_owner_id=photo.get("uploaded_by_owner_id"),
        )
        for photo in photos
    ]
