"""
Unit tests for app/services/owner_service.py — Phase 6.

Run with:
    cd backend
    source venv/bin/activate
    pytest tests/test_owner_service.py -v

Uses the live yelp_lab1 DB with per-test transaction rollback via SAVEPOINT.
"""
from __future__ import annotations

import pytest
from sqlalchemy.orm import Session

from app.models.favorite import Favorite  # noqa: F401
from app.models.owner import Owner
from app.models.restaurant import Restaurant
from app.models.restaurant_photo import RestaurantPhoto  # noqa: F401
from app.models.review import Review
from app.models.user import User
from app.models.user_preference import UserPreference  # noqa: F401
from app.schemas.owner import OwnerProfileUpdate, OwnerRestaurantUpdate
from app.schemas.restaurant import RestaurantCreate
from app.schemas.review import ReviewCreate
from app.services import owner_service, restaurant_service, review_service
from app.services.errors import ServiceConflict, ServiceForbidden, ServiceNotFound


# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------

@pytest.fixture(scope="session")
def engine():
    from app.db.session import engine as app_engine
    return app_engine


@pytest.fixture()
def db(engine):
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

_owner_counter = 0
_user_counter = 0


def make_owner(
    db: Session,
    name: str = "Owner One",
    location: str = "San Jose, CA",
) -> Owner:
    global _owner_counter
    _owner_counter += 1
    o = Owner(
        name=name,
        email=f"owner{_owner_counter}@test.com",
        password_hash="hashed",
        restaurant_location=location,
    )
    db.add(o)
    db.flush()
    return o


def make_user(db: Session, name: str = "User One") -> User:
    global _user_counter
    _user_counter += 1
    u = User(name=name, email=f"user{_user_counter}@test.com", password_hash="hashed")
    db.add(u)
    db.flush()
    return u


def make_restaurant(
    db: Session,
    name: str = "Test Restaurant",
    owner_id: int | None = None,
    user_id: int | None = None,
) -> Restaurant:
    r = Restaurant(
        name=name,
        cuisine_type="Italian",
        city="San Jose",
        state="CA",
        country="US",
        claimed_by_owner_id=owner_id,
        created_by_user_id=user_id,
    )
    db.add(r)
    db.flush()
    r.photos = []
    return r


def make_review(db: Session, restaurant_id: int, user_id: int, rating: int = 4) -> Review:
    r = Review(
        restaurant_id=restaurant_id,
        user_id=user_id,
        rating=rating,
        comment="Nice place",
    )
    db.add(r)
    db.flush()
    return r


# ---------------------------------------------------------------------------
# TestUpdateOwnerProfile
# ---------------------------------------------------------------------------

class TestUpdateOwnerProfile:
    def test_update_name_only(self, db: Session):
        owner = make_owner(db, name="Old Name")
        result = owner_service.update_owner_profile(db, owner, OwnerProfileUpdate(name="New Name"))
        assert result.name == "New Name"
        assert result.restaurant_location == "San Jose, CA"

    def test_update_location_only(self, db: Session):
        owner = make_owner(db, name="Alice", location="Old City, CA")
        result = owner_service.update_owner_profile(
            db, owner, OwnerProfileUpdate(restaurant_location="New City, NY")
        )
        assert result.restaurant_location == "New City, NY"
        assert result.name == "Alice"

    def test_update_both_fields(self, db: Session):
        owner = make_owner(db, name="Old", location="Old Location")
        result = owner_service.update_owner_profile(
            db, owner, OwnerProfileUpdate(name="New", restaurant_location="New Location")
        )
        assert result.name == "New"
        assert result.restaurant_location == "New Location"

    def test_empty_payload_no_change(self, db: Session):
        owner = make_owner(db, name="Stable", location="Stable City, CA")
        result = owner_service.update_owner_profile(db, owner, OwnerProfileUpdate())
        assert result.name == "Stable"
        assert result.restaurant_location == "Stable City, CA"

    def test_returns_profile_response_shape(self, db: Session):
        owner = make_owner(db)
        result = owner_service.update_owner_profile(db, owner, OwnerProfileUpdate(name="Bob"))
        assert result.id == owner.id
        assert result.email == owner.email
        assert result.name == "Bob"


# ---------------------------------------------------------------------------
# TestCreateOwnerRestaurant
# ---------------------------------------------------------------------------

