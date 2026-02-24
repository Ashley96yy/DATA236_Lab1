"""
SQLAlchemy ORM model for the `restaurant_photos` table.

Schema aligned with IMPLEMENTATION_PLAN.md Phase 3 (section 3.1).
NOTE: This table does not exist in db/001_init_schema.sql yet.
      It must be created via migration before photo endpoints go live.
"""
from __future__ import annotations

from datetime import datetime
from typing import Optional, TYPE_CHECKING

from sqlalchemy import BigInteger, DateTime, ForeignKey, String, text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base

if TYPE_CHECKING:
    from app.models.restaurant import Restaurant


class RestaurantPhoto(Base):
    __tablename__ = "restaurant_photos"

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True, autoincrement=True)

    restaurant_id: Mapped[int] = mapped_column(
        BigInteger,
        ForeignKey("restaurants.id", ondelete="CASCADE"),
        nullable=False,
    )
    photo_url: Mapped[str] = mapped_column(String(500), nullable=False)

    # Exactly one of these will be set per row (auth rule from plan section 3.2)
    uploaded_by_user_id: Mapped[Optional[int]] = mapped_column(
        BigInteger,
        ForeignKey("users.id", ondelete="SET NULL"),
        nullable=True,
    )
    uploaded_by_owner_id: Mapped[Optional[int]] = mapped_column(
        BigInteger,
        ForeignKey("owners.id", ondelete="SET NULL"),
        nullable=True,
    )

    created_at: Mapped[datetime] = mapped_column(
        DateTime, nullable=False, server_default=text("CURRENT_TIMESTAMP")
    )

    # Relationships
    restaurant: Mapped["Restaurant"] = relationship(
        "Restaurant", back_populates="photos"
    )
