import { useEffect, useState } from "react";
import { Link, useNavigate } from "react-router-dom";

import { extractApiError, ownerMgmtApi } from "../services/api";

function StatCard({ label, value }) {
  return (
    <div className="owner-stat-card">
      <span className="owner-stat-value">{value}</span>
      <span className="owner-stat-label">{label}</span>
    </div>
  );
}

function RatingBar({ star, count, max }) {
  const pct = max > 0 ? Math.round((count / max) * 100) : 0;
  return (
    <div className="owner-rating-row">
      <span className="owner-rating-star">{star}★</span>
      <div className="owner-rating-bar-track">
        <div className="owner-rating-bar-fill" style={{ width: `${pct}%` }} />
      </div>
      <span className="owner-rating-count">{count}</span>
    </div>
  );
}

function OwnerRestaurantCard({ restaurant, onEdit, onReviews }) {
  return (
    <div className="owner-rc">
      <div className="owner-rc-body">
        <h3 className="owner-rc-name">{restaurant.name}</h3>
        <p className="owner-rc-meta">
          {restaurant.cuisine_type && (
            <span className="owner-rc-cuisine">{restaurant.cuisine_type}</span>
          )}
          <span className="owner-rc-location">
            {restaurant.city}{restaurant.state ? `, ${restaurant.state}` : ""}
          </span>
        </p>
        {restaurant.average_rating > 0 ? (
          <p className="owner-rc-rating">
            ★ {restaurant.average_rating.toFixed(1)}
            <span className="owner-rc-review-count"> ({restaurant.review_count} review{restaurant.review_count !== 1 ? "s" : ""})</span>
          </p>
        ) : (
          <p className="owner-rc-no-reviews">No reviews yet</p>
        )}
        {restaurant.pricing_tier && (
          <span className="owner-rc-tier">{restaurant.pricing_tier}</span>
        )}
      </div>
      <div className="owner-rc-actions">
        <button type="button" className="btn-owner-action" onClick={onEdit}>
          Edit
        </button>
        <button type="button" className="btn-owner-action btn-owner-action--secondary" onClick={onReviews}>
          Reviews
        </button>
      </div>
    </div>
  );
}

export { OwnerRestaurantCard };

export default function OwnerDashboardPage() {
  const navigate = useNavigate();
  const [data, setData] = useState(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState("");

  useEffect(() => {
    let active = true;
    (async () => {
      setLoading(true);
      setError("");
      try {
        const resp = await ownerMgmtApi.dashboard();
        if (active) setData(resp.data);
      } catch (err) {
        if (active) setError(extractApiError(err, "Failed to load dashboard."));
      } finally {
        if (active) setLoading(false);
      }
    })();
    return () => { active = false; };
  }, []);

  if (loading) return <div className="page-status">Loading dashboard...</div>;

  if (error) {
    return (
      <div className="owner-page">
        <div className="alert alert--error">{error}</div>
      </div>
    );
  }

  const dist = data?.rating_distribution ?? {};
  const maxDistCount = Math.max(...Object.values(dist).map(Number), 1);

  return (
    <div className="owner-page">
      <div className="owner-page-header">
        <h1 className="owner-page-title">Owner Dashboard</h1>
        <div className="owner-page-header-actions">
          <Link to="/owner/restaurants" className="btn-owner-nav">My Restaurants</Link>
          <Link to="/owner/profile" className="btn-owner-nav">Owner Profile</Link>
        </div>
      </div>

      {/* Stats row */}
      <div className="owner-stats-row">
        <StatCard label="Claimed Restaurants" value={data.claimed_count} />
        <StatCard label="Total Reviews" value={data.total_reviews} />
        <StatCard
          label="Avg Rating"
          value={data.avg_rating > 0 ? `${data.avg_rating.toFixed(1)} ★` : "—"}
        />
      </div>

      {/* Rating distribution */}
      {data.total_reviews > 0 && (
        <section className="owner-section">
          <h2 className="owner-section-title">Rating Distribution</h2>
          <div className="owner-rating-dist">
            {[5, 4, 3, 2, 1].map((star) => (
              <RatingBar
                key={star}
                star={star}
                count={Number(dist[star] ?? 0)}
                max={maxDistCount}
              />
            ))}
          </div>
        </section>
      )}

      {/* Claimed restaurants */}
      <section className="owner-section">
        <h2 className="owner-section-title">Your Restaurants</h2>
        {data.claimed_restaurants.length === 0 ? (
          <div className="owner-empty">
            <p>No restaurants claimed yet.</p>
            <p className="muted">
              Create a new one or claim an existing restaurant from the{" "}
              <Link to="/">Explore</Link> page.
            </p>
          </div>
        ) : (
          <div className="owner-rc-list">
            {data.claimed_restaurants.map((r) => (
              <OwnerRestaurantCard
                key={r.id}
                restaurant={r}
                onEdit={() => navigate(`/owner/restaurants/${r.id}/edit`)}
                onReviews={() => navigate(`/owner/restaurants/${r.id}/reviews`)}
              />
            ))}
          </div>
        )}
      </section>
    </div>
  );
}