class TestCreateOwnerRestaurant:
    def _payload(self, name: str = "New Bistro") -> RestaurantCreate:
        return RestaurantCreate(
            name=name,
            cuisine_type="French",
            city="Paris",
            state="CA",
            country="US",
        )

    def test_creates_restaurant(self, db: Session):
        owner = make_owner(db)
        result = owner_service.create_owner_restaurant(db, self._payload(), owner.id)
        assert result.name == "New Bistro"
        assert result.cuisine_type == "French"

    def test_claimed_by_owner_id_set(self, db: Session):
        owner = make_owner(db)
        result = owner_service.create_owner_restaurant(db, self._payload(), owner.id)
        assert result.claimed_by_owner_id == owner.id

    def test_created_by_user_id_is_null(self, db: Session):
        owner = make_owner(db)
        result = owner_service.create_owner_restaurant(db, self._payload(), owner.id)
        assert result.created_by_user_id is None

    def test_initial_ratings_are_zero(self, db: Session):
        owner = make_owner(db)
        result = owner_service.create_owner_restaurant(db, self._payload(), owner.id)
        assert result.average_rating == 0.0
        assert result.review_count == 0


# ---------------------------------------------------------------------------
# TestUpdateOwnerRestaurant
# ---------------------------------------------------------------------------

class TestUpdateOwnerRestaurant:
    def test_update_name(self, db: Session):
        owner = make_owner(db)
        r = make_restaurant(db, name="Original", owner_id=owner.id)
        result = owner_service.update_owner_restaurant(
            db, r.id, OwnerRestaurantUpdate(name="Updated"), owner.id
        )
        assert result.name == "Updated"

    def test_update_multiple_fields(self, db: Session):
        owner = make_owner(db)
        r = make_restaurant(db, owner_id=owner.id)
        result = owner_service.update_owner_restaurant(
            db, r.id, OwnerRestaurantUpdate(cuisine_type="Thai", city="Bangkok"), owner.id
        )
        assert result.cuisine_type == "Thai"
        assert result.city == "Bangkok"

    def test_not_found_raises(self, db: Session):
        owner = make_owner(db)
        with pytest.raises(ServiceNotFound):
            owner_service.update_owner_restaurant(
                db, 999_999, OwnerRestaurantUpdate(name="X"), owner.id
            )

    def test_not_owner_raises_forbidden(self, db: Session):
        owner_a = make_owner(db)
        owner_b = make_owner(db)
        r = make_restaurant(db, owner_id=owner_a.id)
        with pytest.raises(ServiceForbidden):
            owner_service.update_owner_restaurant(
                db, r.id, OwnerRestaurantUpdate(name="Hijack"), owner_b.id
            )

    def test_unclaimed_restaurant_raises_forbidden(self, db: Session):
        owner = make_owner(db)
        r = make_restaurant(db, owner_id=None)  # unclaimed
        with pytest.raises(ServiceForbidden):
            owner_service.update_owner_restaurant(
                db, r.id, OwnerRestaurantUpdate(name="X"), owner.id
            )


# ---------------------------------------------------------------------------
# TestClaimRestaurant
# ---------------------------------------------------------------------------

class TestClaimRestaurant:
    def test_claim_unclaimed(self, db: Session):
        owner = make_owner(db)
        r = make_restaurant(db, owner_id=None)
        result = owner_service.claim_restaurant(db, r.id, owner.id)
        assert result.restaurant_id == r.id
        assert result.claimed_by_owner_id == owner.id

    def test_claim_sets_owner_in_db(self, db: Session):
        owner = make_owner(db)
        r = make_restaurant(db, owner_id=None)
        owner_service.claim_restaurant(db, r.id, owner.id)
        db.refresh(r)
        assert r.claimed_by_owner_id == owner.id

    def test_claim_already_claimed_by_same_owner(self, db: Session):
        owner = make_owner(db)
        r = make_restaurant(db, owner_id=owner.id)
        with pytest.raises(ServiceConflict):
            owner_service.claim_restaurant(db, r.id, owner.id)

    def test_claim_already_claimed_by_other_owner(self, db: Session):
        owner_a = make_owner(db)
        owner_b = make_owner(db)
        r = make_restaurant(db, owner_id=owner_a.id)
        with pytest.raises(ServiceConflict):
            owner_service.claim_restaurant(db, r.id, owner_b.id)

    def test_claim_not_found(self, db: Session):
        owner = make_owner(db)
        with pytest.raises(ServiceNotFound):
            owner_service.claim_restaurant(db, 999_999, owner.id)


