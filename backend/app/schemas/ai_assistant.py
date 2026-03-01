from __future__ import annotations

from typing import Literal

from pydantic import BaseModel, Field


class ConversationTurn(BaseModel):
    role: Literal["user", "assistant"]
    content: str = Field(min_length=1, max_length=3000)


class AIChatRequest(BaseModel):
    message: str = Field(min_length=1, max_length=3000)
    conversation_history: list[ConversationTurn] = Field(default_factory=list)


class SuggestedRestaurant(BaseModel):
    id: int
    name: str
    reason: str
    average_rating: float | None = None
    pricing_tier: str | None = None
    cuisine_type: str | None = None
    city: str | None = None


class AIChatResponse(BaseModel):
    reply: str
    suggested_restaurants: list[SuggestedRestaurant] = Field(default_factory=list)
