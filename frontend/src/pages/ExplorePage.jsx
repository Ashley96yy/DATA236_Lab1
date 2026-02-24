import { useEffect, useRef, useState } from "react";
import { useNavigate } from "react-router-dom";
import api, { extractApiError } from "../services/api";

const SORT_OPTIONS = [
  { value: "name", label: "Name (A–Z)" },
  { value: "rating", label: "Top Rated" },
  { value: "review_count", label: "Most Reviewed" },
];

const PRICING_LABELS = {
  $: "$ · Inexpensive",
  $$: "$$ · Moderate",
  $$$: "$$$ · Expensive",
  $$$$: "$$$$ · Very Expensive",
};

function StarRating({ rating }) {
  const stars = Math.round(rating);
  return (
    <span className="star-rating" aria-label={`${rating} out of 5`}>
      {[1, 2, 3, 4, 5].map((i) => (
        <span key={i} className={i <= stars ? "star filled" : "star"}>
          ★
        </span>
      ))}
    </span>
  );
}

function RestaurantCardItem({ restaurant, onClick }) {
  const amenityList = Array.isArray(restaurant.amenities)
    ? restaurant.amenities.slice(0, 3)
    : [];

  return (
    <article className="restaurant-card" onClick={onClick} tabIndex={0}
      onKeyDown={(e) => e.key === "Enter" && onClick()}
      role="button" aria-label={`View details for ${restaurant.name}`}>
      <div className="rc-photo">
        {restaurant.cover_photo_url ? (
          <img src={restaurant.cover_photo_url} alt={restaurant.name} />
        ) : (
          <div className="rc-photo-placeholder">
            <span>🍴</span>
          </div>
        )}
        {restaurant.pricing_tier && (
          <span className="rc-badge">{restaurant.pricing_tier}</span>
        )}
      </div>
      <div className="rc-body">
        <h3 className="rc-name">{restaurant.name}</h3>
        <p className="rc-meta">
          {restaurant.cuisine_type && (
            <span className="rc-cuisine">{restaurant.cuisine_type}</span>
          )}
          <span className="rc-location">
            {restaurant.city}{restaurant.state ? `, ${restaurant.state}` : ""}
          </span>
        </p>
        {restaurant.average_rating > 0 ? (
          <div className="rc-rating">
            <StarRating rating={restaurant.average_rating} />
            <span className="rc-review-count">({restaurant.review_count})</span>
          </div>
        ) : (
          <p className="rc-no-reviews">No reviews yet</p>
        )}
        {restaurant.description && (
          <p className="rc-description">{restaurant.description.slice(0, 100)}{restaurant.description.length > 100 ? "…" : ""}</p>
        )}
        {amenityList.length > 0 && (
          <div className="rc-amenities">
            {amenityList.map((a) => (
              <span key={a} className="rc-amenity-tag">{a}</span>
            ))}
          </div>
        )}
      </div>
    </article>
  );
}

export default function ExplorePage() {
  const navigate = useNavigate();

  const [filters, setFilters] = useState({
    name: "",
    cuisine: "",
    keywords: "",
    city: "",
    zip: "",
    sort: "name",
  });
  const [page, setPage] = useState(1);
  const [results, setResults] = useState(null); // null = not yet loaded
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState("");

  const debounceRef = useRef(null);

  function updateFilter(key, value) {
    setFilters((prev) => ({ ...prev, [key]: value }));
    setPage(1);
  }

  useEffect(() => {
    if (debounceRef.current) clearTimeout(debounceRef.current);
    debounceRef.current = setTimeout(() => {
      fetchRestaurants();
    }, 300);
    return () => clearTimeout(debounceRef.current);
  }, [filters, page]);

  async function fetchRestaurants() {
    setLoading(true);
    setError("");
    try {
      const params = {};
      if (filters.name) params.name = filters.name;
      if (filters.cuisine) params.cuisine = filters.cuisine;
      if (filters.keywords) params.keywords = filters.keywords;
      if (filters.city) params.city = filters.city;
      if (filters.zip) params.zip = filters.zip;
      if (filters.sort) params.sort = filters.sort;
      params.page = page;
      params.limit = 12;

      const resp = await api.get("/restaurants", { params });
      setResults(resp.data);
    } catch (err) {
      setError(extractApiError(err, "Failed to load restaurants."));
      setResults({ items: [], total: 0, page: 1, limit: 12 });
    } finally {
      setLoading(false);
    }
  }

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
              <RestaurantCardItem
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
                onClick={() => setPage((p) => p - 1)}
              >
                ← Previous
              </button>
              <span className="page-info">Page {page} of {totalPages}</span>
              <button
                className="btn-page"
                disabled={page >= totalPages || loading}
                onClick={() => setPage((p) => p + 1)}
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
