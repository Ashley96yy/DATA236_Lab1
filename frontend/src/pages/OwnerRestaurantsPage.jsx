import { useEffect, useState } from "react";
import { useNavigate } from "react-router-dom";

import { extractApiError, ownerMgmtApi } from "../services/api";
import { OwnerRestaurantCard } from "./OwnerDashboardPage";

export default function OwnerRestaurantsPage() {
  const navigate = useNavigate();
  const [restaurants, setRestaurants] = useState(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState("");

  useEffect(() => {
    let active = true;
    (async () => {
      setLoading(true);
      setError("");
      try {
        const resp = await ownerMgmtApi.dashboard();
        if (active) setRestaurants(resp.data.claimed_restaurants);
      } catch (err) {
        if (active) setError(extractApiError(err, "Failed to load restaurants."));
      } finally {
        if (active) setLoading(false);
      }
    })();
    return () => { active = false; };
  }, []);

  if (loading) return <div className="page-status">Loading restaurants...</div>;

  return (
    <div className="owner-page">
      <div className="owner-page-header">
        <h1 className="owner-page-title">My Restaurants</h1>
        <button
          type="button"
          className="btn-owner-nav"
          onClick={() => navigate("/owner/dashboard")}
        >
          ← Dashboard
        </button>
      </div>

      {error && <div className="alert alert--error">{error}</div>}

      {!error && restaurants !== null && restaurants.length === 0 && (
        <div className="owner-empty">
          <p>No claimed restaurants yet.</p>
          <p className="muted">
            You can claim an existing restaurant from its detail page.
          </p>
        </div>
      )}

      {restaurants && restaurants.length > 0 && (
        <div className="owner-rc-list">
          {restaurants.map((r) => (
            <OwnerRestaurantCard
              key={r.id}
              restaurant={r}
              onEdit={() => navigate(`/owner/restaurants/${r.id}/edit`)}
              onReviews={() => navigate(`/owner/restaurants/${r.id}/reviews`)}
            />
          ))}
        </div>
      )}
    </div>
  );
}
