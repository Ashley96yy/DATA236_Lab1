from __future__ import annotations

import json
import re
from typing import Any

from sqlalchemy import String, cast, or_, select
from sqlalchemy.orm import Session, selectinload

from app.core.config import get_settings
from app.models.restaurant import Restaurant
from app.models.user_preference import UserPreference
from app.schemas.ai_assistant import AIChatResponse, ConversationTurn, SuggestedRestaurant
from app.services.errors import ServiceBadRequest
from app.services.restaurant_service import _fetch_ratings

settings = get_settings()

_PRICE_SET = {"$", "$$", "$$$", "$$$$"}
_DEFAULT_CUISINES = {
    "american",
    "chinese",
    "french",
    "indian",
    "italian",
    "japanese",
    "korean",
    "mediterranean",
    "mexican",
    "thai",
    "vietnamese",
}
_DEFAULT_DIETARY = {
    "vegetarian",
    "vegan",
    "halal",
    "gluten-free",
    "gluten free",
    "kosher",
    "keto",
    "dairy-free",
    "dairy free",
}
_DEFAULT_AMBIANCE = {
    "casual",
    "fine dining",
    "family-friendly",
    "family friendly",
    "romantic",
    "quiet",
    "trendy",
    "outdoor",
}
_STOP_WORDS = {
    "a",
    "an",
    "and",
    "at",
    "best",
    "by",
    "for",
    "from",
    "i",
    "in",
    "is",
    "it",
    "me",
    "near",
    "of",
    "on",
    "place",
    "please",
    "recommend",
    "restaurant",
    "restaurants",
    "show",
    "suggest",
    "something",
    "the",
    "to",
    "find",
    "want",
    "with",
}
_LOCATION_FOLLOWUP_TOKENS = {"where", "location", "located", "address"}
_HOURS_FOLLOWUP_TOKENS = {"hour", "hours", "open", "opening", "close", "closing", "time", "schedule"}
_CONTACT_FOLLOWUP_TOKENS = {"contact", "phone", "number", "call", "email"}
_PRICE_FOLLOWUP_TOKENS = {"price", "cost", "expensive", "cheap", "budget", "$"}
_RATING_FOLLOWUP_TOKENS = {"rating", "rated", "stars", "star", "score", "average"}
_CUISINE_FOLLOWUP_TOKENS = {"cuisine", "food", "dish", "dishes"}
_AMENITY_FOLLOWUP_TOKENS = {
    "amenity",
    "amenities",
    "parking",
    "wifi",
    "outdoor",
    "patio",
    "vegan",
    "vegetarian",
    "halal",
    "romantic",
    "family",
    "casual",
    "quiet",
    "trendy",
}
_FOLLOWUP_TOPIC_ORDER: list[tuple[str, set[str]]] = [
    ("hours", _HOURS_FOLLOWUP_TOKENS),
    ("location", _LOCATION_FOLLOWUP_TOKENS),
    ("contact", _CONTACT_FOLLOWUP_TOKENS),
    ("rating", _RATING_FOLLOWUP_TOKENS),
    ("price", _PRICE_FOLLOWUP_TOKENS),
    ("amenities", _AMENITY_FOLLOWUP_TOKENS),
    ("cuisine", _CUISINE_FOLLOWUP_TOKENS),
]
_PRONOUN_FOLLOWUP_TOKENS = {
    "it",
    "its",
    "that",
    "this",
    "one",
    "ones",
}
_ORDINAL_HINTS = {
    "first": 0,
    "1st": 0,
    "second": 1,
    "2nd": 1,
    "third": 2,
    "3rd": 2,
}
_NEW_SEARCH_HINTS = {"recommend", "suggest", "find", "show", "search", "looking for", "i want"}


def generate_chat_response(
    db: Session,
    user_id: int,
    message: str,
    conversation_history: list[ConversationTurn],
) -> AIChatResponse:
    clean_message = message.strip()
    if not clean_message:
        raise ServiceBadRequest("Message cannot be empty.")

    preferences = _load_user_preferences(db, user_id)
    followup = _handle_attribute_followup(
        db=db,
        message=clean_message,
        conversation_history=conversation_history,
        preferences=preferences,
    )
    if followup is not None:
        return followup

    intent = _extract_intent(clean_message, conversation_history, preferences)
    ranked = _search_and_rank_restaurants(db, intent, preferences)

    top_ranked = ranked[:5]
    tavily_context = _fetch_tavily_context(top_ranked, intent)

    suggestions = [
        _build_suggestion(item, tavily_context.get(item["restaurant"].id, []))
        for item in top_ranked
    ]
    reply = _build_reply(
        message=clean_message,
        conversation_history=conversation_history,
        preferences=preferences,
        intent=intent,
        suggestions=suggestions,
        tavily_context=tavily_context,
    )
    return AIChatResponse(reply=reply, suggested_restaurants=suggestions)


