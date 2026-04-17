from __future__ import annotations

import base64
import re

from fastapi import APIRouter, Depends, Query, status
from fastapi import File, UploadFile
from fastapi.security import OAuth2PasswordRequestForm

from app.deps import get_current_user
from app.repository import (
    add_favorite,
    create_user,
    get_favorite_by_user_and_restaurant,
    get_favorites_page,
    get_preferences,
    get_reviews_for_restaurant,
    get_user_by_id,
    get_user_by_email,
    get_user_history,
    list_restaurants_for_ai,
    remove_favorite,
    update_user_avatar,
    update_user_profile,
    update_preferences,
)
from app.schemas import (
    AiAssistantChatRequest,
    AiAssistantChatResponse,
    AiSuggestedRestaurant,
    AvatarUploadResponse,
    FavoritesListResponse,
    LoginResponse,
    SignupRequest,
    UserHistoryResponse,
    UserProfileUpdateRequest,
    UserPreferencesResponse,
    UserPreferencesUpdateRequest,
    UserResponse,
)
from shared.auth.security import create_access_token, verify_password
from shared.db.session_store import build_session_document, store_session
from shared.schemas import LoginRequest
from shared.utils import conflict, not_found, unauthorized

router = APIRouter()

COMMON_CUISINES = {
    "chinese",
    "japanese",
    "korean",
    "italian",
    "mexican",
    "indian",
    "thai",
    "spanish",
    "american",
    "vegan",
    "seafood",
    "mediterranean",
}
VIBE_KEYWORDS = {"quiet", "romantic", "casual", "cozy", "family", "vegan", "spicy"}


def _serialize_user(user: dict) -> UserResponse:
    raw_languages = user.get("languages", [])
    if isinstance(raw_languages, list):
        languages: str | list[str] | None = ", ".join(raw_languages)
    else:
        languages = raw_languages
    raw_gender = user.get("gender")
    normalized_gender = raw_gender.lower() if isinstance(raw_gender, str) else raw_gender
    if normalized_gender not in {"male", "female", "non_binary", "other", "prefer_not_to_say", None}:
        normalized_gender = None
    return UserResponse(
        id=int(user["_id"]),
        name=user["name"],
        email=user["email"],
        phone=user.get("phone"),
        about_me=user.get("about_me"),
        city=user.get("city"),
        state=user.get("state"),
        country=user.get("country"),
        languages=languages,
        gender=normalized_gender,
        avatar_url=user.get("avatar_url"),
    )


def _stringify_hours(hours: dict | None) -> str:
    if not hours:
        return "Hours not available."
    parts = []
    for day, value in hours.items():
        if value:
            parts.append(f"{day}: {value}")
    return " | ".join(parts) if parts else "Hours not available."


def _extract_query_preferences(message: str, restaurants: list[dict], stored_preferences: dict, current_user: dict) -> dict:
    lower = message.lower()
    cuisines = {r.get("cuisine_type", "").strip().lower() for r in restaurants if r.get("cuisine_type")}
    matched_cuisine = next((c for c in sorted(cuisines | COMMON_CUISINES, key=len, reverse=True) if c and c in lower), None)

    cities = {
        (r.get("address", {}) or {}).get("city", "").strip()
        for r in restaurants
        if (r.get("address", {}) or {}).get("city")
    }
    matched_city = next((city for city in cities if city and city.lower() in lower), None)
    if matched_city is None:
        preferred_locations = stored_preferences.get("preferred_locations") or []
        if preferred_locations:
            matched_city = preferred_locations[0]
        elif current_user.get("city"):
            matched_city = current_user["city"]

    matched_price = next((tier for tier in ("$$$$", "$$$", "$$", "$") if tier in message), None)
    if matched_price is None:
        matched_price = stored_preferences.get("price_range")

    keywords = [keyword for keyword in VIBE_KEYWORDS if keyword in lower]
    return {
        "cuisine": matched_cuisine,
        "city": matched_city,
        "price": matched_price,
        "keywords": keywords,
    }


