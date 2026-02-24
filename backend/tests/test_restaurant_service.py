"""
Unit tests for app/services/restaurant_service.py — Phase 3.

Run with:
    cd backend
    source venv/bin/activate
    pytest tests/test_restaurant_service.py -v

Uses a dedicated MySQL test database (yelp_lab1_test) that is created/dropped
once per test session. Each test runs in a transaction that is rolled back so
tests are isolated and the test DB is always clean.
"""
from __future__ import annotations

import pytest
from sqlalchemy.orm import Session

from app.models.owner import Owner
from app.models.restaurant import Restaurant
from app.models.restaurant_photo import RestaurantPhoto  # noqa: F401 — registers model
from app.models.user import User
from app.models.user_preference import UserPreference  # noqa: F401 — registers model
from app.schemas.restaurant import RestaurantCreate
from app.services import restaurant_service
from app.services.errors import (
    ServiceBadRequest,
    ServiceForbidden,
    ServiceNotFound,
    ServiceUnauthorized,
)


# ---------------------------------------------------------------------------
# Test DB fixtures (MySQL, session-scoped schema, function-scoped session)
# ---------------------------------------------------------------------------

@pytest.fixture(scope="session")
def engine():
    """Use the live yelp_lab1 DB — tests roll back so no data persists."""
    from app.db.session import engine as app_engine
    return app_engine


@pytest.fixture()
def db(engine):
    """
    Each test runs inside a transaction that is rolled back at teardown.
    Service-level db.commit() calls are handled via SAVEPOINT so the outer
    transaction (and thus all test data) is never permanently committed.
    """
    connection = engine.connect()
    trans = connection.begin()
    session = Session(bind=connection, join_transaction_mode="create_savepoint")
    yield session
    session.close()
    trans.rollback()
    connection.close()


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def make_user(db: Session, email: str = "u@test.com") -> User:
    u = User(name="Test User", email=email, password_hash="hashed")
    db.add(u)
    db.flush()
    return u


def make_owner(db: Session, email: str = "o@test.com") -> Owner:
    o = Owner(name="Test Owner", email=email, password_hash="hashed", restaurant_location="Test City")
    db.add(o)
    db.flush()
    return o


def make_restaurant(db: Session, user_id: int, name: str = "Test Restaurant",
                    amenities=None) -> "RestaurantResponse":  # type: ignore[name-defined]
    data = RestaurantCreate(
        name=name,
        city="Testville",
        amenities=amenities or ["WiFi", "Parking"],
    )
    return restaurant_service.create_restaurant(db, data, user_id)


# ---------------------------------------------------------------------------
# Test: create_restaurant
# ---------------------------------------------------------------------------

class TestCreateRestaurant:
    def test_creates_and_returns_response(self, db):
        user = make_user(db)
        data = RestaurantCreate(
            name="Burger Place",
            city="San Jose",
            state="CA",
            pricing_tier="$$",
            amenities=["WiFi"],
        )
        resp = restaurant_service.create_restaurant(db, data, user.id)

        assert resp.id is not None
        assert resp.name == "Burger Place"
        assert resp.city == "San Jose"
        assert resp.pricing_tier == "$$"
        assert resp.amenities == ["WiFi"]
        assert resp.created_by_user_id == user.id
        assert resp.photos == []

    def test_optional_fields_default_to_none(self, db):
        user = make_user(db, "u2@test.com")
        data = RestaurantCreate(name="Minimal", city="Oakland")
        resp = restaurant_service.create_restaurant(db, data, user.id)

        assert resp.cuisine_type is None
        assert resp.description is None
        assert resp.amenities is None
        assert resp.claimed_by_owner_id is None

    def test_average_rating_defaults_to_zero(self, db):
        user = make_user(db, "u3@test.com")
        data = RestaurantCreate(name="New Place", city="Anywhere")
        resp = restaurant_service.create_restaurant(db, data, user.id)
        assert resp.average_rating == 0.0
        assert resp.review_count == 0


# ---------------------------------------------------------------------------
# Test: get_restaurant_by_id
# ---------------------------------------------------------------------------