def _handle_attribute_followup(
    db: Session,
    message: str,
    conversation_history: list[ConversationTurn],
    preferences: dict[str, Any],
) -> AIChatResponse | None:
    followup_type = _detect_followup_type(message)
    ranked_names = _extract_latest_ranked_names(db, conversation_history)
    if not ranked_names:
        ranked_names = _infer_context_names_from_previous_user_query(
            db=db,
            conversation_history=conversation_history,
            preferences=preferences,
        )

    if _looks_like_new_search_request(message):
        return None

    # If user asks a follow-up attribute question but we can't resolve context,
    # ask clarification instead of silently falling back to global re-ranking.
    if followup_type is not None and not ranked_names:
        return AIChatResponse(
            reply=(
                "I can help with that, but I need the target restaurant first. "
                "Please mention the name, or ask for a new recommendation."
            ),
            suggested_restaurants=[],
        )

    if not ranked_names:
        return None

    has_reference_hint = _has_reference_hint(message, ranked_names)
    if followup_type is None and not has_reference_hint:
        return None

    referenced_name = _extract_referenced_restaurant_name(message, ranked_names)
    if not referenced_name and followup_type is not None and len(ranked_names) == 1:
        referenced_name = ranked_names[0]
    if not referenced_name:
        reply = _build_followup_clarification_reply(ranked_names)
        suggestions = _build_followup_suggestions(db, ranked_names[:3])
        return AIChatResponse(reply=reply, suggested_restaurants=suggestions)

    restaurant = db.execute(
        select(Restaurant)
        .options(selectinload(Restaurant.photos))
        .where(Restaurant.name.ilike(referenced_name.strip()))
        .limit(1)
    ).scalar_one_or_none()
    if restaurant is None:
        reply = _build_followup_clarification_reply(ranked_names)
        suggestions = _build_followup_suggestions(db, ranked_names[:3])
        return AIChatResponse(reply=reply, suggested_restaurants=suggestions)

    avg_rating, review_count = _fetch_ratings(db, [restaurant.id]).get(restaurant.id, (0.0, 0))
    if followup_type is None:
        followup_type = "summary"
    reply, reason = _build_attribute_followup_reply(
        restaurant=restaurant,
        followup_type=followup_type,
        average_rating=avg_rating,
        review_count=review_count,
    )

    suggestion = SuggestedRestaurant(
        id=restaurant.id,
        name=restaurant.name,
        reason=reason,
        average_rating=avg_rating,
        pricing_tier=restaurant.pricing_tier,
        cuisine_type=restaurant.cuisine_type,
        city=restaurant.city,
    )
    return AIChatResponse(reply=reply, suggested_restaurants=[suggestion])


def _detect_followup_type(message: str) -> str | None:
    lowered = message.lower()
    for topic, tokens in _FOLLOWUP_TOPIC_ORDER:
        if any(token in lowered for token in tokens):
            return topic
    return None


def _build_attribute_followup_reply(
    *,
    restaurant: Restaurant,
    followup_type: str,
    average_rating: float,
    review_count: int,
) -> tuple[str, str]:
    if followup_type == "hours":
        return _build_hours_followup_reply(restaurant), "Open-hours details for your selected restaurant"
    if followup_type == "location":
        return _build_location_followup_reply(restaurant), "Location details for your selected restaurant"
    if followup_type == "contact":
        return _build_contact_followup_reply(restaurant), "Contact details for your selected restaurant"
    if followup_type == "rating":
        return (
            _build_rating_followup_reply(restaurant, average_rating, review_count),
            "Rating details for your selected restaurant",
        )
    if followup_type == "price":
        return _build_price_followup_reply(restaurant), "Pricing details for your selected restaurant"
    if followup_type == "amenities":
        return _build_amenities_followup_reply(restaurant), "Amenities details for your selected restaurant"
    if followup_type == "cuisine":
        return _build_cuisine_followup_reply(restaurant), "Cuisine details for your selected restaurant"
    return _build_summary_followup_reply(restaurant), "Details for your selected restaurant"


def _build_location_followup_reply(restaurant: Restaurant) -> str:
    location_parts = [
        part.strip()
        for part in (
            restaurant.street,
            restaurant.city,
            restaurant.state,
            restaurant.zip_code,
        )
        if part and str(part).strip()
    ]
    if location_parts:
        location_text = ", ".join(location_parts)
        return f"{restaurant.name} is located in {location_text}."
    if restaurant.city:
        return f"{restaurant.name} is in {restaurant.city}."
    return f"I couldn't find a full location for {restaurant.name}, but you can open its detail card."