def _rank_restaurants(restaurants: list[dict], preferences: dict, stored_preferences: dict) -> list[dict]:
    ranked = []
    preferred_cuisines = {c.lower() for c in (stored_preferences.get("cuisines") or [])}
    preferred_locations = {c.lower() for c in (stored_preferences.get("preferred_locations") or [])}
    for restaurant in restaurants:
        address = restaurant.get("address", {}) or {}
        cuisine = (restaurant.get("cuisine_type") or "").strip()
        city = (address.get("city") or "").strip()
        description = (restaurant.get("description") or "").lower()
        amenities = [str(item).lower() for item in restaurant.get("amenities") or []]

        reviews = get_reviews_for_restaurant(int(restaurant["_id"]))
        review_count = len(reviews)
        average_rating = round(
            sum(review.get("rating", 0) for review in reviews) / review_count,
            2,
        ) if review_count else 0.0

        score = average_rating * 20 + min(review_count, 20)
        reasons = []

        if preferences["cuisine"] and cuisine.lower() == preferences["cuisine"]:
            score += 60
            reasons.append("Matches your cuisine request")
        elif cuisine.lower() in preferred_cuisines:
            score += 25
            reasons.append("Matches your saved cuisine preference")

        if preferences["city"] and city.lower() == preferences["city"].lower():
            score += 40
            reasons.append(f"In your requested area ({city})")
        elif city.lower() in preferred_locations:
            score += 20
            reasons.append(f"In one of your preferred locations ({city})")

        if preferences["price"] and restaurant.get("pricing_tier") == preferences["price"]:
            score += 25
            reasons.append(f"Within your requested budget ({preferences['price']})")

        for keyword in preferences["keywords"]:
            if keyword in description or keyword in amenities or keyword in cuisine.lower():
                score += 8
                reasons.append(f"Related to '{keyword}'")

        ranked.append(
            {
                "id": int(restaurant["_id"]),
                "name": restaurant["name"],
                "cuisine_type": restaurant.get("cuisine_type"),
                "pricing_tier": restaurant.get("pricing_tier"),
                "average_rating": average_rating,
                "hours": restaurant.get("hours") or {},
                "score": score,
                "reason": "; ".join(dict.fromkeys(reasons)) or "Strong overall rating and review activity",
            }
        )

    ranked.sort(key=lambda item: (-item["score"], item["name"].lower()))
    return ranked[:3]


def _build_ai_response(current_user: dict, payload: AiAssistantChatRequest) -> AiAssistantChatResponse:
    restaurants = list_restaurants_for_ai()
    stored_preferences = get_preferences(int(current_user["_id"]))
    effective_message = payload.message
    lower = payload.message.lower()
    is_hours_followup = "hour" in lower and "first" in lower

    if is_hours_followup:
        previous_user_messages = [
            turn.content
            for turn in payload.conversation_history
            if turn.role == "user" and turn.content.strip()
        ]
        if previous_user_messages:
            effective_message = previous_user_messages[-1]

    extracted = _extract_query_preferences(effective_message, restaurants, stored_preferences, current_user)
    suggestions = _rank_restaurants(restaurants, extracted, stored_preferences)

    if not suggestions:
        return AiAssistantChatResponse(
            reply="I could not find a strong match yet. Try adding a cuisine, budget, or city.",
            suggested_restaurants=[],
        )

    if is_hours_followup:
        top = suggestions[0]
        return AiAssistantChatResponse(
            reply=f"{top['name']} hours: {_stringify_hours(top['hours'])}",
            suggested_restaurants=[
                AiSuggestedRestaurant(
                    id=top["id"],
                    name=top["name"],
                    cuisine_type=top["cuisine_type"],
                    pricing_tier=top["pricing_tier"],
                    average_rating=top["average_rating"],
                    reason="Open-hours details for your selected restaurant",
                )
            ],
        )

    reply_lines = ["Here are top matches based on your preferences and query:"]
    for index, item in enumerate(suggestions, start=1):
        meta_bits = [item["name"]]
        if item["average_rating"]:
            meta_bits.append(f"{item['average_rating']:.1f}★")
        if item["pricing_tier"]:
            meta_bits.append(item["pricing_tier"])
        reply_lines.append(f"{index}. {' '.join(meta_bits)} - {item['reason']}")

    return AiAssistantChatResponse(
        reply="\n".join(reply_lines),
        suggested_restaurants=[
            AiSuggestedRestaurant(
                id=item["id"],
                name=item["name"],
                cuisine_type=item["cuisine_type"],
                pricing_tier=item["pricing_tier"],
                average_rating=item["average_rating"],
                reason=item["reason"],
            )
            for item in suggestions
        ],
    )


@router.post("/auth/signup", response_model=UserResponse, status_code=status.HTTP_201_CREATED)
def signup(payload: SignupRequest) -> UserResponse:
    if get_user_by_email(payload.email) is not None:
        raise conflict("Email already exists.")
    user = create_user(name=payload.name, email=payload.email, password=payload.password)
    return _serialize_user(user)


@router.post("/auth/login", response_model=LoginResponse)
def login(payload: LoginRequest) -> LoginResponse:
    user = get_user_by_email(payload.email)
    if user is None or not verify_password(payload.password, user["password_hash"]):
        raise unauthorized("Invalid email or password.")
    token = create_access_token(subject=str(user["_id"]), token_type="user")
    store_session(build_session_document(subject_id=int(user["_id"]), role="user", token=token))
    return LoginResponse(access_token=token, user=_serialize_user(user))


