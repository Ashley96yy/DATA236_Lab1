import { useEffect, useState } from "react";
import { Link, useNavigate } from "react-router-dom";

import RestaurantCard from "../components/RestaurantCard";
import { useAppDispatch, useAppSelector } from "../store/hooks";
import {
  fetchFavoritesPage,
  fetchHistory,
  setFavoritesPage,
} from "../store/slices/favoritesSlice";

const LIMIT = 10;

function StarDisplay({ rating }) {
  return (
    <span className="star-rating" aria-label={`${rating} out of 5`}>
      {[1, 2, 3, 4, 5].map((i) => (
        <span key={i} className={i <= rating ? "star filled" : "star"}>★</span>
      ))}
    </span>
  );
}

export default function DashboardPage() {
  const navigate = useNavigate();
  const dispatch = useAppDispatch();
  const [tab, setTab] = useState("favorites");
  const {
    paged: favorites,
    page: favPage,
    listLoading: favLoading,
    listError: favError,
    history,
    historyLoading: histLoading,
    historyError: histError,
  } = useAppSelector((state) => state.favorites);

  // Load favorites whenever tab is active or page changes
  useEffect(() => {
    if (tab === "favorites") {
      dispatch(fetchFavoritesPage({ page: favPage, limit: LIMIT }));
    }
  }, [dispatch, tab, favPage]);

  // Load history once when tab first opened
  useEffect(() => {
    if (tab === "history" && history === null) {
      dispatch(fetchHistory());
    }
  }, [dispatch, history, tab]);

  const favTotalPages = favorites ? Math.ceil(favorites.total / LIMIT) : 1;

  return (
    <div className="dashboard-page">
      <h1 className="dashboard-title">My Dashboard</h1>

      {/* ── Tab bar ── */}
      <div className="dashboard-tabs">
        <button
          type="button"
          className={`tab-btn${tab === "favorites" ? " tab-btn--active" : ""}`}
          onClick={() => setTab("favorites")}
        >
          ❤️ Favorites
          {favorites && <span className="tab-count">{favorites.total}</span>}
        </button>
        <button
          type="button"
          className={`tab-btn${tab === "history" ? " tab-btn--active" : ""}`}
          onClick={() => setTab("history")}
        >
          📋 History
        </button>
      </div>

      {/* ── Favorites tab ── */}
      {tab === "favorites" && (
        <div className="dashboard-panel">
          {favLoading && (
            <div className="explore-status">
              <div className="spinner" />
            </div>
          )}
          {favError && <div className="alert alert--error">{favError}</div>}

          {!favLoading && favorites && favorites.items.length === 0 && (
            <div className="dashboard-empty">
              <p className="dashboard-empty-icon">🤍</p>
              <p>No favorites yet.</p>
              <Link to="/" className="btn-primary" style={{ display: "inline-block", marginTop: 12 }}>
                Explore restaurants
              </Link>
            </div>
          )}

          {favorites && favorites.items.length > 0 && (
            <>
              <p className="dashboard-count">
                {favorites.total} favorited restaurant{favorites.total !== 1 ? "s" : ""}
              </p>
              <div className="restaurant-grid">
                {favorites.items.map((r) => (
                  <RestaurantCard
                    key={r.id}
                    restaurant={r}
                    onClick={() => navigate(`/restaurant/${r.id}`)}
                  />
                ))}
              </div>

              {favTotalPages > 1 && (
                <div className="pagination">
                  <button
                    className="btn-page"
                    disabled={favPage === 1 || favLoading}
                    onClick={() => dispatch(setFavoritesPage(favPage - 1))}
                  >
                    ← Previous
                  </button>
                  <span className="page-info">Page {favPage} of {favTotalPages}</span>
                  <button
                    className="btn-page"
                    disabled={favPage >= favTotalPages || favLoading}
                    onClick={() => dispatch(setFavoritesPage(favPage + 1))}
                  >
                    Next →
                  </button>
                </div>
              )}
            </>
          )}
        </div>
      )}

      {/* ── History tab ── */}
      {tab === "history" && (
        <div className="dashboard-panel">
          {histLoading && (
            <div className="explore-status">
              <div className="spinner" />
            </div>
          )}
          {histError && <div className="alert alert--error">{histError}</div>}

          {history && (
            <>
              {/* My Reviews */}
              <section className="history-section">
                <h2 className="history-heading">My Reviews</h2>
                {history.my_reviews.length === 0 ? (
                  <p className="muted">You haven't written any reviews yet.</p>
                ) : (
                  <div className="history-review-list">
                    {history.my_reviews.map((rv) => (
                      <div key={rv.id} className="history-review-card">
                        <div className="history-review-top">
                          <span
                            className="history-restaurant-name"
                            onClick={() => navigate(`/restaurant/${rv.restaurant_id}`)}
                            role="button"
                            tabIndex={0}
                            onKeyDown={(e) => e.key === "Enter" && navigate(`/restaurant/${rv.restaurant_id}`)}
                          >
                            {rv.restaurant_name}
                          </span>
                          <StarDisplay rating={rv.rating} />
                          <span className="history-review-date">
                            {new Date(rv.created_at).toLocaleDateString()}
                          </span>
                        </div>
                        {rv.comment && (
                          <p className="history-review-comment">{rv.comment}</p>
                        )}
                      </div>
                    ))}
                  </div>
                )}
              </section>

              {/* Restaurants I Added */}
              <section className="history-section">
                <h2 className="history-heading">Restaurants I Added</h2>
                {history.my_restaurants_added.length === 0 ? (
                  <p className="muted">
                    You haven't added any restaurants yet.{" "}
                    <Link to="/add-restaurant">Add one now</Link>
                  </p>
                ) : (
                  <div className="restaurant-grid">
                    {history.my_restaurants_added.map((r) => (
                      <RestaurantCard
                        key={r.id}
                        restaurant={r}
                        onClick={() => navigate(`/restaurant/${r.id}`)}
                      />
                    ))}
                  </div>
                )}
              </section>
            </>
          )}
        </div>
      )}
    </div>
  );
}