def _build_hours_followup_reply(restaurant: Restaurant) -> str:
    if isinstance(restaurant.hours_json, dict) and restaurant.hours_json:
        pairs = [
            f"{str(day).title()}: {str(hours)}"
            for day, hours in restaurant.hours_json.items()
            if day and str(hours).strip()
        ]
        if pairs:
            return f"{restaurant.name} hours: " + " | ".join(pairs[:7])

    tavily_hours = _fetch_tavily_hours_hint(restaurant)
    if tavily_hours:
        return f"I don't have structured hours in our DB, but live context suggests: {tavily_hours}"
    return (
        f"I couldn't find reliable open hours for {restaurant.name} in our local data. "
        "Please check the official listing before visiting."
    )


def _build_contact_followup_reply(restaurant: Restaurant) -> str:
    contact_bits: list[str] = []
    if restaurant.phone:
        contact_bits.append(f"phone: {restaurant.phone}")
    if restaurant.email:
        contact_bits.append(f"email: {restaurant.email}")
    if contact_bits:
        return f"{restaurant.name} contact info: " + " | ".join(contact_bits)
    return f"I couldn't find direct contact details for {restaurant.name} in our local data."


def _build_rating_followup_reply(
    restaurant: Restaurant,
    average_rating: float,
    review_count: int,
) -> str:
    if review_count > 0:
        return (
            f"{restaurant.name} currently averages {average_rating:.1f}★ "
            f"from {review_count} review(s)."
        )
    return f"{restaurant.name} does not have ratings yet."


def _build_price_followup_reply(restaurant: Restaurant) -> str:
    if restaurant.pricing_tier:
        return f"{restaurant.name} is in the {restaurant.pricing_tier} price tier."
    return f"I don't have pricing tier data for {restaurant.name} yet."


def _build_cuisine_followup_reply(restaurant: Restaurant) -> str:
    if restaurant.cuisine_type:
        return f"{restaurant.name} serves {restaurant.cuisine_type} cuisine."
    return f"I don't have a cuisine label recorded for {restaurant.name}."


def _build_amenities_followup_reply(restaurant: Restaurant) -> str:
    raw = restaurant.amenities
    if isinstance(raw, list):
        amenities = [str(item).strip() for item in raw if str(item).strip()]
        if amenities:
            return f"{restaurant.name} amenities: " + ", ".join(amenities[:8])
    text_bits = [bit for bit in [restaurant.description, restaurant.cuisine_type] if bit]
    if text_bits:
        return (
            f"I don't have structured amenities for {restaurant.name}, but here's what I know: "
            + " ".join(text_bits)
        )
    return f"I don't have amenities data for {restaurant.name} yet."


def _build_summary_followup_reply(restaurant: Restaurant) -> str:
    location = restaurant.city or "unknown location"
    cuisine = restaurant.cuisine_type or "unspecified cuisine"
    price = restaurant.pricing_tier or "unknown price tier"
    return (
        f"{restaurant.name}: {cuisine}, {price}, in {location}. "
        "You can ask me for its location, open hours, contact, price, or amenities."
    )


def _fetch_tavily_hours_hint(restaurant: Restaurant) -> str | None:
    if not settings.tavily_api_key:
        return None
    try:
        from tavily import TavilyClient
    except Exception:
        return None

    client = TavilyClient(api_key=settings.tavily_api_key)
    city_hint = restaurant.city or ""
    query = f"{restaurant.name} {city_hint} opening hours"
    try:
        result = client.search(query=query, max_results=1, search_depth="basic")
    except Exception:
        return None

    row = ((result or {}).get("results") or [None])[0]
    if not isinstance(row, dict):
        return None

    title = str(row.get("title", "")).strip()
    content = str(row.get("content", "")).strip()
    merged = f"{title}: {content}".strip(": ").strip()
    return _truncate(merged, 220) if merged else None


def _extract_referenced_restaurant_name(
    message: str,
    ranked_names: list[str],
) -> str | None:
    lowered = message.lower()
    for name in ranked_names:
        if name.lower() in lowered:
            return name

    for token, index in _ORDINAL_HINTS.items():
        if token in lowered and index < len(ranked_names):
            return ranked_names[index]

    if "last" in lowered and ranked_names:
        return ranked_names[-1]
    if ("top" in lowered or "best" in lowered) and ranked_names:
        return ranked_names[0]

    if any(token in lowered for token in _PRONOUN_FOLLOWUP_TOKENS):
        return ranked_names[0]
    return None


