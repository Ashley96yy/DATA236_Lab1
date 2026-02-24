"""
Unit tests for app/services/favorite_service.py — Phase 5.

Run with:
    cd backend
    source venv/bin/activate
    pytest tests/test_favorite_service.py -v

Uses the live yelp_lab1 DB with per-test transaction rollback via SAVEPOINT.
"""
from __future__ import annotations

import pytest
from sqlalchemy.orm import Session

from app.models.favorite import Favorite  # noqa: F401 — registers model
from app.models.owner import Owner  # noqa: F401
from app.models.restaurant import Restaurant
from app.models.restaurant_photo import RestaurantPhoto  # noqa: F401
from app.models.review import Review
from app.models.user import User
from app.models.user_preference import UserPreference  # noqa: F401
from app.schemas.restaurant import RestaurantCreate
from app.schemas.review import ReviewCreate
from app.services import favorite_service, restaurant_service, review_service
from app.services.errors import ServiceConflict, ServiceNotFound


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

def make_user(db: Session, email: str = "u@fav.com", name: str = "Alice") -> User:
    u = User(name=name, email=email, password_hash="hashed")
    db.add(u)
    db.flush()
    return u


def make_restaurant(db: Session, user_id: int, name: str = "Fav Spot") -> int:
    resp = restaurant_service.create_restaurant(
        db,
        RestaurantCreate(name=name, city="Testville"),
        user_id,
    )
    return resp.id


# ---------------------------------------------------------------------------
# TestAddFavorite
# ---------------------------------------------------------------------------

class TestAddFavorite:
    def test_add_favorite_returns_status(self, db):
        u = make_user(db)
        rid = make_restaurant(db, u.id)

        resp = favorite_service.add_favorite(db, rid, u.id)

        assert resp.restaurant_id == rid
        assert resp.favorited is True

    def test_duplicate_raises_service_conflict(self, db):
        u = make_user(db, "dup@fav.com")
        rid = make_restaurant(db, u.id)

        favorite_service.add_favorite(db, rid, u.id)

        with pytest.raises(ServiceConflict):
            favorite_service.add_favorite(db, rid, u.id)

    def test_nonexistent_restaurant_raises_service_not_found(self, db):
        u = make_user(db, "nf@fav.com")
        with pytest.raises(ServiceNotFound):
            favorite_service.add_favorite(db, 999999, u.id)

    def test_two_users_can_favorite_same_restaurant(self, db):
        u1 = make_user(db, "u1@fav.com", "Bob")
        u2 = make_user(db, "u2@fav.com", "Carol")
        rid = make_restaurant(db, u1.id)

        r1 = favorite_service.add_favorite(db, rid, u1.id)
        r2 = favorite_service.add_favorite(db, rid, u2.id)

        assert r1.favorited is True
        assert r2.favorited is True

    def test_same_user_can_favorite_different_restaurants(self, db):
        u = make_user(db, "multi@fav.com")
        rid1 = make_restaurant(db, u.id, "Place A")
        rid2 = make_restaurant(db, u.id, "Place B")

        favorite_service.add_favorite(db, rid1, u.id)
        favorite_service.add_favorite(db, rid2, u.id)

        resp = favorite_service.get_favorites(db, u.id)
        ids = [item.id for item in resp.items]
        assert rid1 in ids
        assert rid2 in ids


# ---------------------------------------------------------------------------
# TestRemoveFavorite
# ---------------------------------------------------------------------------

class TestRemoveFavorite:
    def test_remove_existing_favorite(self, db):
        u = make_user(db, "rm@fav.com")
        rid = make_restaurant(db, u.id)

        favorite_service.add_favorite(db, rid, u.id)
        favorite_service.remove_favorite(db, rid, u.id)

        resp = favorite_service.get_favorites(db, u.id)
        assert not any(item.id == rid for item in resp.items)

    def test_remove_non_existing_raises_service_not_found(self, db):
        u = make_user(db, "rmnf@fav.com")
        rid = make_restaurant(db, u.id)

        with pytest.raises(ServiceNotFound):
            favorite_service.remove_favorite(db, rid, u.id)

    def test_remove_other_users_favorite_raises_service_not_found(self, db):
        u1 = make_user(db, "rmown1@fav.com", "Dave")
        u2 = make_user(db, "rmown2@fav.com", "Eve")
        rid = make_restaurant(db, u1.id)

        favorite_service.add_favorite(db, rid, u1.id)

        # u2 never favorited it → 404
        with pytest.raises(ServiceNotFound):
            favorite_service.remove_favorite(db, rid, u2.id)

    def test_remove_is_not_idempotent(self, db):
        u = make_user(db, "rmtwice@fav.com")
        rid = make_restaurant(db, u.id)

        favorite_service.add_favorite(db, rid, u.id)
        favorite_service.remove_favorite(db, rid, u.id)

        with pytest.raises(ServiceNotFound):
            favorite_service.remove_favorite(db, rid, u.id)


# ---------------------------------------------------------------------------
# TestGetFavorites
# ---------------------------------------------------------------------------

