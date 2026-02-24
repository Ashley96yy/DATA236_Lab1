"""
Unit tests for app/services/review_service.py — Phase 4.

Run with:
    cd backend
    source venv/bin/activate
    pytest tests/test_review_service.py -v

Uses the live yelp_lab1 DB; each test rolls back via SAVEPOINT so no data persists.
"""
from __future__ import annotations

import pytest
from sqlalchemy.orm import Session

from app.models.owner import Owner  # noqa: F401 — ensure model is registered
from app.models.restaurant import Restaurant
from app.models.restaurant_photo import RestaurantPhoto  # noqa: F401
from app.models.review import Review
from app.models.user import User
from app.models.user_preference import UserPreference  # noqa: F401
from app.schemas.restaurant import RestaurantCreate
from app.schemas.review import ReviewCreate, ReviewUpdate
from app.services import restaurant_service, review_service
from app.services.errors import ServiceConflict, ServiceForbidden, ServiceNotFound


# ---------------------------------------------------------------------------
# Fixtures — mirrors test_restaurant_service.py
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

def make_user(db: Session, email: str = "u@review.com", name: str = "Alice") -> User:
    u = User(name=name, email=email, password_hash="hashed")
    db.add(u)
    db.flush()
    return u


def make_restaurant(db: Session, user_id: int) -> int:
    """Create a restaurant and return its id."""
    resp = restaurant_service.create_restaurant(
        db,
        RestaurantCreate(name="Review Spot", city="Testville"),
        user_id,
    )
    return resp.id


# ---------------------------------------------------------------------------
# TestCreateReview
# ---------------------------------------------------------------------------

class TestCreateReview:
    def test_creates_review_and_returns_response(self, db):
        u = make_user(db)
        rid = make_restaurant(db, u.id)

        data = ReviewCreate(rating=4, comment="Great place")
        resp = review_service.create_review(db, rid, data, u.id)

        assert resp.id is not None
        assert resp.restaurant_id == rid
        assert resp.rating == 4
        assert resp.comment == "Great place"
        assert resp.user_name == u.name

    def test_comment_is_optional(self, db):
        u = make_user(db, "u2@review.com")
        rid = make_restaurant(db, u.id)

        data = ReviewCreate(rating=3)
        resp = review_service.create_review(db, rid, data, u.id)

        assert resp.comment is None
        assert resp.rating == 3

    def test_duplicate_raises_service_conflict(self, db):
        u = make_user(db, "u3@review.com")
        rid = make_restaurant(db, u.id)

        review_service.create_review(db, rid, ReviewCreate(rating=5), u.id)

        with pytest.raises(ServiceConflict):
            review_service.create_review(db, rid, ReviewCreate(rating=1), u.id)

    def test_two_different_users_can_review_same_restaurant(self, db):
        u1 = make_user(db, "u4a@review.com", "Bob")
        u2 = make_user(db, "u4b@review.com", "Carol")
        rid = make_restaurant(db, u1.id)

        r1 = review_service.create_review(db, rid, ReviewCreate(rating=5), u1.id)
        r2 = review_service.create_review(db, rid, ReviewCreate(rating=2), u2.id)

        assert r1.id != r2.id


# ---------------------------------------------------------------------------
# TestUpdateReview
# ---------------------------------------------------------------------------

class TestUpdateReview:
    def _setup(self, db):
        u = make_user(db, "upd@review.com")
        rid = make_restaurant(db, u.id)
        rv = review_service.create_review(db, rid, ReviewCreate(rating=3, comment="OK"), u.id)
        return u, rv

    def test_update_rating(self, db):
        u, rv = self._setup(db)
        updated = review_service.update_review(db, rv.id, ReviewUpdate(rating=5), u.id)
        assert updated.rating == 5
        assert updated.comment == "OK"  # unchanged

    def test_update_comment(self, db):
        u, rv = self._setup(db)
        updated = review_service.update_review(db, rv.id, ReviewUpdate(comment="Better!"), u.id)
        assert updated.comment == "Better!"
        assert updated.rating == 3  # unchanged

    def test_update_both_fields(self, db):
        u, rv = self._setup(db)
        updated = review_service.update_review(
            db, rv.id, ReviewUpdate(rating=1, comment="Changed mind"), u.id
        )
        assert updated.rating == 1
        assert updated.comment == "Changed mind"

    def test_not_found_raises_service_not_found(self, db):
        u = make_user(db, "nf@review.com")
        with pytest.raises(ServiceNotFound):
            review_service.update_review(db, 999999, ReviewUpdate(rating=1), u.id)

    def test_wrong_owner_raises_service_forbidden(self, db):
        u1 = make_user(db, "own1@review.com", "Dave")
        u2 = make_user(db, "own2@review.com", "Eve")
        rid = make_restaurant(db, u1.id)
        rv = review_service.create_review(db, rid, ReviewCreate(rating=4), u1.id)

        with pytest.raises(ServiceForbidden):
            review_service.update_review(db, rv.id, ReviewUpdate(rating=1), u2.id)


# ---------------------------------------------------------------------------
# TestDeleteReview
# ---------------------------------------------------------------------------

