from __future__ import annotations

import hashlib
import math
import re
import time
from dataclasses import dataclass
from datetime import datetime
from typing import Any

from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.core.config import get_settings
from app.models.restaurant import Restaurant
from app.models.review import Review

settings = get_settings()

_SYNC_TTL_SECONDS = 45
_HASH_EMBEDDING_DIMENSION = 256
_last_sync_signature: str | None = None
_last_sync_monotonic: float = 0.0


@dataclass(slots=True)
class VectorSearchHit:
    restaurant_id: int
    similarity: float


class _SimpleHashEmbeddings:
    """Offline-safe fallback embedding for local development."""

    def __init__(self, dimension: int = _HASH_EMBEDDING_DIMENSION) -> None:
        self.dimension = dimension

    def embed_documents(self, texts: list[str]) -> list[list[float]]:
        return [self._embed_text(text) for text in texts]

    def embed_query(self, text: str) -> list[float]:
        return self._embed_text(text)

    def _embed_text(self, text: str) -> list[float]:
        vector = [0.0] * self.dimension
        tokens = re.findall(r"[a-z0-9$][a-z0-9$&+/\-]{1,}", text.lower())
        if not tokens:
            return vector

        for token in tokens:
            digest = hashlib.sha256(token.encode("utf-8")).digest()
            index = int.from_bytes(digest[:4], "big") % self.dimension
            sign = 1.0 if digest[4] % 2 == 0 else -1.0
            weight = 1.0 + min(len(token), 12) / 12.0
            vector[index] += sign * weight

        magnitude = math.sqrt(sum(value * value for value in vector))
        if magnitude == 0:
            return vector
        return [value / magnitude for value in vector]


def build_retrieval_query(
    *,
    message: str,
    intent: dict[str, Any],
    preferences: dict[str, Any],
) -> str:
    lines = [f"User query: {message.strip()}"]

    cuisines = intent.get("cuisines") or []
    if cuisines:
        lines.append("Requested cuisines: " + ", ".join(cuisines))
    if intent.get("price_range"):
        lines.append(f"Requested price range: {intent['price_range']}")
    if intent.get("location"):
        lines.append(f"Requested location: {intent['location']}")

    dietary = intent.get("dietary_needs") or []
    if dietary:
        lines.append("Dietary needs: " + ", ".join(dietary))

    ambiance = intent.get("ambiance") or []
    if ambiance:
        lines.append("Desired ambiance: " + ", ".join(ambiance))

    keywords = intent.get("keywords") or []
    if keywords:
        lines.append("Keywords: " + ", ".join(keywords))

    preferred_cuisines = preferences.get("cuisines") or []
    preferred_locations = preferences.get("preferred_locations") or []
    if preferred_cuisines:
        lines.append("Saved cuisine preferences: " + ", ".join(str(v) for v in preferred_cuisines))
    if preferences.get("price_range"):
        lines.append(f"Saved price preference: {preferences['price_range']}")
    if preferred_locations:
        lines.append("Saved preferred locations: " + ", ".join(str(v) for v in preferred_locations))

    return "\n".join(line for line in lines if line.strip())


def semantic_candidate_search(
    db: Session,
    *,
    message: str,
    intent: dict[str, Any],
    preferences: dict[str, Any],
    limit: int,
) -> list[VectorSearchHit]:
    if limit <= 0:
        return []

    collection = _get_collection()
    if collection is None:
        return []

    embedder = _build_embedder()
    query_text = build_retrieval_query(
        message=message,
        intent=intent,
        preferences=preferences,
    )
    if not query_text.strip():
        return []

    try:
        _sync_restaurant_collection_if_needed(db, collection=collection, embedder=embedder)
        result = collection.query(
            query_embeddings=[embedder.embed_query(query_text)],
            n_results=limit,
            include=["distances", "metadatas"],
        )
    except Exception:
        return []

    ids = (result or {}).get("ids") or [[]]
    distances = (result or {}).get("distances") or [[]]
    hits: list[VectorSearchHit] = []
    seen_ids: set[int] = set()

    for raw_id, raw_distance in zip(ids[0], distances[0], strict=False):
        try:
            restaurant_id = int(raw_id)
        except (TypeError, ValueError):
            continue
        if restaurant_id in seen_ids:
            continue
        seen_ids.add(restaurant_id)
        distance = float(raw_distance or 0.0)
        hits.append(
            VectorSearchHit(
                restaurant_id=restaurant_id,
                similarity=1.0 / (1.0 + max(distance, 0.0)),
            )
        )

    return hits


def rebuild_restaurant_index(db: Session) -> int:
    collection = _get_collection()
    if collection is None:
        return 0

    embedder = _build_embedder()
    return _sync_restaurant_collection(db, collection=collection, embedder=embedder)


def _get_collection():
    try:
        import chromadb
    except Exception:
        return None

    settings.vector_db_dir.mkdir(parents=True, exist_ok=True)
    client = chromadb.PersistentClient(path=str(settings.vector_db_dir))
    return client.get_or_create_collection(
        name=settings.vector_collection_name,
        metadata={"hnsw:space": "cosine"},
    )


