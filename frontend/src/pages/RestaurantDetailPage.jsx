import { useCallback, useEffect, useRef, useState } from "react";
import { useNavigate, useParams } from "react-router-dom";

import FavoriteButton from "../components/FavoriteButton";
import { useOwnerAuth } from "../contexts/OwnerAuthContext";
import { useAuth } from "../contexts/AuthContext";
import api, { extractApiError, ownerApi, ownerMgmtApi } from "../services/api";

const DAY_ORDER = ["Mon", "Tue", "Wed", "Thu", "Fri", "Sat", "Sun"];
const wait = (ms) => new Promise((resolve) => setTimeout(resolve, ms));

function StarRating({ rating }) {
  const full = Math.floor(rating);
  const half = rating - full >= 0.5;
  return (
    <span className="star-rating">
      {[1, 2, 3, 4, 5].map((i) => (
        <span key={i} className={i <= full ? "star filled" : (i === full + 1 && half ? "star half" : "star")}>
          ★
        </span>
      ))}
    </span>
  );
}

function InfoRow({ icon, label, value }) {
  if (!value) return null;
  return (
    <div className="detail-info-row">
      <span className="detail-icon">{icon}</span>
      <div>
        <span className="detail-label">{label}</span>
        <span className="detail-value">{value}</span>
      </div>
    </div>
  );
}