# ---------------------------------------------------------------------------
# TestGetOwnerRestaurantReviews
# ---------------------------------------------------------------------------

class TestGetOwnerRestaurantReviews:
    def test_returns_empty_for_no_reviews(self, db: Session):
        owner = make_owner(db)
        r = make_restaurant(db, owner_id=owner.id)
        result = owner_service.get_owner_restaurant_reviews(db, r.id, owner.id)
        assert result["items"] == []
        assert result["total"] == 0

    def test_returns_reviews(self, db: Session):
        owner = make_owner(db)
        user = make_user(db)
        r = make_restaurant(db, owner_id=owner.id)
        make_review(db, r.id, user.id, rating=5)
        result = owner_service.get_owner_restaurant_reviews(db, r.id, owner.id)
        assert result["total"] == 1
        assert result["items"][0].rating == 5

    def test_pagination(self, db: Session):
        owner = make_owner(db)
        r = make_restaurant(db, owner_id=owner.id)
        for _ in range(5):
            u = make_user(db)
            make_review(db, r.id, u.id)
        result = owner_service.get_owner_restaurant_reviews(db, r.id, owner.id, page=1, limit=3)
        assert result["total"] == 5
        assert len(result["items"]) == 3
        assert result["page"] == 1
        assert result["limit"] == 3

    def test_not_found_raises(self, db: Session):
        owner = make_owner(db)
        with pytest.raises(ServiceNotFound):
            owner_service.get_owner_restaurant_reviews(db, 999_999, owner.id)

    def test_not_owner_raises_forbidden(self, db: Session):
        owner_a = make_owner(db)
        owner_b = make_owner(db)
        r = make_restaurant(db, owner_id=owner_a.id)
        with pytest.raises(ServiceForbidden):
            owner_service.get_owner_restaurant_reviews(db, r.id, owner_b.id)


# ---------------------------------------------------------------------------
# TestGetOwnerDashboard
# ---------------------------------------------------------------------------

class TestGetOwnerDashboard:
    def test_no_claimed_restaurants(self, db: Session):
        owner = make_owner(db)
        result = owner_service.get_owner_dashboard(db, owner.id)
        assert result.claimed_count == 0
        assert result.total_reviews == 0
        assert result.avg_rating == 0.0
        assert result.claimed_restaurants == []

    def test_claimed_count(self, db: Session):
        owner = make_owner(db)
        make_restaurant(db, owner_id=owner.id)
        make_restaurant(db, owner_id=owner.id)
        result = owner_service.get_owner_dashboard(db, owner.id)
        assert result.claimed_count == 2

    def test_total_reviews_and_avg(self, db: Session):
        owner = make_owner(db)
        user = make_user(db)
        r = make_restaurant(db, owner_id=owner.id)
        make_review(db, r.id, user.id, rating=4)
        user2 = make_user(db)
        make_review(db, r.id, user2.id, rating=2)
        result = owner_service.get_owner_dashboard(db, owner.id)
        assert result.total_reviews == 2
        assert result.avg_rating == 3.0

    def test_rating_distribution_all_slots_filled(self, db: Session):
        owner = make_owner(db)
        result = owner_service.get_owner_dashboard(db, owner.id)
        assert set(result.rating_distribution.keys()) == {1, 2, 3, 4, 5}

    def test_rating_distribution_counts(self, db: Session):
        owner = make_owner(db)
        r = make_restaurant(db, owner_id=owner.id)
        u1 = make_user(db)
        u2 = make_user(db)
        u3 = make_user(db)
        make_review(db, r.id, u1.id, rating=5)
        make_review(db, r.id, u2.id, rating=5)
        make_review(db, r.id, u3.id, rating=3)
        result = owner_service.get_owner_dashboard(db, owner.id)
        assert result.rating_distribution[5] == 2
        assert result.rating_distribution[3] == 1
        assert result.rating_distribution[1] == 0

    def test_claimed_restaurants_list(self, db: Session):
        owner = make_owner(db)
        r = make_restaurant(db, name="My Restaurant", owner_id=owner.id)
        result = owner_service.get_owner_dashboard(db, owner.id)
        assert len(result.claimed_restaurants) == 1
        assert result.claimed_restaurants[0].name == "My Restaurant"

    def test_other_owners_restaurants_excluded(self, db: Session):
        owner_a = make_owner(db)
        owner_b = make_owner(db)
        make_restaurant(db, owner_id=owner_b.id)
        result = owner_service.get_owner_dashboard(db, owner_a.id)
        assert result.claimed_count == 0
