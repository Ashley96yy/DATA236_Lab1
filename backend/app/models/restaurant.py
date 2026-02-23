"""
SQLAlchemy ORM model for the `restaurants` table.

Schema aligned with IMPLEMENTATION_PLAN.md Phase 3 (section 3.1).
NOTE: The existing SQL table (db/001_init_schema.sql) is missing several columns
listed below. A migration will be required before endpoints go live.
See schema mismatch notes at bottom of this file.
"""
from __future__ import annotations

from datetime import datetime
from typing import Optional

from sqlalchemy import BigInteger, DateTime, Enum, Float, ForeignKey, JSON, String, Text, text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base

pricing_tier_enum = Enum("$", "$$", "$$$", "$$$$", name="pricing_tier_enum")


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
    pricing_tier: Mapped[Optional[str]] = mapped_column(pricing_tier_enum, nullable=True)
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
    reviews: Mapped[list] = relationship(
        "Review", back_populates="restaurant", cascade="all, delete-orphan"
    )


# ---------------------------------------------------------------------------
# SCHEMA MISMATCH NOTES (vs db/001_init_schema.sql)
# ---------------------------------------------------------------------------
# The live DB table is MISSING these columns that this model expects:
#   - street          (VARCHAR 255)  — plan calls it out explicitly
#   - state           (VARCHAR 50)   — present in plan; absent in SQL
#   - country         (VARCHAR 100)  — absent in SQL
#   - latitude        (FLOAT)        — required for Phase 7
#   - longitude       (FLOAT)        — required for Phase 7
#   - phone           (VARCHAR 30)   — absent in SQL (was "contact_info")
#   - email           (VARCHAR 255)  — absent in SQL
#   - hours_json      (JSON)         — SQL has `hours VARCHAR(120)` instead
#   - amenities       (JSON)         — absent in SQL (critical for Phase 7)
#   - claimed_by_owner_id (BIGINT FK → owners.id) — absent in SQL
#
# The live DB table has these columns NOT in this model (to be renamed/dropped):
#   - address         → superseded by street + city + state + zip_code + country
#   - contact_info    → superseded by phone + email
#   - hours           → superseded by hours_json
#   - price_tier      → renamed to pricing_tier in plan
#
# Action required before endpoints go live:
#   ALTER TABLE to add missing columns and rename/adjust existing ones.
#   This will be done via a raw SQL migration script or Alembic (per Decision B).
# ---------------------------------------------------------------------------