def _extract_latest_ranked_names(
    db: Session,
    conversation_history: list[ConversationTurn],
) -> list[str]:
    assistant_message = next(
        (turn.content for turn in reversed(conversation_history) if turn.role == "assistant"),
        "",
    )
    if not assistant_message:
        return []
    ranked = _extract_ranked_names(assistant_message)
    if ranked:
        return ranked
    return _extract_mentioned_restaurant_names(db, assistant_message)


def _infer_context_names_from_previous_user_query(
    db: Session,
    conversation_history: list[ConversationTurn],
    preferences: dict[str, Any],
) -> list[str]:
    previous_user_message = next(
        (turn.content for turn in reversed(conversation_history) if turn.role == "user"),
        "",
    )
    if not previous_user_message.strip():
        return []

    # Reconstruct likely candidates from the last search-like user message.
    intent = _extract_intent_heuristic(previous_user_message, preferences)
    has_structured_filters = bool(
        intent.get("cuisines")
        or intent.get("location")
        or intent.get("price_range")
        or intent.get("dietary_needs")
        or intent.get("ambiance")
    )
    if not has_structured_filters:
        return []

    ranked = _search_and_rank_restaurants(db, intent, preferences)
    names: list[str] = []
    for row in ranked[:3]:
        restaurant = row.get("restaurant")
        if restaurant and getattr(restaurant, "name", None):
            names.append(str(restaurant.name))
    return names


def _extract_mentioned_restaurant_names(db: Session, text: str, max_names: int = 5) -> list[str]:
    lowered = text.lower()
    if not lowered.strip():
        return []

    names = db.execute(
        select(Restaurant.name).where(Restaurant.name.is_not(None)).limit(500)
    ).scalars().all()
    matches: list[tuple[int, int, str]] = []
    for raw_name in names:
        name = str(raw_name or "").strip()
        if not name:
            continue
        idx = lowered.find(name.lower())
        if idx >= 0:
            matches.append((idx, -len(name), name))
    if not matches:
        return []
    matches.sort()
    deduped: list[str] = []
    seen: set[str] = set()
    for _, _, name in matches:
        key = name.lower()
        if key in seen:
            continue
        seen.add(key)
        deduped.append(name)
        if len(deduped) >= max_names:
            break
    return deduped


def _has_reference_hint(message: str, ranked_names: list[str]) -> bool:
    lowered = message.lower()
    if any(name.lower() in lowered for name in ranked_names):
        return True
    if any(token in lowered for token in _PRONOUN_FOLLOWUP_TOKENS):
        return True
    if any(token in lowered for token in _ORDINAL_HINTS):
        return True
    return "last one" in lowered or "that one" in lowered or "this one" in lowered


def _looks_like_new_search_request(message: str) -> bool:
    lowered = message.lower()
    has_search_verb = any(token in lowered for token in _NEW_SEARCH_HINTS)
    has_reference = any(token in lowered for token in _PRONOUN_FOLLOWUP_TOKENS) or any(
        token in lowered for token in _ORDINAL_HINTS
    )
    return has_search_verb and not has_reference


def _build_followup_clarification_reply(ranked_names: list[str]) -> str:
    if not ranked_names:
        return (
            "Could you tell me which restaurant you mean? "
            "You can mention the name or say first/second."
        )
    short_list = ", ".join(ranked_names[:3])
    return (
        "I can help with details, but I need the target restaurant. "
        f"Do you mean: {short_list}? You can say first/second or the exact name."
    )


def _build_followup_suggestions(db: Session, ranked_names: list[str]) -> list[SuggestedRestaurant]:
    if not ranked_names:
        return []
    restaurants = db.execute(
        select(Restaurant)
        .options(selectinload(Restaurant.photos))
        .where(or_(*[Restaurant.name.ilike(name) for name in ranked_names[:3]]))
        .limit(10)
    ).scalars().all()
    if not restaurants:
        return []

    by_name = {str(r.name).lower(): r for r in restaurants if r.name}
    ordered: list[Restaurant] = []
    for name in ranked_names[:3]:
        match = by_name.get(name.lower())
        if match:
            ordered.append(match)

    if not ordered:
        ordered = restaurants[:3]

    ratings = _fetch_ratings(db, [r.id for r in ordered])
    return [
        SuggestedRestaurant(
            id=r.id,
            name=r.name,
            reason="From your recent recommendation list",
            average_rating=ratings.get(r.id, (0.0, 0))[0],
            pricing_tier=r.pricing_tier,
            cuisine_type=r.cuisine_type,
            city=r.city,
        )
        for r in ordered
    ]


