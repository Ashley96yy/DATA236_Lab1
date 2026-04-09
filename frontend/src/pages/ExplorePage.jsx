import { useEffect, useRef } from "react";
import { useNavigate } from "react-router-dom";

import RestaurantCard from "../components/RestaurantCard";
import { useAppDispatch, useAppSelector } from "../store/hooks";
import {
  fetchRestaurants,
  setRestaurantFilter,
  setRestaurantPage,
} from "../store/slices/restaurantSlice";

const SORT_OPTIONS = [
  { value: "name", label: "Name (A–Z)" },
  { value: "rating", label: "Top Rated" },
  { value: "review_count", label: "Most Reviewed" },
];


export default function ExplorePage() {
  const navigate = useNavigate();
  const dispatch = useAppDispatch();
  const { filters, page, results, loadingList: loading, listError: error } = useAppSelector(
    (state) => state.restaurants
  );

  const debounceRef = useRef(null);

  function updateFilter(key, value) {
    dispatch(setRestaurantFilter({ key, value }));
  }

  useEffect(() => {
    if (debounceRef.current) clearTimeout(debounceRef.current);
    debounceRef.current = setTimeout(() => {
      dispatch(fetchRestaurants({ filters, page, limit: 12 }));
    }, 300);
    return () => clearTimeout(debounceRef.current);
  }, [dispatch, filters, page]);

  const totalPages = results ? Math.ceil(results.total / results.limit) : 1;

  return (
    <div className="explore-page">
      {/* ── Hero ── */}
      <div className="explore-hero">
        <h1 className="explore-hero-title">Find Your Next Favourite Spot</h1>
        <p className="explore-hero-sub">
          Explore thousands of restaurants by name, cuisine, city, or keyword.
        </p>
      </div>

      {/* ── Filter bar ── */}
      <div className="explore-filters">
        <input
          id="filter-name"
          className="filter-input"
          type="text"
          placeholder="Restaurant name…"
          value={filters.name}
          onChange={(e) => updateFilter("name", e.target.value)}
        />
        <input
          id="filter-cuisine"
          className="filter-input"
          type="text"
          placeholder="Cuisine (e.g. Italian)…"
          value={filters.cuisine}
          onChange={(e) => updateFilter("cuisine", e.target.value)}
        />
        <input
          id="filter-keywords"
          className="filter-input"
          type="text"
          placeholder="Keywords (WiFi, Vegan…)"
          value={filters.keywords}
          onChange={(e) => updateFilter("keywords", e.target.value)}
        />
        <input
          id="filter-city"
          className="filter-input"
          type="text"
          placeholder="City…"
          value={filters.city}
          onChange={(e) => updateFilter("city", e.target.value)}
        />
        <input
          id="filter-zip"
          className="filter-input filter-input--sm"
          type="text"
          placeholder="Zip…"
          value={filters.zip}
          onChange={(e) => updateFilter("zip", e.target.value)}
        />
        <select
          id="filter-sort"
          className="filter-select"
          value={filters.sort}
          onChange={(e) => updateFilter("sort", e.target.value)}
        >
          {SORT_OPTIONS.map((o) => (
            <option key={o.value} value={o.value}>{o.label}</option>
          ))}
        </select>
      </div>

      {/* ── Error banner ── */}
      {error && (
        <div className="alert alert--error" role="alert">
          {error}
        </div>
      )}

      {/* ── Results ── */}
      {loading && !results && (
        <div className="explore-status">
          <div className="spinner" />
          <p>Loading restaurants…</p>
        </div>
      )}

      {results && results.items.length === 0 && !loading && (
        <div className="explore-empty">
          <p className="explore-empty-icon">🍽️</p>
          <h2>No restaurants found</h2>
          <p className="muted">Try different filters or{" "}
            <button className="btn-link" onClick={() => navigate("/add-restaurant")}>
              add the first one
            </button>.
          </p>
        </div>
      )}

      {results && results.items.length > 0 && (
        <>
          <p className="explore-count">
            {loading ? "Refreshing…" : `${results.total} restaurant${results.total !== 1 ? "s" : ""} found`}
          </p>
          <div className="restaurant-grid">
            {results.items.map((r) => (
              <RestaurantCard
                key={r.id}
                restaurant={r}
                onClick={() => navigate(`/restaurant/${r.id}`)}
              />
            ))}
          </div>

          {/* Pagination */}
          {totalPages > 1 && (
            <div className="pagination">
              <button
                className="btn-page"
                disabled={page === 1 || loading}
                onClick={() => dispatch(setRestaurantPage(page - 1))}
              >
                ← Previous
              </button>
              <span className="page-info">Page {page} of {totalPages}</span>
              <button
                className="btn-page"
                disabled={page >= totalPages || loading}
                onClick={() => dispatch(setRestaurantPage(page + 1))}
              >
                Next →
              </button>
            </div>
          )}
        </>
      )}
    </div>
  );
}