class TestDeleteReview:
    def _setup(self, db):
        u = make_user(db, "del@review.com")
        rid = make_restaurant(db, u.id)
        rv = review_service.create_review(db, rid, ReviewCreate(rating=3), u.id)
        return u, rv

    def test_delete_own_review(self, db):
        u, rv = self._setup(db)
        review_service.delete_review(db, rv.id, u.id)
        # Confirm gone
        result = review_service.get_reviews_for_restaurant(db, rv.restaurant_id)
        ids = [r.id for r in result["items"]]
        assert rv.id not in ids

    def test_not_found_raises_service_not_found(self, db):
        u = make_user(db, "nfdel@review.com")
        with pytest.raises(ServiceNotFound):
            review_service.delete_review(db, 999999, u.id)

    def test_wrong_owner_raises_service_forbidden(self, db):
        u1 = make_user(db, "del1@review.com", "Frank")
        u2 = make_user(db, "del2@review.com", "Grace")
        rid = make_restaurant(db, u1.id)
        rv = review_service.create_review(db, rid, ReviewCreate(rating=4), u1.id)

        with pytest.raises(ServiceForbidden):
            review_service.delete_review(db, rv.id, u2.id)


# ---------------------------------------------------------------------------
# TestGetReviewsForRestaurant
# ---------------------------------------------------------------------------

class TestGetReviewsForRestaurant:
    def test_returns_empty_when_no_reviews(self, db):
        u = make_user(db, "empty@review.com")
        rid = make_restaurant(db, u.id)

        result = review_service.get_reviews_for_restaurant(db, rid)
        assert result["total"] == 0
        assert result["items"] == []

    def test_includes_user_name(self, db):
        u = make_user(db, "named@review.com", "Helen")
        rid = make_restaurant(db, u.id)
        review_service.create_review(db, rid, ReviewCreate(rating=4), u.id)

        result = review_service.get_reviews_for_restaurant(db, rid)
        assert result["items"][0].user_name == "Helen"

    def test_pagination(self, db):
        u1 = make_user(db, "pg1@review.com", "Iris")
        u2 = make_user(db, "pg2@review.com", "Jack")
        u3 = make_user(db, "pg3@review.com", "Kara")
        rid = make_restaurant(db, u1.id)

        for u in [u1, u2, u3]:
            review_service.create_review(db, rid, ReviewCreate(rating=3), u.id)

        page1 = review_service.get_reviews_for_restaurant(db, rid, page=1, limit=2)
        page2 = review_service.get_reviews_for_restaurant(db, rid, page=2, limit=2)

        assert page1["total"] == 3
        assert len(page1["items"]) == 2
        assert len(page2["items"]) == 1

    def test_ordered_newest_first(self, db):
        u1 = make_user(db, "ord1@review.com", "Leo")
        u2 = make_user(db, "ord2@review.com", "Mia")
        rid = make_restaurant(db, u1.id)

        rv1 = review_service.create_review(db, rid, ReviewCreate(rating=2), u1.id)
        rv2 = review_service.create_review(db, rid, ReviewCreate(rating=5), u2.id)

        result = review_service.get_reviews_for_restaurant(db, rid)
        # Newest (rv2) should appear first
        assert result["items"][0].id == rv2.id
        assert result["items"][1].id == rv1.id


# ---------------------------------------------------------------------------
# TestGetAvgRating
# ---------------------------------------------------------------------------

class TestGetAvgRating:
    def test_no_reviews_returns_zero(self, db):
        u = make_user(db, "avg0@review.com")
        rid = make_restaurant(db, u.id)

        avg, cnt = review_service.get_avg_rating(db, rid)
        assert avg == 0.0
        assert cnt == 0

    def test_single_review(self, db):
        u = make_user(db, "avg1@review.com")
        rid = make_restaurant(db, u.id)
        review_service.create_review(db, rid, ReviewCreate(rating=4), u.id)

        avg, cnt = review_service.get_avg_rating(db, rid)
        assert avg == 4.0
        assert cnt == 1

    def test_multiple_reviews_average(self, db):
        u1 = make_user(db, "avgm1@review.com", "Nina")
        u2 = make_user(db, "avgm2@review.com", "Omar")
        u3 = make_user(db, "avgm3@review.com", "Pam")
        rid = make_restaurant(db, u1.id)

        for u, rating in [(u1, 2), (u2, 4), (u3, 3)]:
            review_service.create_review(db, rid, ReviewCreate(rating=rating), u.id)

        avg, cnt = review_service.get_avg_rating(db, rid)
        assert avg == 3.0
        assert cnt == 3

    def test_rating_is_rounded_to_two_decimals(self, db):
        users = [make_user(db, f"rnd{i}@review.com", f"U{i}") for i in range(3)]
        rid = make_restaurant(db, users[0].id)

        for u, rating in zip(users, [1, 2, 5]):
            review_service.create_review(db, rid, ReviewCreate(rating=rating), u.id)

        avg, _ = review_service.get_avg_rating(db, rid)
        # 8/3 = 2.666... → rounds to 2.67
        assert avg == round(8 / 3, 2)
