import { useRef, useState } from "react";
import { useNavigate } from "react-router-dom";
import api, { extractApiError } from "../services/api";

const PRICING_TIERS = ["$", "$$", "$$$", "$$$$"];
const DEFAULT_AMENITIES = [
  "WiFi", "Parking", "Outdoor Seating", "Takeout", "Delivery",
  "Reservations", "Live Music", "Dog Friendly", "Vegan Options", "Wheelchair Accessible",
];

const DAY_KEYS = ["Mon", "Tue", "Wed", "Thu", "Fri", "Sat", "Sun"];

function AmenityCheckbox({ label, checked, onChange }) {
  return (
    <label className="amenity-check">
      <input type="checkbox" checked={checked} onChange={onChange} />
      {label}
    </label>
  );
}

export default function AddRestaurantPage() {
  const navigate = useNavigate();
  const photoInputRef = useRef(null);

  // ── Form state ────────────────────────────────────────────────────────────
  const [form, setForm] = useState({
    name: "",
    cuisine_type: "",
    description: "",
    street: "",
    city: "",
    state: "",
    zip_code: "",
    country: "",
    latitude: "",
    longitude: "",
    phone: "",
    email: "",
    pricing_tier: "",
  });

  const [hoursForm, setHoursForm] = useState(
    Object.fromEntries(DAY_KEYS.map((d) => [d, ""]))
  );
  const [selectedAmenities, setSelectedAmenities] = useState([]);
  const [customAmenity, setCustomAmenity] = useState("");

  // ── Submission states ─────────────────────────────────────────────────────
  const [submitting, setSubmitting] = useState(false);
  const [formError, setFormError] = useState("");
  const [createdRestaurant, setCreatedRestaurant] = useState(null); // set after create success

  // ── Photo upload states ───────────────────────────────────────────────────
  const [photoFiles, setPhotoFiles] = useState([]);
  const [photoPreviewUrls, setPhotoPreviewUrls] = useState([]);
  const [uploading, setUploading] = useState(false);
  const [photoError, setPhotoError] = useState("");
  const [photoSuccess, setPhotoSuccess] = useState("");

  // ── Helpers ───────────────────────────────────────────────────────────────
  function set(field, value) {
    setForm((prev) => ({ ...prev, [field]: value }));
  }

  function toggleAmenity(label) {
    setSelectedAmenities((prev) =>
      prev.includes(label) ? prev.filter((a) => a !== label) : [...prev, label]
    );
  }

  function addCustomAmenity() {
    const trimmed = customAmenity.trim();
    if (trimmed && !selectedAmenities.includes(trimmed)) {
      setSelectedAmenities((prev) => [...prev, trimmed]);
    }
    setCustomAmenity("");
  }

  function buildHoursJson() {
    const obj = {};
    for (const [day, val] of Object.entries(hoursForm)) {
      if (val.trim()) obj[day] = val.trim();
    }
    return Object.keys(obj).length ? obj : null;
  }

  // ── Create restaurant ─────────────────────────────────────────────────────
  async function handleSubmit(e) {
    e.preventDefault();
    setFormError("");

    if (!form.name.trim()) {
      setFormError("Restaurant name is required.");
      return;
    }
    if (!form.city.trim()) {
      setFormError("City is required.");
      return;
    }

    const body = {
      name: form.name.trim(),
      cuisine_type: form.cuisine_type.trim() || null,
      description: form.description.trim() || null,
      street: form.street.trim() || null,
      city: form.city.trim(),
      state: form.state.trim() || null,
      zip_code: form.zip_code.trim() || null,
      country: form.country.trim() || null,
      latitude: form.latitude ? parseFloat(form.latitude) : null,
      longitude: form.longitude ? parseFloat(form.longitude) : null,
      phone: form.phone.trim() || null,
      email: form.email.trim() || null,
      hours_json: buildHoursJson(),
      pricing_tier: form.pricing_tier || null,
      amenities: selectedAmenities.length ? selectedAmenities : null,
    };

    setSubmitting(true);
    try {
      const resp = await api.post("/restaurants", body);
      setCreatedRestaurant(resp.data);
    } catch (err) {
      setFormError(extractApiError(err, "Failed to create restaurant."));
    } finally {
      setSubmitting(false);
    }
  }

  // ── Photo file selection ──────────────────────────────────────────────────
  function handlePhotoSelect(e) {
    const files = Array.from(e.target.files || []);
    const total = photoFiles.length + files.length;
    if (total > 5) {
      setPhotoError("Maximum 5 photos allowed.");
      return;
    }
    setPhotoError("");
    setPhotoFiles((prev) => [...prev, ...files]);
    const newPreviews = files.map((f) => URL.createObjectURL(f));
    setPhotoPreviewUrls((prev) => [...prev, ...newPreviews]);
    // reset input so same file can be re-selected after removal
    e.target.value = "";
  }

  function removePhoto(index) {
    URL.revokeObjectURL(photoPreviewUrls[index]);
    setPhotoFiles((prev) => prev.filter((_, i) => i !== index));
    setPhotoPreviewUrls((prev) => prev.filter((_, i) => i !== index));
  }

  // ── Upload photos ─────────────────────────────────────────────────────────
  async function handlePhotoUpload() {
    if (!createdRestaurant || photoFiles.length === 0) return;
    setPhotoError("");
    setPhotoSuccess("");
    setUploading(true);

    const formData = new FormData();
    photoFiles.forEach((f) => formData.append("files", f));

    try {
      await api.post(`/restaurants/${createdRestaurant.id}/photos`, formData, {
        headers: { "Content-Type": "multipart/form-data" },
      });
      setPhotoSuccess(`${photoFiles.length} photo(s) uploaded successfully!`);
      setPhotoFiles([]);
      setPhotoPreviewUrls([]);
    } catch (err) {
      setPhotoError(extractApiError(err, "Photo upload failed."));
    } finally {
      setUploading(false);
    }
  }

  function goToDetail() {
    navigate(`/restaurant/${createdRestaurant.id}`);
  }

  // ── Post-create view ──────────────────────────────────────────────────────
  if (createdRestaurant) {
    return (
      <div className="add-restaurant-page">
        <div className="page-card">
          <div className="create-success-header">
            <span className="create-success-icon">🎉</span>
            <div>
              <h1 className="auth-title">"{createdRestaurant.name}" is live!</h1>
              <p className="muted">Would you like to add some photos now?</p>
            </div>
          </div>

          {/* Photo upload section */}
          <section className="photo-upload-section">
            <h2 className="section-heading">Upload Photos (up to 5)</h2>

            {photoError && <div className="alert alert--error">{photoError}</div>}
            {photoSuccess && <div className="alert alert--success">{photoSuccess}</div>}

            <div className="photo-preview-grid">
              {photoPreviewUrls.map((url, i) => (
                <div key={i} className="photo-thumb-wrap">
                  <img src={url} alt={`Preview ${i + 1}`} className="photo-thumb" />
                  <button
                    type="button"
                    className="photo-remove-btn"
                    onClick={() => removePhoto(i)}
                    aria-label="Remove photo"
                  >
                    ×
                  </button>
                </div>
              ))}
              {photoFiles.length < 5 && (
                <button
                  type="button"
                  className="photo-add-btn"
                  onClick={() => photoInputRef.current?.click()}
                >
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

            <div className="create-actions">
              {photoFiles.length > 0 && (
                <button
                  type="button"
                  className="btn-primary"
                  onClick={handlePhotoUpload}
                  disabled={uploading}
                >
                  {uploading ? "Uploading…" : `Upload ${photoFiles.length} Photo(s)`}
                </button>
              )}
              <button type="button" className="btn-secondary" onClick={goToDetail}>
                {photoFiles.length === 0 ? "View Restaurant Page →" : "Skip & View Page →"}
              </button>
            </div>
          </section>
        </div>
      </div>
    );
  }

  // ── Create form ───────────────────────────────────────────────────────────
  return (
    <div className="add-restaurant-page">
      <div className="page-card">
        <h1 className="auth-title">Add a Restaurant</h1>
        <p className="muted">Help the community discover great places to eat.</p>

        {formError && <div className="alert alert--error">{formError}</div>}

        <form className="add-restaurant-form" onSubmit={handleSubmit} noValidate>
          {/* ── Identity ── */}
          <fieldset className="form-fieldset">
            <legend className="form-legend">Basic Info</legend>
            <div className="form-grid two-col">
              <label className="full-row">
                <span className="field-label">Restaurant Name <span className="required">*</span></span>
                <input
                  id="ar-name"
                  type="text"
                  value={form.name}
                  onChange={(e) => set("name", e.target.value)}
                  placeholder="e.g. Mario's Pizzeria"
                  required
                />
              </label>
              <label>
                <span className="field-label">Cuisine Type</span>
                <input
                  id="ar-cuisine"
                  type="text"
                  value={form.cuisine_type}
                  onChange={(e) => set("cuisine_type", e.target.value)}
                  placeholder="Italian, Thai, Mexican…"
                />
              </label>
              <label>
                <span className="field-label">Pricing Tier</span>
                <select
                  id="ar-pricing"
                  value={form.pricing_tier}
                  onChange={(e) => set("pricing_tier", e.target.value)}
                >
                  <option value="">— Select —</option>
                  {PRICING_TIERS.map((t) => (
                    <option key={t} value={t}>{t}</option>
                  ))}
                </select>
              </label>
              <label className="full-row">
                <span className="field-label">Description</span>
                <textarea
                  id="ar-description"
                  value={form.description}
                  onChange={(e) => set("description", e.target.value)}
                  rows={3}
                  placeholder="A short description of the restaurant…"
                />
              </label>
            </div>
          </fieldset>

          {/* ── Address ── */}
          <fieldset className="form-fieldset">
            <legend className="form-legend">Address</legend>
            <div className="form-grid two-col">
              <label className="full-row">
                <span className="field-label">Street</span>
                <input
                  id="ar-street"
                  type="text"
                  value={form.street}
                  onChange={(e) => set("street", e.target.value)}
                  placeholder="123 Main St"
                />
              </label>
              <label>
                <span className="field-label">City <span className="required">*</span></span>
                <input
                  id="ar-city"
                  type="text"
                  value={form.city}
                  onChange={(e) => set("city", e.target.value)}
                  placeholder="San Francisco"
                  required
                />
              </label>
              <label>
                <span className="field-label">State</span>
                <input
                  id="ar-state"
                  type="text"
                  value={form.state}
                  onChange={(e) => set("state", e.target.value)}
                  placeholder="CA"
                />
              </label>
              <label>
                <span className="field-label">Zip Code</span>
                <input
                  id="ar-zip"
                  type="text"
                  value={form.zip_code}
                  onChange={(e) => set("zip_code", e.target.value)}
                  placeholder="94102"
                />
              </label>
              <label>
                <span className="field-label">Country</span>
                <input
                  id="ar-country"
                  type="text"
                  value={form.country}
                  onChange={(e) => set("country", e.target.value)}
                  placeholder="USA"
                />
              </label>
            </div>
          </fieldset>

          {/* ── Contact ── */}
          <fieldset className="form-fieldset">
            <legend className="form-legend">Contact</legend>
            <div className="form-grid two-col">
              <label>
                <span className="field-label">Phone</span>
                <input
                  id="ar-phone"
                  type="tel"
                  value={form.phone}
                  onChange={(e) => set("phone", e.target.value)}
                  placeholder="+1 415 555 0100"
                />
              </label>
              <label>
                <span className="field-label">Email</span>
                <input
                  id="ar-email"
                  type="email"
                  value={form.email}
                  onChange={(e) => set("email", e.target.value)}
                  placeholder="hello@restaurant.com"
                />
              </label>
            </div>
          </fieldset>

          {/* ── Hours ── */}
          <fieldset className="form-fieldset">
            <legend className="form-legend">Hours</legend>
            <div className="hours-grid">
              {DAY_KEYS.map((day) => (
                <label key={day} className="hours-row">
                  <span className="hours-day">{day}</span>
                  <input
                    id={`ar-hours-${day}`}
                    type="text"
                    value={hoursForm[day]}
                    onChange={(e) =>
                      setHoursForm((prev) => ({ ...prev, [day]: e.target.value }))
                    }
                    placeholder="9am – 10pm or Closed"
                  />
                </label>
              ))}
            </div>
          </fieldset>

          {/* ── Amenities ── */}
          <fieldset className="form-fieldset">
            <legend className="form-legend">Amenities</legend>
            <div className="amenities-grid">
              {DEFAULT_AMENITIES.map((a) => (
                <AmenityCheckbox
                  key={a}
                  label={a}
                  checked={selectedAmenities.includes(a)}
                  onChange={() => toggleAmenity(a)}
                />
              ))}
            </div>
            <div className="custom-amenity-row">
              <input
                id="ar-custom-amenity"
                type="text"
                value={customAmenity}
                onChange={(e) => setCustomAmenity(e.target.value)}
                onKeyDown={(e) => e.key === "Enter" && (e.preventDefault(), addCustomAmenity())}
                placeholder="Add custom amenity…"
              />
              <button type="button" className="btn-secondary btn-sm" onClick={addCustomAmenity}>
                Add
              </button>
            </div>
            {selectedAmenities.length > 0 && (
              <div className="selected-amenities">
                {selectedAmenities.map((a) => (
                  <span key={a} className="amenity-tag-selected">
                    {a}
                    <button
                      type="button"
                      className="amenity-tag-remove"
                      onClick={() => toggleAmenity(a)}
                      aria-label={`Remove ${a}`}
                    >
                      ×
                    </button>
                  </span>
                ))}
              </div>
            )}
          </fieldset>

          <button
            id="ar-submit"
            type="submit"
            className="btn-primary btn-full"
            disabled={submitting}
          >
            {submitting ? "Creating…" : "Create Restaurant"}
          </button>
        </form>
      </div>
    </div>
  );
}
