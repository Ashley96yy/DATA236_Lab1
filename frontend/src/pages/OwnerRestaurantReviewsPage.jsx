import { useEffect, useState } from "react";
import { useNavigate, useParams } from "react-router-dom";

import { extractApiError, ownerMgmtApi } from "../services/api";

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

export default function OwnerRestaurantReviewsPage() {
  const { id } = useParams();
  const navigate = useNavigate();
  const [data, setData] = useState(null);
  const [page, setPage] = useState(1);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState("");

  useEffect(() => {
    let active = true;
    (async () => {
      setLoading(true);
      setError("");
      try {
        const resp = await ownerMgmtApi.getRestaurantReviews(id, page, LIMIT);
        if (active) setData(resp.data);
      } catch (err) {
        if (!active) return;
        if (err?.response?.status === 403) {
          setError("You don't own this restaurant.");
        } else {
          setError(extractApiError(err, "Failed to load reviews."));
        }
      } finally {
        if (active) setLoading(false);
      }
    })();
    return () => { active = false; };
  }, [id, page]);

  const totalPages = data ? Math.ceil(data.total / LIMIT) : 1;

  return (
    <div className="owner-page">
      <div className="owner-page-header">
        <h1 className="owner-page-title">Restaurant Reviews</h1>
        <button
          type="button"
          className="btn-owner-nav"
          onClick={() => navigate(-1)}
        >
          ← Back
        </button>
      </div>

      {loading && (
        <div className="explore-status">
          <div className="spinner" />
        </div>
      )}

      {error && <div className="alert alert--error">{error}</div>}

      {!loading && data && (
        <>
          <p className="owner-reviews-count">
            {data.total} review{data.total !== 1 ? "s" : ""} total
          </p>

          {data.items.length === 0 ? (
            <div className="owner-empty">
              <p>No reviews yet for this restaurant.</p>
            </div>
          ) : (
            <div className="owner-review-list">
              {data.items.map((rv) => (
                <div key={rv.id} className="owner-review-card">
                  <div className="owner-review-top">
                    <span className="owner-review-user">{rv.user_name}</span>
                    <StarDisplay rating={rv.rating} />
                    <span className="owner-review-date">
                      {new Date(rv.created_at).toLocaleDateString()}
                    </span>
                  </div>
                  {rv.comment && (
                    <p className="owner-review-comment">{rv.comment}</p>
                  )}
                </div>
              ))}
            </div>
          )}

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