def _extract_ranked_names(text: str) -> list[str]:
    names: list[str] = []
    for match in re.finditer(r"(?m)^\s*\d+\.\s*([^\(\n\-]+?)(?:\s*\(|\s*-|$)", text):
        name = match.group(1).strip()
        if name:
            names.append(name)
    return names


def _load_user_preferences(db: Session, user_id: int) -> dict[str, Any]:
    pref = db.execute(
        select(UserPreference).where(UserPreference.user_id == user_id)
    ).scalar_one_or_none()
    if pref is None:
        return {
            "cuisines": [],
            "price_range": None,
            "preferred_locations": [],
            "dietary_needs": [],
            "ambiance": [],
            "sort_preference": "rating",
        }
    return {
        "cuisines": pref.cuisines or [],
        "price_range": pref.price_range,
        "preferred_locations": pref.preferred_locations or [],
        "dietary_needs": pref.dietary_needs or [],
        "ambiance": pref.ambiance or [],
        "sort_preference": pref.sort_preference or "rating",
    }


def _extract_intent(
    message: str,
    conversation_history: list[ConversationTurn],
    preferences: dict[str, Any],
) -> dict[str, Any]:
    heuristic_intent = _extract_intent_heuristic(message, preferences)
    llm_intent = _extract_intent_with_llm(message, conversation_history, preferences)
    if llm_intent is None:
        return heuristic_intent
    return _merge_intent_with_message_priority(llm_intent, heuristic_intent)


def _merge_intent_with_message_priority(
    llm_intent: dict[str, Any],
    heuristic_intent: dict[str, Any],
) -> dict[str, Any]:
    merged = dict(llm_intent)

    def _clean_list(values: list[Any] | None) -> list[str]:
        if not values:
            return []
        out: list[str] = []
        seen: set[str] = set()
        for raw in values:
            token = str(raw).strip().lower()
            if not token or token in seen:
                continue
            seen.add(token)
            out.append(token)
        return out

    # Current user message should override stale context parsed from history.
    for key in ("cuisines", "dietary_needs", "ambiance"):
        h_values = _clean_list(heuristic_intent.get(key))
        if h_values:
            merged[key] = h_values
        else:
            merged[key] = _clean_list(merged.get(key))

    # Keep LLM keywords, but force include message-derived keywords first.
    merged_keywords = _clean_list(merged.get("keywords"))
    heuristic_keywords = _clean_list(heuristic_intent.get("keywords"))
    merged["keywords"] = (heuristic_keywords + merged_keywords)[:8]

    # Scalar fields from message (if present) take precedence.
    for key in ("price_range", "location", "occasion"):
        if heuristic_intent.get(key):
            merged[key] = heuristic_intent.get(key)

    return _normalize_intent(merged)


def _extract_intent_with_llm(
    message: str,
    conversation_history: list[ConversationTurn],
    preferences: dict[str, Any],
) -> dict[str, Any] | None:
    client = _build_llm_client(temperature=0.1)
    if client is None:
        return None

    history_blob = "\n".join(
        f"{turn.role}: {turn.content}" for turn in conversation_history[-6:]
    )
    prompt = (
        "Extract restaurant search intent from the user message and conversation.\n"
        "Return JSON only with keys:\n"
        'cuisines (array), price_range (one of "$","$$","$$$","$$$$" or null),\n'
        "location (string or null), dietary_needs (array), ambiance (array),\n"
        "keywords (array), occasion (string or null).\n\n"
        f"User preferences: {json.dumps(preferences, ensure_ascii=True)}\n"
        f"Conversation history:\n{history_blob or '(none)'}\n"
        f"User message: {message}\n"
    )

    try:
        from langchain_core.messages import HumanMessage, SystemMessage

        response = client.invoke(
            [
                SystemMessage(
                    content=(
                        "You parse restaurant recommendation intent. "
                        "Output valid JSON only."
                    )
                ),
                HumanMessage(content=prompt),
            ]
        )
        payload = _extract_json_object(_message_content_to_text(response.content))
        if payload is None:
            return None
        return _normalize_intent(payload)
    except Exception:
        return None