def _build_embedder():
    provider = settings.embedding_provider.strip().lower()
    if provider == "openai" and settings.openai_api_key:
        try:
            from langchain_openai import OpenAIEmbeddings
        except Exception:
            return _SimpleHashEmbeddings()
        return OpenAIEmbeddings(
            api_key=settings.openai_api_key,
            model=settings.openai_embedding_model,
        )
    return _SimpleHashEmbeddings()


def _sync_restaurant_collection_if_needed(db: Session, *, collection, embedder) -> int:
    global _last_sync_monotonic, _last_sync_signature

    signature = _build_sync_signature(db)
    now = time.monotonic()
    if (
        _last_sync_signature == signature
        and (now - _last_sync_monotonic) < _SYNC_TTL_SECONDS
    ):
        return 0

    synced = _sync_restaurant_collection(db, collection=collection, embedder=embedder)
    _last_sync_signature = signature
    _last_sync_monotonic = now
    return synced


def _build_sync_signature(db: Session) -> str:
    restaurant_stats = db.execute(
        select(
            func.count(Restaurant.id),
            func.max(Restaurant.updated_at),
            func.max(Restaurant.created_at),
        )
    ).one()
    review_stats = db.execute(
        select(
            func.count(Review.id),
            func.max(Review.updated_at),
            func.max(Review.created_at),
        )
    ).one()
    return "|".join(
        [
            str(int(restaurant_stats[0] or 0)),
            _dt_key(restaurant_stats[1] or restaurant_stats[2]),
            str(int(review_stats[0] or 0)),
            _dt_key(review_stats[1] or review_stats[2]),
        ]
    )


def _sync_restaurant_collection(db: Session, *, collection, embedder) -> int:
    restaurants = db.execute(
        select(Restaurant).order_by(Restaurant.id.asc())
    ).scalars().all()

    existing = collection.get(include=["metadatas"])
    existing_ids = existing.get("ids") or []
    if existing_ids:
        collection.delete(ids=existing_ids)

    if not restaurants:
        return 0

    review_rows = db.execute(
        select(Review.restaurant_id, Review.rating, Review.comment)
        .order_by(Review.restaurant_id.asc(), Review.updated_at.desc(), Review.id.desc())
    ).all()
    reviews_by_restaurant: dict[int, list[str]] = {}
    for row in review_rows:
        if row.restaurant_id is None:
            continue
        bucket = reviews_by_restaurant.setdefault(int(row.restaurant_id), [])
        if len(bucket) >= 3:
            continue
        if row.comment:
            bucket.append(f"{row.rating} star review: {str(row.comment).strip()}")
        elif row.rating is not None:
            bucket.append(f"{row.rating} star review")

    ids: list[str] = []
    documents: list[str] = []
    metadatas: list[dict[str, Any]] = []
    for restaurant in restaurants:
        ids.append(str(restaurant.id))
        documents.append(
            _restaurant_to_document(
                restaurant,
                reviews_by_restaurant.get(int(restaurant.id), []),
            )
        )
        metadatas.append(
            {
                "restaurant_id": int(restaurant.id),
                "city": restaurant.city or "",
                "cuisine_type": restaurant.cuisine_type or "",
                "pricing_tier": restaurant.pricing_tier or "",
            }
        )

    embeddings = embedder.embed_documents(documents)
    collection.upsert(
        ids=ids,
        documents=documents,
        metadatas=metadatas,
        embeddings=embeddings,
    )
    return len(ids)


def _restaurant_to_document(restaurant: Restaurant, review_snippets: list[str]) -> str:
    lines = [
        f"Restaurant name: {restaurant.name}",
        f"Cuisine: {restaurant.cuisine_type or 'unknown'}",
        f"Description: {restaurant.description or 'n/a'}",
        f"City: {restaurant.city}",
        f"State: {restaurant.state or 'n/a'}",
        f"Country: {restaurant.country or 'n/a'}",
        f"Price tier: {restaurant.pricing_tier or 'n/a'}",
        "Amenities: " + ", ".join(str(v) for v in (restaurant.amenities or [])) if restaurant.amenities else "Amenities: n/a",
        "Hours: " + _hours_to_text(restaurant.hours_json),
    ]
    if restaurant.street:
        lines.append(f"Street: {restaurant.street}")
    if restaurant.phone:
        lines.append(f"Phone: {restaurant.phone}")
    if restaurant.email:
        lines.append(f"Email: {restaurant.email}")
    if review_snippets:
        lines.append("Review highlights: " + " | ".join(review_snippets[:3]))
    return "\n".join(lines)


def _hours_to_text(hours_json: Any) -> str:
    if not isinstance(hours_json, dict) or not hours_json:
        return "n/a"
    parts = [
        f"{str(day)} {str(hours)}"
        for day, hours in hours_json.items()
        if day and str(hours).strip()
    ]
    return "; ".join(parts[:7]) if parts else "n/a"


def _dt_key(value: datetime | None) -> str:
    if value is None:
        return "0"
    return value.isoformat()