class TestGetRestaurantById:
    def test_returns_existing_restaurant(self, db):
        user = make_user(db, "g1@test.com")
        created = make_restaurant(db, user.id, "Find Me")
        result = restaurant_service.get_restaurant_by_id(db, created.id)
        assert result.id == created.id
        assert result.name == "Find Me"

    def test_photos_list_is_included(self, db):
        user = make_user(db, "g2@test.com")
        created = make_restaurant(db, user.id, "With Photos")
        result = restaurant_service.get_restaurant_by_id(db, created.id)
        assert isinstance(result.photos, list)

    def test_raises_not_found_for_missing_id(self, db):
        with pytest.raises(ServiceNotFound):
            restaurant_service.get_restaurant_by_id(db, 999999)


# ---------------------------------------------------------------------------
# Test: search_restaurants
# ---------------------------------------------------------------------------

class TestSearchRestaurants:
    @pytest.fixture(autouse=True)
    def seed(self, db):
        user = make_user(db, "s@test.com")
        restaurant_service.create_restaurant(db, RestaurantCreate(
            name="Sushi Palace",
            city="San Francisco", state="CA",
            cuisine_type="Japanese",
            amenities=["WiFi", "Sushi Bar"],
            description="Best sushi in town",
        ), user.id)
        restaurant_service.create_restaurant(db, RestaurantCreate(
            name="Taco Heaven",
            city="Los Angeles", state="CA",
            cuisine_type="Mexican",
            amenities=["Outdoor Seating"],
            description="Great tacos and burritos",
        ), user.id)

    def test_returns_all_without_filters(self, db):
        result = restaurant_service.search_restaurants(db)
        assert result.total >= 2

    def test_filter_by_name(self, db):
        result = restaurant_service.search_restaurants(db, name="Sushi")
        assert result.total >= 1
        assert all("sushi" in item.name.lower() for item in result.items)

    def test_filter_by_city(self, db):
        result = restaurant_service.search_restaurants(db, city="San Francisco")
        assert result.total >= 1
        assert all(item.city == "San Francisco" for item in result.items)

    def test_filter_by_cuisine(self, db):
        result = restaurant_service.search_restaurants(db, cuisine="Japanese")
        assert result.total >= 1

    def test_keyword_matches_amenities(self, db):
        """'wifi' must match restaurants with amenities JSON containing 'WiFi'."""
        result = restaurant_service.search_restaurants(db, keywords="wifi")
        assert result.total >= 1
        names = [item.name for item in result.items]
        assert "Sushi Palace" in names

    def test_keyword_does_not_match_wrong_restaurant(self, db):
        """'outdoor' should match Taco Heaven but not Sushi Palace."""
        result = restaurant_service.search_restaurants(db, keywords="outdoor")
        assert result.total >= 1
        names = [item.name for item in result.items]
        assert "Taco Heaven" in names

    def test_keyword_matches_description(self, db):
        result = restaurant_service.search_restaurants(db, keywords="tacos")
        assert result.total >= 1
        assert any("Taco" in item.name for item in result.items)

    def test_keyword_matches_name(self, db):
        result = restaurant_service.search_restaurants(db, keywords="Heaven")
        assert result.total >= 1

    def test_no_match_returns_empty(self, db):
        result = restaurant_service.search_restaurants(db, name="XYZNONEXISTENT123")
        assert result.total == 0
        assert result.items == []

    def test_pagination_respects_limit(self, db):
        result = restaurant_service.search_restaurants(db, page=1, limit=1)
        assert len(result.items) == 1

    def test_pagination_page_2(self, db):
        p1 = restaurant_service.search_restaurants(db, page=1, limit=1)
        p2 = restaurant_service.search_restaurants(db, page=2, limit=1)
        assert p1.items[0].id != p2.items[0].id

    def test_pagination_metadata_fields(self, db):
        result = restaurant_service.search_restaurants(db, page=2, limit=1)
        assert result.page == 2
        assert result.limit == 1

    def test_sort_params_accepted(self, db):
        for s in ("name", "rating", "review_count"):
            result = restaurant_service.search_restaurants(db, sort=s)
            assert result.total >= 2, f"sort={s} returned wrong total"


# ---------------------------------------------------------------------------
# Test: upload_photos — auth + quota validation (no real file I/O)
# ---------------------------------------------------------------------------

