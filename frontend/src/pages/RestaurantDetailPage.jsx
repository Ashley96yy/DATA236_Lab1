import { useEffect, useRef, useState } from "react";
import { useNavigate, useParams } from "react-router-dom";
import api, { extractApiError } from "../services/api";
import { useAuth } from "../contexts/AuthContext";

const DAY_ORDER = ["Mon", "Tue", "Wed", "Thu", "Fri", "Sat", "Sun"];

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

  // selected photo for lightbox
  const [lightboxUrl, setLightboxUrl] = useState(null);

  useEffect(() => {
    loadRestaurant();
  }, [id]);

  async function loadRestaurant() {
    setLoading(true);
    setError("");
    try {
      const resp = await api.get(`/restaurants/${id}`);
      setRestaurant(resp.data);
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

  // ── Photo helpers ─────────────────────────────────────────────────────────
  const isOwner = isAuthenticated && restaurant &&
    restaurant.created_by_user_id === user?.id;

  const existingPhotoCount = restaurant?.photos?.length ?? 0;
  const canUploadMore = isOwner && existingPhotoCount < 5;

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

    try {
      await api.post(`/restaurants/${restaurant.id}/photos`, formData, {
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
          <button className="btn-back" onClick={() => navigate(-1)}>← Back</button>
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

          {/* ── Reviews placeholder ── */}
          <section className="detail-section">
            <h2 className="section-heading">Reviews</h2>
            <div className="reviews-placeholder">
              <p className="muted">Reviews coming in Phase 4.</p>
              <button
                id="write-review-btn"
                className="btn-primary"
                disabled
                title="Available in Phase 4"
              >
                ✍️ Write a Review
              </button>
            </div>
          </section>
        </div>

        {/* ── Sidebar ── */}
        <aside className="detail-sidebar">
          <div className="detail-info-card">
            <h3 className="detail-info-heading">Details</h3>

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