def _extract_intent_heuristic(message: str, preferences: dict[str, Any]) -> dict[str, Any]:
    lowered = message.lower()
    cuisine_vocab = {c.lower() for c in preferences.get("cuisines", []) if c} | _DEFAULT_CUISINES
    dietary_vocab = {d.lower() for d in preferences.get("dietary_needs", []) if d} | _DEFAULT_DIETARY
    ambiance_vocab = {a.lower() for a in preferences.get("ambiance", []) if a} | _DEFAULT_AMBIANCE

    cuisines = [c for c in sorted(cuisine_vocab) if c in lowered]
    dietary = [d for d in sorted(dietary_vocab) if d in lowered]
    ambiance = [a for a in sorted(ambiance_vocab) if a in lowered]

    price_match = re.search(r"\${1,4}", message)
    price_range = price_match.group(0) if price_match and price_match.group(0) in _PRICE_SET else None

    location = None
    loc_match = re.search(r"\b(?:in|near|around)\s+([a-zA-Z][a-zA-Z\s]{1,40})", message, flags=re.I)
    if loc_match:
        location = loc_match.group(1).strip(" .,!?")

    words = [w for w in re.findall(r"[a-zA-Z][a-zA-Z\-]{2,}", lowered) if w not in _STOP_WORDS]
    keywords = words[:6]

    occasion = None
    for token in ("anniversary", "birthday", "date", "dinner", "lunch", "brunch", "tonight"):
        if token in lowered:
            occasion = token
            break

    return {
        "cuisines": cuisines,
        "price_range": price_range,
        "location": location,
        "dietary_needs": dietary,
        "ambiance": ambiance,
        "keywords": keywords,
        "occasion": occasion,
    }


def _normalize_intent(intent: dict[str, Any]) -> dict[str, Any]:
    cuisines = [str(v).strip().lower() for v in intent.get("cuisines", []) if str(v).strip()]
    dietary = [str(v).strip().lower() for v in intent.get("dietary_needs", []) if str(v).strip()]
    ambiance = [str(v).strip().lower() for v in intent.get("ambiance", []) if str(v).strip()]
    keywords = [str(v).strip().lower() for v in intent.get("keywords", []) if str(v).strip()]
    location = intent.get("location")
    occasion = intent.get("occasion")
    price_range = intent.get("price_range")

    if price_range not in _PRICE_SET:
        price_range = None
    return {
        "cuisines": cuisines[:6],
        "price_range": price_range,
        "location": (str(location).strip() if location else None),
        "dietary_needs": dietary[:6],
        "ambiance": ambiance[:6],
        "keywords": keywords[:8],
        "occasion": (str(occasion).strip().lower() if occasion else None),
    }


def _search_and_rank_restaurants(
    db: Session,
    intent: dict[str, Any],
    preferences: dict[str, Any],
) -> list[dict[str, Any]]:
    stmt = select(Restaurant).options(selectinload(Restaurant.photos))
    cuisines = intent.get("cuisines") or []
    location = intent.get("location")
    keywords = intent.get("keywords") or []

    if cuisines:
        stmt = stmt.where(
            or_(*[Restaurant.cuisine_type.ilike(f"%{cuisine}%") for cuisine in cuisines])
        )
    if location:
        stmt = stmt.where(Restaurant.city.ilike(f"%{location}%"))
    # Only apply free-text keyword filtering when no structured filters were given.
    # If user already specified cuisine/location, keyword filter can over-constrain
    # the query (e.g. "recommend chinese restaurant") and cause false empty sets.
    if keywords and not (cuisines or location):
        keyword_clauses = []
        for kw in keywords[:4]:
            pattern = f"%{kw}%"
            keyword_clauses.append(Restaurant.name.ilike(pattern))
            keyword_clauses.append(Restaurant.cuisine_type.ilike(pattern))
            keyword_clauses.append(Restaurant.description.ilike(pattern))
            keyword_clauses.append(cast(Restaurant.amenities, String).ilike(pattern))
        stmt = stmt.where(or_(*keyword_clauses))

    restaurants = db.execute(stmt.limit(60)).scalars().all()
    if not restaurants and cuisines:
        # Keep precision for explicit cuisine asks; avoid falling back to unrelated results.
        return []
    if not restaurants:
        restaurants = db.execute(
            select(Restaurant).options(selectinload(Restaurant.photos)).limit(60)
        ).scalars().all()
    if not restaurants:
        return []

    ratings = _fetch_ratings(db, [r.id for r in restaurants])
    ranked: list[dict[str, Any]] = []
    for restaurant in restaurants:
        avg_rating, review_count = ratings.get(restaurant.id, (0.0, 0))
        score, reasons = _score_restaurant(
            restaurant=restaurant,
            average_rating=avg_rating,
            review_count=review_count,
            intent=intent,
            preferences=preferences,
        )
        ranked.append(
            {
                "restaurant": restaurant,
                "score": score,
                "average_rating": avg_rating,
                "review_count": review_count,
                "reasons": reasons,
            }
        )

    ranked.sort(
        key=lambda row: (row["score"], row["average_rating"], row["review_count"]),
        reverse=True,
    )
    return ranked