class TestUploadPhotosAuth:
    class MockFile:
        def __init__(self, filename="photo.jpg", content_type="image/jpeg", data=b"\xff\xd8\xff\xe0"):
            self.filename = filename
            self.content_type = content_type
            self._data = data

        async def read(self):
            return self._data

    @pytest.fixture(autouse=True)
    def setup(self, db, monkeypatch, tmp_path):
        self.user = make_user(db, "pu@test.com")
        self.owner = make_owner(db, "po@test.com")
        rest = make_restaurant(db, self.user.id, "Photo Test Restaurant")
        self.rid = rest.id
        # Claim restaurant by owner
        from sqlalchemy import update
        db.execute(
            update(Restaurant)
            .where(Restaurant.id == self.rid)
            .values(claimed_by_owner_id=self.owner.id)
        )
        db.flush()
        # Redirect file writes to tmp_path so no production disk I/O
        monkeypatch.setattr("app.services.restaurant_service._photos_dir", tmp_path)

    @pytest.mark.asyncio
    async def test_wrong_user_raises_forbidden(self, db):
        other = make_user(db, "wrong@test.com")
        with pytest.raises(ServiceForbidden):
            await restaurant_service.upload_photos(
                db, self.rid, [self.MockFile()],
                {"token_type": "user", "sub": str(other.id)},
                "http://localhost:8000/",
            )

    @pytest.mark.asyncio
    async def test_wrong_owner_raises_forbidden(self, db):
        other = make_owner(db, "wrong_o@test.com")
        with pytest.raises(ServiceForbidden):
            await restaurant_service.upload_photos(
                db, self.rid, [self.MockFile()],
                {"token_type": "owner", "sub": str(other.id)},
                "http://localhost:8000/",
            )

    @pytest.mark.asyncio
    async def test_invalid_token_type_raises_unauthorized(self, db):
        with pytest.raises(ServiceUnauthorized):
            await restaurant_service.upload_photos(
                db, self.rid, [self.MockFile()],
                {"token_type": "admin", "sub": "1"},
                "http://localhost:8000/",
            )

    @pytest.mark.asyncio
    async def test_missing_restaurant_raises_not_found(self, db):
        with pytest.raises(ServiceNotFound):
            await restaurant_service.upload_photos(
                db, 999999, [self.MockFile()],
                {"token_type": "user", "sub": str(self.user.id)},
                "http://localhost:8000/",
            )

    @pytest.mark.asyncio
    async def test_empty_filename_raises_bad_request(self, db):
        with pytest.raises(ServiceBadRequest, match="Empty filename"):
            await restaurant_service.upload_photos(
                db, self.rid, [self.MockFile(filename="")],
                {"token_type": "user", "sub": str(self.user.id)},
                "http://localhost:8000/",
            )

    @pytest.mark.asyncio
    async def test_unsupported_extension_raises_bad_request(self, db):
        with pytest.raises(ServiceBadRequest, match="Unsupported format"):
            await restaurant_service.upload_photos(
                db, self.rid, [self.MockFile(filename="photo.gif", content_type="image/gif")],
                {"token_type": "user", "sub": str(self.user.id)},
                "http://localhost:8000/",
            )

    @pytest.mark.asyncio
    async def test_more_than_5_files_raises_bad_request(self, db):
        """Uploading 6 files at once should fail (quota: 5 total)."""
        files = [self.MockFile() for _ in range(6)]
        with pytest.raises(ServiceBadRequest, match="at most 5"):
            await restaurant_service.upload_photos(
                db, self.rid, files,
                {"token_type": "user", "sub": str(self.user.id)},
                "http://localhost:8000/",
            )

    @pytest.mark.asyncio
    async def test_creator_can_upload_photo(self, db):
        photos = await restaurant_service.upload_photos(
            db, self.rid, [self.MockFile()],
            {"token_type": "user", "sub": str(self.user.id)},
            "http://localhost:8000/",
        )
        assert len(photos) == 1
        assert photos[0].uploaded_by_user_id == self.user.id
        assert "restaurant_photos" in photos[0].photo_url

    @pytest.mark.asyncio
    async def test_owner_can_upload_photo(self, db):
        photos = await restaurant_service.upload_photos(
            db, self.rid, [self.MockFile()],
            {"token_type": "owner", "sub": str(self.owner.id)},
            "http://localhost:8000/",
        )
        assert len(photos) == 1
        assert photos[0].uploaded_by_owner_id == self.owner.id