export default function RestaurantDetailPage() {
  const { id } = useParams();
  const navigate = useNavigate();
  const { isAuthenticated, user } = useAuth();
  const { isOwnerAuthenticated, owner } = useOwnerAuth();
  const photoInputRef = useRef(null);

  const [restaurant, setRestaurant] = useState(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState("");

  // photo upload
  const [photoFiles, setPhotoFiles] = useState([]);
  const [photoPreviewUrls, setPhotoPreviewUrls] = useState([]);
  const [uploading, setUploading] = useState(false);
  const [photoError, setPhotoError] = useState("");
  const [photoSuccess, setPhotoSuccess] = useState("");

  // lightbox
  const [lightboxUrl, setLightboxUrl] = useState(null);

  // reviews
  const [reviews, setReviews] = useState([]);
  const [reviewsTotal, setReviewsTotal] = useState(0);
  const [reviewsLoading, setReviewsLoading] = useState(false);
  const [reviewRating, setReviewRating] = useState(0);
  const [reviewComment, setReviewComment] = useState("");
  const [reviewSubmitting, setReviewSubmitting] = useState(false);
  const [reviewError, setReviewError] = useState("");
  const [reviewSuccess, setReviewSuccess] = useState("");
  const [editingReview, setEditingReview] = useState(null); // { id, rating, comment }
  const [hoverRating, setHoverRating] = useState(0);
  const [claimSubmitting, setClaimSubmitting] = useState(false);
  const [claimError, setClaimError] = useState("");
  const [claimSuccess, setClaimSuccess] = useState("");

  useEffect(() => {
    loadRestaurant();
  }, [id]);

  const loadReviews = useCallback(async () => {
    setReviewsLoading(true);
    try {
      const resp = await api.get(`/restaurants/${id}/reviews?limit=50`);
      setReviews(resp.data.items || []);
      setReviewsTotal(resp.data.total || 0);
      return resp.data.items || [];
    } catch {
      // non-blocking
      return [];
    } finally {
      setReviewsLoading(false);
    }
  }, [id]);

  useEffect(() => {
    loadReviews();
  }, [loadReviews]);

  async function loadRestaurant() {
    setLoading(true);
    setError("");
    try {
      const resp = await api.get(`/restaurants/${id}`);
      setRestaurant(resp.data);
      return resp.data;
    } catch (err) {
      if (err?.response?.status === 404) {
        setError("Restaurant not found.");
      } else {
        setError(extractApiError(err, "Failed to load restaurant."));
      }
    } finally {
      setLoading(false);
    }
  }

  const syncReviewMutation = useCallback(async (predicate, attempts = 8, delayMs = 400) => {
    for (let attempt = 0; attempt < attempts; attempt += 1) {
      try {
        const [reviewResp, restaurantResp] = await Promise.all([
          api.get(`/restaurants/${id}/reviews?limit=50`),
          api.get(`/restaurants/${id}`),
        ]);
        const nextReviews = reviewResp.data.items || [];
        const nextTotal = reviewResp.data.total || 0;
        const nextRestaurant = restaurantResp.data;

        setReviews(nextReviews);
        setReviewsTotal(nextTotal);
        setRestaurant(nextRestaurant);

        if (predicate(nextReviews, nextRestaurant)) {
          return true;
        }
      } catch {
        // ignore and retry
      }
      await wait(delayMs);
    }
    await loadReviews();
    await loadRestaurant();
    return false;
  }, [id, loadReviews]);

  // ── Photo helpers ─────────────────────────────────────────────────────────
  const isCreatorUser = isAuthenticated && restaurant &&
    restaurant.created_by_user_id === user?.id;
  const isClaimedOwner = isOwnerAuthenticated && restaurant &&
    restaurant.claimed_by_owner_id === owner?.id;

  const existingPhotoCount = restaurant?.photos?.length ?? 0;
  const canUploadMore = (isCreatorUser || isClaimedOwner) && existingPhotoCount < 5;

  function handlePhotoSelect(e) {
    const files = Array.from(e.target.files || []);
    const total = photoFiles.length + files.length;
    const remaining = 5 - existingPhotoCount;
    if (total > remaining) {
      setPhotoError(`You can add at most ${remaining} more photo(s).`);
      return;
    }
    setPhotoError("");
    setPhotoFiles((prev) => [...prev, ...files]);
    const newPreviews = files.map((f) => URL.createObjectURL(f));
    setPhotoPreviewUrls((prev) => [...prev, ...newPreviews]);
    e.target.value = "";
  }

  function removePhoto(index) {
    URL.revokeObjectURL(photoPreviewUrls[index]);
    setPhotoFiles((prev) => prev.filter((_, i) => i !== index));
    setPhotoPreviewUrls((prev) => prev.filter((_, i) => i !== index));
  }

  async function handlePhotoUpload() {
    if (!restaurant || photoFiles.length === 0) return;
    setPhotoError("");
    setPhotoSuccess("");
    setUploading(true);

    const formData = new FormData();
    photoFiles.forEach((f) => formData.append("files", f));
    const uploadClient = isClaimedOwner ? ownerApi : api;

    try {
      await uploadClient.post(`/restaurants/${restaurant.id}/photos`, formData, {
        headers: { "Content-Type": "multipart/form-data" },
      });
      setPhotoSuccess(`${photoFiles.length} photo(s) uploaded!`);
      setPhotoFiles([]);
      setPhotoPreviewUrls([]);
      // Reload to show new photos
      await loadRestaurant();
    } catch (err) {
      setPhotoError(extractApiError(err, "Photo upload failed."));
    } finally {
      setUploading(false);
    }
  }

  async function handleClaimRestaurant() {
    if (!restaurant || claimSubmitting) return;
    setClaimError("");
    setClaimSuccess("");
    setClaimSubmitting(true);
    try {
      await ownerMgmtApi.claimRestaurant(restaurant.id);
      setClaimSuccess("Restaurant claimed successfully.");
      await loadRestaurant();
    } catch (err) {
      setClaimError(extractApiError(err, "Could not claim restaurant."));
    } finally {
      setClaimSubmitting(false);
    }
  }

  // ── Render states ─────────────────────────────────────────────────────────
  if (loading) {
    return (
      <div className="explore-status">
        <div className="spinner" />
        <p>Loading restaurant…</p>
      </div>
    );
  }

  if (error) {
    return (
      <div className="explore-status">
        <div className="alert alert--error">{error}</div>
        <button className="btn-secondary" style={{ marginTop: 16 }} onClick={() => navigate("/")}>
          ← Back to Explore
        </button>
      </div>
    );
  }

  const r = restaurant;
  const heroPhoto = r.photos?.[0]?.photo_url;

  const hoursEntries = r.hours_json
    ? DAY_ORDER.filter((d) => r.hours_json[d]).map((d) => ({ day: d, value: r.hours_json[d] }))
    : [];

  const address = [r.street, r.city, r.state, r.zip_code, r.country]
    .filter(Boolean)
    .join(", ");

  return (
    <div className="detail-page">
      {/* ── Lightbox ── */}
      {lightboxUrl && (
        <div className="lightbox-overlay" onClick={() => setLightboxUrl(null)}>
          <img src={lightboxUrl} alt="Full size" className="lightbox-img" />
          <button className="lightbox-close" onClick={() => setLightboxUrl(null)}>×</button>
        </div>
      )}

      {/* ── Hero ── */}
      <div className="detail-hero" style={heroPhoto ? { backgroundImage: `url(${heroPhoto})` } : {}}>
        <div className="detail-hero-overlay">
          <div className="detail-hero-topbar">
            <button className="btn-back" onClick={() => navigate(-1)}>← Back</button>
            <FavoriteButton restaurantId={r.id} className="detail-fav-btn" />
          </div>
          <div className="detail-hero-content">
            {r.pricing_tier && <span className="detail-pricing-badge">{r.pricing_tier}</span>}
            <h1 className="detail-name">{r.name}</h1>
            {r.cuisine_type && (
              <p className="detail-cuisine">{r.cuisine_type}</p>
            )}
            <div className="detail-rating-row">
              {r.average_rating > 0 ? (
                <>
                  <StarRating rating={r.average_rating} />
                  <span className="detail-review-count">{r.review_count} review{r.review_count !== 1 ? "s" : ""}</span>
                </>
              ) : (
                <span className="detail-no-reviews">No reviews yet</span>
              )}
            </div>
          </div>
        </div>
      </div>

      <div className="detail-body">
        <div className="detail-left">
          {/* ── Description ── */}
          {r.description && (
            <section className="detail-section">
              <h2 className="section-heading">About</h2>
              <p className="detail-description">{r.description}</p>
            </section>
          )}

          {/* ── Photos gallery ── */}
          <section className="detail-section">
            <h2 className="section-heading">Photos</h2>

            {/* Owner upload section */}
            {canUploadMore && (
              <div className="photo-upload-inline">
                {photoError && <div className="alert alert--error">{photoError}</div>}
                {photoSuccess && <div className="alert alert--success">{photoSuccess}</div>}

                <div className="photo-preview-grid">
                  {photoPreviewUrls.map((url, i) => (
                    <div key={i} className="photo-thumb-wrap">
                      <img src={url} alt={`Preview ${i + 1}`} className="photo-thumb" />
                      <button type="button" className="photo-remove-btn" onClick={() => removePhoto(i)}>×</button>
                    </div>
                  ))}
                  {photoFiles.length + existingPhotoCount < 5 && (
                    <button type="button" className="photo-add-btn" onClick={() => photoInputRef.current?.click()}>
                      + Add Photo
                    </button>
                  )}
                </div>

                <input
                  ref={photoInputRef}
                  type="file"
                  accept="image/jpeg,image/png,image/webp"
                  multiple
                  style={{ display: "none" }}
                  onChange={handlePhotoSelect}
                />

                {photoFiles.length > 0 && (
                  <button
                    type="button"
                    className="btn-primary"
                    style={{ marginTop: 12 }}
                    onClick={handlePhotoUpload}
                    disabled={uploading}
                  >
                    {uploading ? "Uploading…" : `Upload ${photoFiles.length} Photo(s)`}
                  </button>
                )}
              </div>
            )}

            {/* Existing photos */}
            {r.photos && r.photos.length > 0 ? (
              <div className="photo-gallery">
                {r.photos.map((p) => (
                  <button
                    key={p.id}
                    className="gallery-thumb-btn"
                    onClick={() => setLightboxUrl(p.photo_url)}
                    aria-label="Enlarge photo"
                  >
                    <img src={p.photo_url} alt="Restaurant" className="gallery-thumb" />
                  </button>
                ))}
              </div>
            ) : !canUploadMore ? (
              <p className="muted">No photos yet.</p>
            ) : null}
          </section>

          {/* ── Hours ── */}
          {hoursEntries.length > 0 && (
            <section className="detail-section">
              <h2 className="section-heading">Hours</h2>
              <table className="hours-table">
                <tbody>
                  {hoursEntries.map(({ day, value }) => (
                    <tr key={day}>
                      <td className="hours-day-cell">{day}</td>
                      <td>{value}</td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </section>
          )}

          {/* ── Reviews ── */}
          <section className="detail-section">
            <h2 className="section-heading">
              Reviews {reviewsTotal > 0 && <span className="reviews-count-badge">({reviewsTotal})</span>}
            </h2>

            {/* Write / Edit review form */}
            {isAuthenticated && (
              <div className="review-form-card">
                <h3 className="review-form-title">
                  {editingReview ? "Edit Your Review" : "Write a Review"}
                </h3>

                {reviewError && <div className="alert alert--error">{reviewError}</div>}
                {reviewSuccess && <div className="alert alert--success">{reviewSuccess}</div>}

                {/* Star selector */}
                <div className="star-selector">
                  {[1, 2, 3, 4, 5].map((s) => {
                    const active = editingReview
                      ? s <= (hoverRating || editingReview.rating)
                      : s <= (hoverRating || reviewRating);
                    return (
                      <button
                        key={s}
                        type="button"
                        className={`star-btn${active ? " active" : ""}`}
                        onMouseEnter={() => setHoverRating(s)}
                        onMouseLeave={() => setHoverRating(0)}
                        onClick={() => {
                          if (editingReview) setEditingReview({ ...editingReview, rating: s });
                          else setReviewRating(s);
                        }}
                        aria-label={`${s} star${s > 1 ? "s" : ""}`}
                      >
                        ★
                      </button>
                    );
                  })}
                  <span className="star-label">
                    {(editingReview ? editingReview.rating : reviewRating) > 0
                      ? `${editingReview ? editingReview.rating : reviewRating} / 5`
                      : "Select rating"}
                  </span>
                </div>

                <textarea
                  className="review-textarea"
                  placeholder="Share your experience (optional)"
                  value={editingReview ? editingReview.comment : reviewComment}
                  onChange={(e) => {
                    if (editingReview) setEditingReview({ ...editingReview, comment: e.target.value });
                    else setReviewComment(e.target.value);
                  }}
                  rows={3}
                />

                <div className="review-form-actions">
                  <button
                    type="button"
                    className="btn-primary"
                    disabled={reviewSubmitting || (editingReview ? editingReview.rating < 1 : reviewRating < 1)}
                    onClick={async () => {
                      setReviewError("");
                      setReviewSuccess("");
                      setReviewSubmitting(true);
                      try {
                        if (editingReview) {
                          const expectedReviewId = editingReview.id;
                          const expectedRating = editingReview.rating;
                          const expectedComment = editingReview.comment || null;
                          await api.put(`/reviews/${editingReview.id}`, {
                            rating: editingReview.rating,
                            comment: editingReview.comment || null,
                          });
                          setReviewSuccess("Review update queued. Syncing...");
                          setEditingReview(null);
                          await syncReviewMutation(
                            (items) => items.some(
                              (item) =>
                                item.id === expectedReviewId &&
                                item.rating === expectedRating &&
                                (item.comment || null) === expectedComment,
                            ),
                          );
                          setReviewSuccess("Review updated!");
                        } else {
                          const expectedRating = reviewRating;
                          const expectedComment = reviewComment || null;
                          const expectedUserId = user?.id;
                          await api.post(`/restaurants/${id}/reviews`, {
                            rating: reviewRating,
                            comment: reviewComment || null,
                          });
                          setReviewSuccess("Review submitted and syncing...");
                          setReviewRating(0);
                          setReviewComment("");
                          await syncReviewMutation(
                            (items) => items.some(
                              (item) =>
                                item.user_id === expectedUserId &&
                                item.rating === expectedRating &&
                                (item.comment || null) === expectedComment,
                            ),
                          );
                          setReviewSuccess("Review submitted!");
                        }
                      } catch (err) {
                        setReviewError(extractApiError(err, "Could not submit review."));
                      } finally {
                        setReviewSubmitting(false);
                      }
                    }}
                  >
                    {reviewSubmitting ? "Saving…" : editingReview ? "Save Changes" : "Submit Review"}
                  </button>

                  {editingReview && (
                    <button
                      type="button"
                      className="btn-secondary"
                      onClick={() => { setEditingReview(null); setReviewError(""); }}
                    >
                      Cancel
                    </button>
                  )}
                </div>
              </div>
            )}

            {/* Review list */}
            {reviewsLoading ? (
              <div className="spinner" style={{ margin: "16px auto" }} />
            ) : reviews.length === 0 ? (
              <p className="muted" style={{ marginTop: 12 }}>
                No reviews yet.{isAuthenticated ? " Be the first!" : " Log in to write one."}
              </p>
            ) : (
              <div className="review-list">
                {reviews.map((rv) => (
                  <div key={rv.id} className="review-card">
                    <div className="review-header">
                      <div className="review-meta">
                        <span className="review-author">{rv.user_name}</span>
                        <span className="review-date">
                          {new Date(rv.created_at).toLocaleDateString()}
                        </span>
                      </div>
                      <div className="review-stars">
                        {[1,2,3,4,5].map((s) => (
                          <span key={s} className={s <= rv.rating ? "star filled" : "star"}>★</span>
                        ))}
                      </div>
                    </div>

                    {rv.comment && <p className="review-comment">{rv.comment}</p>}

                    {/* Edit / Delete — only for own reviews */}
                    {isAuthenticated && user?.id === rv.user_id && (
                      <div className="review-actions">
                        <button
                          type="button"
                          className="btn-text"
                          onClick={() => {
                            setEditingReview({ id: rv.id, rating: rv.rating, comment: rv.comment || "" });
                            setReviewError("");
                            setReviewSuccess("");
                            window.scrollTo({ top: 0, behavior: "smooth" });
                          }}
                        >
                          Edit
                        </button>
                        <button
                          type="button"
                          className="btn-text btn-text--danger"
                          onClick={async () => {
                            if (!window.confirm("Delete this review?")) return;
                            try {
                              await api.delete(`/reviews/${rv.id}`);
                              setReviewSuccess("Review delete queued. Syncing...");
                              await syncReviewMutation((items) => !items.some((item) => item.id === rv.id));
                              setReviewSuccess("Review deleted!");
                            } catch (err) {
                              setReviewError(extractApiError(err, "Could not delete review."));
                            }
                          }}
                        >
                          Delete
                        </button>
                      </div>
                    )}
                  </div>
                ))}
              </div>
            )}
          </section>
        </div>

        {/* ── Sidebar ── */}
        <aside className="detail-sidebar">
          <div className="detail-info-card">
            <h3 className="detail-info-heading">Details</h3>

            {isOwnerAuthenticated && (
              <div className="owner-claim-panel">
                {claimError && <div className="alert alert--error">{claimError}</div>}
                {claimSuccess && <div className="alert alert--success">{claimSuccess}</div>}

                {!r.claimed_by_owner_id && (
                  <>
                    <p className="muted">Own this restaurant? Claim it to manage details and photos.</p>
                    <button
                      type="button"
                      className="btn-primary owner-claim-btn"
                      onClick={handleClaimRestaurant}
                      disabled={claimSubmitting}
                    >
                      {claimSubmitting ? "Claiming..." : "Claim This Restaurant"}
                    </button>
                  </>
                )}

                {r.claimed_by_owner_id && isClaimedOwner && (
                  <div className="owner-claim-status owner-claim-status--success">
                    You have already claimed this restaurant.
                  </div>
                )}

                {r.claimed_by_owner_id && !isClaimedOwner && (
                  <div className="owner-claim-status">
                    This restaurant has already been claimed by another owner.
                  </div>
                )}
              </div>
            )}

            <InfoRow icon="📍" label="Address" value={address} />
            <InfoRow icon="📞" label="Phone" value={r.phone} />
            <InfoRow icon="✉️" label="Email" value={r.email} />
            {r.pricing_tier && (
              <InfoRow icon="💰" label="Price" value={r.pricing_tier} />
            )}
            {r.cuisine_type && (
              <InfoRow icon="🍴" label="Cuisine" value={r.cuisine_type} />
            )}

            {/* Amenities */}
            {Array.isArray(r.amenities) && r.amenities.length > 0 && (
              <div className="detail-amenities">
                <p className="detail-label" style={{ marginBottom: 8 }}>Amenities</p>
                <div className="amenities-tags">
                  {r.amenities.map((a) => (
                    <span key={a} className="rc-amenity-tag">{a}</span>
                  ))}
                </div>
              </div>
            )}
          </div>
        </aside>
      </div>
    </div>
  );
}
