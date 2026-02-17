from datetime import datetime
from typing import Optional

from sqlalchemy import DateTime, Enum, ForeignKey, JSON, text
from sqlalchemy.orm import Mapped, mapped_column

from app.db.base import Base

price_range_enum = Enum("$", "$$", "$$$", "$$$$", name="price_range_enum")
sort_preference_enum = Enum(
    "rating",
    "distance",
    "popularity",
    "price",
    name="sort_preference_enum",
)


class UserPreference(Base):
    __tablename__ = "user_preferences"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id", ondelete="CASCADE"), unique=True)
    cuisines: Mapped[Optional[list[str]]] = mapped_column(JSON, nullable=True)
    price_range: Mapped[Optional[str]] = mapped_column(price_range_enum, nullable=True)
    preferred_locations: Mapped[Optional[list[str]]] = mapped_column(JSON, nullable=True)
    search_radius_km: Mapped[Optional[int]] = mapped_column(nullable=True)
    dietary_needs: Mapped[Optional[list[str]]] = mapped_column(JSON, nullable=True)
    ambiance: Mapped[Optional[list[str]]] = mapped_column(JSON, nullable=True)
    sort_preference: Mapped[str] = mapped_column(
        sort_preference_enum,
        nullable=False,
        server_default=text("'rating'"),
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime,
        nullable=False,
        server_default=text("CURRENT_TIMESTAMP"),
        server_onupdate=text("CURRENT_TIMESTAMP"),
    )