class TestGetFavorites:
    def test_empty_when_no_favorites(self, db):
        u = make_user(db, "empty@fav.com")
        resp = favorite_service.get_favorites(db, u.id)

        assert resp.total == 0
        assert resp.items == []

    def test_returns_restaurant_card(self, db):
        u = make_user(db, "card@fav.com")
        rid = make_restaurant(db, u.id, "Card Test")

        favorite_service.add_favorite(db, rid, u.id)
        resp = favorite_service.get_favorites(db, u.id)

        assert resp.total == 1
        assert resp.items[0].id == rid
        assert resp.items[0].name == "Card Test"

    def test_pagination(self, db):
        u = make_user(db, "pg@fav.com")
        rids = [make_restaurant(db, u.id, f"Spot {i}") for i in range(5)]
        for rid in rids:
            favorite_service.add_favorite(db, rid, u.id)

        page1 = favorite_service.get_favorites(db, u.id, page=1, limit=3)
        page2 = favorite_service.get_favorites(db, u.id, page=2, limit=3)

        assert page1.total == 5
        assert len(page1.items) == 3
        assert len(page2.items) == 2

    def test_newest_favorited_first(self, db):
        u = make_user(db, "order@fav.com")
        rid1 = make_restaurant(db, u.id, "First")
        rid2 = make_restaurant(db, u.id, "Second")

        favorite_service.add_favorite(db, rid1, u.id)
        favorite_service.add_favorite(db, rid2, u.id)

        resp = favorite_service.get_favorites(db, u.id)
        # rid2 favorited last → appears first
        assert resp.items[0].id == rid2
        assert resp.items[1].id == rid1

    def test_unfavorited_restaurant_not_in_list(self, db):
        u = make_user(db, "unfav@fav.com")
        rid1 = make_restaurant(db, u.id, "Keep")
        rid2 = make_restaurant(db, u.id, "Remove")

        favorite_service.add_favorite(db, rid1, u.id)
        favorite_service.add_favorite(db, rid2, u.id)
        favorite_service.remove_favorite(db, rid2, u.id)

        resp = favorite_service.get_favorites(db, u.id)
        ids = [item.id for item in resp.items]
        assert rid1 in ids
        assert rid2 not in ids


# ---------------------------------------------------------------------------
# TestGetUserHistory
# ---------------------------------------------------------------------------

class TestGetUserHistory:
    def test_empty_history_for_new_user(self, db):
        u = make_user(db, "hist0@fav.com")
        hist = favorite_service.get_user_history(db, u.id)

        assert hist.my_reviews == []
        assert hist.my_restaurants_added == []

    def test_history_includes_restaurants_added(self, db):
        u = make_user(db, "hadd@fav.com")
        rid = make_restaurant(db, u.id, "My Place")

        hist = favorite_service.get_user_history(db, u.id)

        assert len(hist.my_restaurants_added) == 1
        assert hist.my_restaurants_added[0].id == rid
        assert hist.my_restaurants_added[0].name == "My Place"

    def test_history_includes_reviews_written(self, db):
        u = make_user(db, "hrev@fav.com")
        rid = make_restaurant(db, u.id, "Review Place")

        review_service.create_review(db, rid, ReviewCreate(rating=5, comment="Loved it"), u.id)

        hist = favorite_service.get_user_history(db, u.id)

        assert len(hist.my_reviews) == 1
        assert hist.my_reviews[0].restaurant_id == rid
        assert hist.my_reviews[0].restaurant_name == "Review Place"
        assert hist.my_reviews[0].rating == 5
        assert hist.my_reviews[0].comment == "Loved it"

    def test_history_reviews_are_newest_first(self, db):
        u1 = make_user(db, "hord1@fav.com", "Frank")
        u2 = make_user(db, "hord2@fav.com", "Grace")
        rid1 = make_restaurant(db, u1.id, "Spot A")
        rid2 = make_restaurant(db, u1.id, "Spot B")

        review_service.create_review(db, rid1, ReviewCreate(rating=3), u1.id)
        review_service.create_review(db, rid2, ReviewCreate(rating=5), u1.id)

        hist = favorite_service.get_user_history(db, u1.id)
        ids = [r.id for r in hist.my_reviews]
        # rid2 review was created last → appears first
        assert ids[0] > ids[1]

    def test_history_only_shows_own_restaurants(self, db):
        u1 = make_user(db, "hown1@fav.com", "Helen")
        u2 = make_user(db, "hown2@fav.com", "Ivan")
        make_restaurant(db, u1.id, "Helen's Place")
        make_restaurant(db, u2.id, "Ivan's Place")

        hist = favorite_service.get_user_history(db, u1.id)
        names = [r.name for r in hist.my_restaurants_added]
        assert "Helen's Place" in names
        assert "Ivan's Place" not in names

    def test_history_only_shows_own_reviews(self, db):
        u1 = make_user(db, "hrevown1@fav.com", "Jack")
        u2 = make_user(db, "hrevown2@fav.com", "Kara")
        rid = make_restaurant(db, u1.id)

        review_service.create_review(db, rid, ReviewCreate(rating=4), u1.id)
        # u2 writes a review on a different restaurant — shouldn't appear in u1's history
        rid2 = make_restaurant(db, u2.id, "Other Place")
        review_service.create_review(db, rid2, ReviewCreate(rating=2), u2.id)

        hist = favorite_service.get_user_history(db, u1.id)
        assert len(hist.my_reviews) == 1
        assert hist.my_reviews[0].restaurant_id == rid

    def test_history_review_includes_restaurant_name(self, db):
        u = make_user(db, "hrname@fav.com")
        rid = make_restaurant(db, u.id, "Named Place")

        review_service.create_review(db, rid, ReviewCreate(rating=4), u.id)

        hist = favorite_service.get_user_history(db, u.id)
        assert hist.my_reviews[0].restaurant_name == "Named Place"