def _score_restaurant(
    *,
    restaurant: Restaurant,
    average_rating: float,
    review_count: int,
    intent: dict[str, Any],
    preferences: dict[str, Any],
) -> tuple[float, list[str]]:
    score = average_rating * 0.9 + min(review_count, 40) * 0.05
    reasons: list[str] = []

    text_blob = " ".join(
        [
            restaurant.name or "",
            restaurant.cuisine_type or "",
            restaurant.description or "",
            " ".join(str(v) for v in (restaurant.amenities or [])),
        ]
    ).lower()

    wanted_cuisines = [c.lower() for c in (intent.get("cuisines") or [])]
    pref_cuisines = [str(c).lower() for c in (preferences.get("cuisines") or [])]
    restaurant_cuisine = (restaurant.cuisine_type or "").lower()

    if wanted_cuisines and any(c in restaurant_cuisine for c in wanted_cuisines):
        score += 4
        reasons.append("Matches your cuisine request")
    elif pref_cuisines and any(c in restaurant_cuisine for c in pref_cuisines):
        score += 2
        reasons.append("Matches your saved cuisine preferences")

    wanted_price = intent.get("price_range")
    pref_price = preferences.get("price_range")
    if wanted_price and restaurant.pricing_tier == wanted_price:
        score += 2.5
        reasons.append(f"Within your requested budget ({wanted_price})")
    elif pref_price and restaurant.pricing_tier == pref_price:
        score += 1.5
        reasons.append(f"Matches your usual budget ({pref_price})")

    location = intent.get("location")
    if location and location.lower() in (restaurant.city or "").lower():
        score += 2
        reasons.append(f"In your requested area ({restaurant.city})")
    else:
        for pref_location in preferences.get("preferred_locations", []):
            if pref_location and pref_location.lower() in (restaurant.city or "").lower():
                score += 1.2
                reasons.append(f"In your preferred location ({restaurant.city})")
                break

    wanted_dietary = [d.lower() for d in (intent.get("dietary_needs") or [])]
    pref_dietary = [str(d).lower() for d in (preferences.get("dietary_needs") or [])]
    for token in wanted_dietary + pref_dietary:
        if token and token in text_blob:
            score += 1
            reasons.append(f"Supports {token} options")
            break

    wanted_ambiance = [a.lower() for a in (intent.get("ambiance") or [])]
    pref_ambiance = [str(a).lower() for a in (preferences.get("ambiance") or [])]
    for token in wanted_ambiance + pref_ambiance:
        if token and token in text_blob:
            score += 0.8
            reasons.append(f"Fits {token} ambiance")
            break

    for kw in (intent.get("keywords") or [])[:4]:
        if kw and kw.lower() in text_blob:
            score += 0.6

    occasion = intent.get("occasion")
    if occasion and occasion in text_blob:
        score += 0.6

    if average_rating > 0:
        reasons.append(f"Rated {average_rating:.1f}★ from {review_count} review(s)")

    return score, reasons


def _fetch_tavily_context(
    ranked: list[dict[str, Any]],
    intent: dict[str, Any],
) -> dict[int, list[str]]:
    if not settings.tavily_api_key:
        return {}
    try:
        from tavily import TavilyClient
    except Exception:
        return {}

    client = TavilyClient(api_key=settings.tavily_api_key)
    context: dict[int, list[str]] = {}
    for item in ranked[:3]:
        restaurant: Restaurant = item["restaurant"]
        city_hint = restaurant.city or intent.get("location") or ""
        query = f"{restaurant.name} {city_hint} restaurant hours special events"
        try:
            result = client.search(query=query, max_results=2, search_depth="basic")
        except Exception:
            continue

        snippets: list[str] = []
        for row in (result or {}).get("results", [])[:2]:
            title = str(row.get("title", "")).strip()
            content = str(row.get("content", "")).strip()
            merged = f"{title}: {content}".strip(": ").strip()
            if merged:
                snippets.append(_truncate(merged, 220))
        if snippets:
            context[restaurant.id] = snippets
    return context


def _build_suggestion(item: dict[str, Any], tavily_snippets: list[str]) -> SuggestedRestaurant:
    restaurant: Restaurant = item["restaurant"]
    reasons = item["reasons"][:2]
    reason = "; ".join(reasons) if reasons else "Relevant to your query and profile"
    if tavily_snippets:
        reason = f"{reason}; Live context checked via Tavily"

    return SuggestedRestaurant(
        id=restaurant.id,
        name=restaurant.name,
        reason=reason,
        average_rating=item["average_rating"],
        pricing_tier=restaurant.pricing_tier,
        cuisine_type=restaurant.cuisine_type,
        city=restaurant.city,
    )