@router.post("/auth/token", response_model=LoginResponse, include_in_schema=False)
def login_token(form_data: OAuth2PasswordRequestForm = Depends()) -> LoginResponse:
    return login(LoginRequest(email=form_data.username, password=form_data.password))


@router.get("/auth/me", response_model=UserResponse)
def read_auth_me(current_user: dict = Depends(get_current_user)) -> UserResponse:
    return _serialize_user(current_user)


@router.get("/users/me", response_model=UserResponse)
def read_me(current_user: dict = Depends(get_current_user)) -> UserResponse:
    return _serialize_user(current_user)


@router.put("/users/me", response_model=UserResponse)
def update_me(
    payload: UserProfileUpdateRequest,
    current_user: dict = Depends(get_current_user),
) -> UserResponse:
    user = update_user_profile(int(current_user["_id"]), payload.model_dump(exclude_none=True))
    return _serialize_user(user)


@router.post("/users/me/avatar", response_model=AvatarUploadResponse)
async def upload_avatar(
    file: UploadFile = File(...),
    current_user: dict = Depends(get_current_user),
) -> AvatarUploadResponse:
    raw = await file.read()
    if not raw:
        raise conflict("Uploaded file is empty.")
    content_type = file.content_type or "image/jpeg"
    encoded = base64.b64encode(raw).decode("utf-8")
    avatar_url = f"data:{content_type};base64,{encoded}"
    update_user_avatar(int(current_user["_id"]), avatar_url)
    return AvatarUploadResponse(avatar_url=avatar_url)


@router.get("/users/me/preferences", response_model=UserPreferencesResponse)
def read_preferences(current_user: dict = Depends(get_current_user)) -> UserPreferencesResponse:
    return UserPreferencesResponse(**get_preferences(int(current_user["_id"])))


@router.put("/users/me/preferences", response_model=UserPreferencesResponse)
def save_preferences(
    payload: UserPreferencesUpdateRequest,
    current_user: dict = Depends(get_current_user),
) -> UserPreferencesResponse:
    return UserPreferencesResponse(
        **update_preferences(int(current_user["_id"]), payload.model_dump(exclude_none=True))
    )


@router.get("/users/me/favorites", response_model=FavoritesListResponse)
def list_favorites(
    page: int = Query(default=1, ge=1),
    limit: int = Query(default=20, ge=1, le=100),
    current_user: dict = Depends(get_current_user),
) -> FavoritesListResponse:
    return FavoritesListResponse(**get_favorites_page(int(current_user["_id"]), page=page, limit=limit))


@router.post("/users/me/favorites/{restaurant_id}", status_code=status.HTTP_201_CREATED)
def add_to_favorites(
    restaurant_id: int,
    current_user: dict = Depends(get_current_user),
) -> dict:
    if get_favorite_by_user_and_restaurant(int(current_user["_id"]), restaurant_id) is not None:
        raise conflict("Already in favorites.")
    add_favorite(int(current_user["_id"]), restaurant_id)
    return {"status": "added", "restaurant_id": restaurant_id}


@router.post("/favorites/{restaurant_id}", status_code=status.HTTP_201_CREATED)
def add_to_favorites_shortcut(
    restaurant_id: int,
    current_user: dict = Depends(get_current_user),
) -> dict:
    return add_to_favorites(restaurant_id=restaurant_id, current_user=current_user)


@router.delete("/users/me/favorites/{restaurant_id}", status_code=status.HTTP_204_NO_CONTENT)
def remove_from_favorites(
    restaurant_id: int,
    current_user: dict = Depends(get_current_user),
) -> None:
    if not remove_favorite(int(current_user["_id"]), restaurant_id):
        raise not_found("Favorite not found.")


@router.delete("/favorites/{restaurant_id}", status_code=status.HTTP_204_NO_CONTENT)
def remove_from_favorites_shortcut(
    restaurant_id: int,
    current_user: dict = Depends(get_current_user),
) -> None:
    remove_from_favorites(restaurant_id=restaurant_id, current_user=current_user)


@router.get("/users/me/history", response_model=UserHistoryResponse)
def user_history(current_user: dict = Depends(get_current_user)) -> UserHistoryResponse:
    return UserHistoryResponse(**get_user_history(int(current_user["_id"])))


@router.post("/ai-assistant/chat", response_model=AiAssistantChatResponse)
def chat_with_ai(
    payload: AiAssistantChatRequest,
    current_user: dict = Depends(get_current_user),
) -> AiAssistantChatResponse:
    return _build_ai_response(current_user, payload)
