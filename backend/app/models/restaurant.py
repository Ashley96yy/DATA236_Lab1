"""SQLAlchemy ORM model for the `restaurants` table (Phase 3)."""
from __future__ import annotations

from datetime import datetime
from typing import Optional

from sqlalchemy import BigInteger, DateTime, Float, ForeignKey, JSON, String, Text, text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base


class Restaurant(Base):
    __tablename__ = "restaurants"

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True, autoincrement=True)

    # Core identity
    name: Mapped[str] = mapped_column(String(200), nullable=False)
    cuisine_type: Mapped[Optional[str]] = mapped_column(String(100), nullable=True)
    description: Mapped[Optional[str]] = mapped_column(Text, nullable=True)

    # Address
    street: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)
    city: Mapped[str] = mapped_column(String(100), nullable=False)
    state: Mapped[Optional[str]] = mapped_column(String(50), nullable=True)
    zip_code: Mapped[Optional[str]] = mapped_column(String(20), nullable=True)
    country: Mapped[Optional[str]] = mapped_column(String(100), nullable=True)

    # Geo (Phase 7 — required here so column exists)
    latitude: Mapped[Optional[float]] = mapped_column(Float, nullable=True)
    longitude: Mapped[Optional[float]] = mapped_column(Float, nullable=True)

    # Contact
    phone: Mapped[Optional[str]] = mapped_column(String(30), nullable=True)
    email: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)

    # Rich data
    hours_json: Mapped[Optional[dict]] = mapped_column(JSON, nullable=True)
    pricing_tier: Mapped[Optional[str]] = mapped_column(String(10), nullable=True)
    amenities: Mapped[Optional[list]] = mapped_column(JSON, nullable=True)

    # Ownership
    created_by_user_id: Mapped[Optional[int]] = mapped_column(
        BigInteger,
        ForeignKey("users.id", ondelete="SET NULL"),
        nullable=True,
    )
    claimed_by_owner_id: Mapped[Optional[int]] = mapped_column(
        BigInteger,
        ForeignKey("owners.id", ondelete="SET NULL"),
        nullable=True,
    )

    # Timestamps
    created_at: Mapped[datetime] = mapped_column(
        DateTime, nullable=False, server_default=text("CURRENT_TIMESTAMP")
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime,
        nullable=False,
        server_default=text("CURRENT_TIMESTAMP"),
        server_onupdate=text("CURRENT_TIMESTAMP"),
    )

    # Relationships (used by joined queries in service layer)
    photos: Mapped[list["RestaurantPhoto"]] = relationship(  # noqa: F821
        "RestaurantPhoto", back_populates="restaurant", cascade="all, delete-orphan"
    )
    # reviews relationship added in Phase 4 once the Review model is defined


# Legacy columns (address, contact_info, hours) remain in the DB for seed data
# compatibility but are not mapped here and not used by the API.