def _build_reply(
    *,
    message: str,
    conversation_history: list[ConversationTurn],
    preferences: dict[str, Any],
    intent: dict[str, Any],
    suggestions: list[SuggestedRestaurant],
    tavily_context: dict[int, list[str]],
) -> str:
    llm_reply = _build_reply_with_llm(
        message=message,
        conversation_history=conversation_history,
        preferences=preferences,
        intent=intent,
        suggestions=suggestions,
        tavily_context=tavily_context,
    )
    if llm_reply:
        return llm_reply
    return _build_fallback_reply(suggestions)


def _build_reply_with_llm(
    *,
    message: str,
    conversation_history: list[ConversationTurn],
    preferences: dict[str, Any],
    intent: dict[str, Any],
    suggestions: list[SuggestedRestaurant],
    tavily_context: dict[int, list[str]],
) -> str | None:
    client = _build_llm_client(temperature=0.35)
    if client is None:
        return None

    suggestion_payload = [s.model_dump() for s in suggestions]
    context_payload = {
        "user_preferences": preferences,
        "query_intent": intent,
        "suggested_restaurants": suggestion_payload,
        "tavily_context": tavily_context,
        "conversation_history": [turn.model_dump() for turn in conversation_history[-8:]],
        "new_message": message,
    }

    try:
        from langchain_core.messages import HumanMessage, SystemMessage

        response = client.invoke(
            [
                SystemMessage(
                    content=(
                        "You are a restaurant recommendation assistant. "
                        "Use provided preferences, ranked restaurants, and Tavily context. "
                        "Be concise, conversational, and practical."
                    )
                ),
                HumanMessage(
                    content=(
                        "Generate a helpful response with 2-4 recommendations and short reasons.\n"
                        f"{json.dumps(context_payload, ensure_ascii=True)}"
                    )
                ),
            ]
        )
        text = _message_content_to_text(response.content).strip()
        return text or None
    except Exception:
        return None


def _build_fallback_reply(suggestions: list[SuggestedRestaurant]) -> str:
    if not suggestions:
        return (
            "I couldn't find a strong match yet. Try adding cuisine, budget ($-$$$$), "
            "or location so I can narrow recommendations."
        )

    lines = ["Here are top matches based on your preferences and query:"]
    for index, suggestion in enumerate(suggestions[:3], start=1):
        meta = []
        if suggestion.average_rating:
            meta.append(f"{suggestion.average_rating:.1f}★")
        if suggestion.pricing_tier:
            meta.append(suggestion.pricing_tier)
        suffix = f" ({', '.join(meta)})" if meta else ""
        lines.append(f"{index}. {suggestion.name}{suffix} - {suggestion.reason}")
    return "\n".join(lines)


def _build_llm_client(temperature: float):
    provider = settings.llm_provider.strip().lower()
    if provider == "anthropic":
        if not settings.anthropic_api_key:
            return None
        try:
            from langchain_anthropic import ChatAnthropic
        except Exception:
            return None
        return ChatAnthropic(
            anthropic_api_key=settings.anthropic_api_key,
            model=settings.anthropic_model,
            temperature=temperature,
        )

    if not settings.openai_api_key:
        return None
    try:
        from langchain_openai import ChatOpenAI
    except Exception:
        return None
    return ChatOpenAI(
        api_key=settings.openai_api_key,
        model=settings.openai_model,
        temperature=temperature,
    )


def _message_content_to_text(content: Any) -> str:
    if isinstance(content, str):
        return content
    if isinstance(content, list):
        chunks: list[str] = []
        for item in content:
            if isinstance(item, str):
                chunks.append(item)
            elif isinstance(item, dict):
                maybe_text = item.get("text")
                if maybe_text:
                    chunks.append(str(maybe_text))
        return "\n".join(chunks).strip()
    return str(content or "")


def _extract_json_object(raw: str) -> dict[str, Any] | None:
    if not raw:
        return None
    try:
        parsed = json.loads(raw)
        return parsed if isinstance(parsed, dict) else None
    except json.JSONDecodeError:
        pass

    match = re.search(r"\{.*\}", raw, flags=re.S)
    if not match:
        return None
    try:
        parsed = json.loads(match.group(0))
        return parsed if isinstance(parsed, dict) else None
    except json.JSONDecodeError:
        return None


def _truncate(value: str, max_len: int) -> str:
    if len(value) <= max_len:
        return value
    return value[: max_len - 3].rstrip() + "..."
