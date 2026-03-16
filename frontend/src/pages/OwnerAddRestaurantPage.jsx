import { useRef, useState } from "react";
import { useNavigate } from "react-router-dom";

import { extractApiError, ownerApi, ownerMgmtApi } from "../services/api";

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

export default function OwnerAddRestaurantPage() {
  const navigate = useNavigate();
  const photoInputRef = useRef(null);
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
    Object.fromEntries(DAY_KEYS.map((day) => [day, ""]))
  );
  const [selectedAmenities, setSelectedAmenities] = useState([]);
  const [customAmenity, setCustomAmenity] = useState("");
  const [submitting, setSubmitting] = useState(false);
  const [formError, setFormError] = useState("");
  const [createdRestaurant, setCreatedRestaurant] = useState(null);
  const [photoFiles, setPhotoFiles] = useState([]);
  const [photoPreviewUrls, setPhotoPreviewUrls] = useState([]);
  const [uploading, setUploading] = useState(false);
  const [photoError, setPhotoError] = useState("");
  const [photoSuccess, setPhotoSuccess] = useState("");

  function set(field, value) {
    setForm((prev) => ({ ...prev, [field]: value }));
  }

  function toggleAmenity(label) {
    setSelectedAmenities((prev) =>
      prev.includes(label) ? prev.filter((item) => item !== label) : [...prev, label]
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
    const payload = {};
    for (const [day, value] of Object.entries(hoursForm)) {
      if (value.trim()) payload[day] = value.trim();
    }
    return Object.keys(payload).length ? payload : null;
  }

  async function handleSubmit(event) {
    event.preventDefault();
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
      const response = await ownerMgmtApi.createRestaurant(body);
      setCreatedRestaurant(response.data);
    } catch (err) {
      setFormError(extractApiError(err, "Failed to create restaurant."));
    } finally {
      setSubmitting(false);
    }
  }

  function handlePhotoSelect(event) {
    const files = Array.from(event.target.files || []);
    const total = photoFiles.length + files.length;
    if (total > 5) {
      setPhotoError("Maximum 5 photos allowed.");
      return;
    }
    setPhotoError("");
    setPhotoFiles((prev) => [...prev, ...files]);
    const newPreviews = files.map((file) => URL.createObjectURL(file));
    setPhotoPreviewUrls((prev) => [...prev, ...newPreviews]);
    event.target.value = "";
  }

  function removePhoto(index) {
    URL.revokeObjectURL(photoPreviewUrls[index]);
    setPhotoFiles((prev) => prev.filter((_, i) => i !== index));
    setPhotoPreviewUrls((prev) => prev.filter((_, i) => i !== index));
  }

  async function handlePhotoUpload() {
    if (!createdRestaurant || photoFiles.length === 0) return;
    setPhotoError("");
    setPhotoSuccess("");
    setUploading(true);

    const formData = new FormData();
    photoFiles.forEach((file) => formData.append("files", file));

    try {
      await ownerApi.post(`/restaurants/${createdRestaurant.id}/photos`, formData, {
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

  if (createdRestaurant) {
    return (
      <div className="add-restaurant-page">
        <div className="page-card">
          <div className="create-success-header">
            <span className="create-success-icon">🏪</span>
            <div>
              <h1 className="auth-title">"{createdRestaurant.name}" is now claimed by you</h1>
              <p className="muted">Upload photos now or continue to the restaurant page.</p>
            </div>
          </div>

          <section className="photo-upload-section">
            <h2 className="section-heading">Upload Photos (up to 5)</h2>

            {photoError && <div className="alert alert--error">{photoError}</div>}
            {photoSuccess && <div className="alert alert--success">{photoSuccess}</div>}

            <div className="photo-preview-grid">
              {photoPreviewUrls.map((url, index) => (
                <div key={index} className="photo-thumb-wrap">
                  <img src={url} alt={`Preview ${index + 1}`} className="photo-thumb" />
                  <button
                    type="button"
                    className="photo-remove-btn"
                    onClick={() => removePhoto(index)}
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
                  {uploading ? "Uploading..." : `Upload ${photoFiles.length} Photo(s)`}
                </button>
              )}
              <button
                type="button"
                className="btn-secondary"
                onClick={() => navigate(`/restaurant/${createdRestaurant.id}`)}
              >
                {photoFiles.length === 0 ? "View Restaurant Page →" : "Skip & View Page →"}
              </button>
            </div>
          </section>
        </div>
      </div>
    );
  }

  return (
    <div className="add-restaurant-page">
      <div className="page-card">
        <h1 className="auth-title">Create Owner Restaurant Listing</h1>
        <p className="muted">Post a restaurant directly under your owner account.</p>

        {formError && <div className="alert alert--error">{formError}</div>}

        <form className="add-restaurant-form" onSubmit={handleSubmit} noValidate>
          <fieldset className="form-fieldset">
            <legend className="form-legend">Basic Info</legend>
            <div className="form-grid two-col">
              <label className="full-row">
                <span className="field-label">Restaurant Name <span className="required">*</span></span>
                <input
                  type="text"
                  value={form.name}
                  onChange={(event) => set("name", event.target.value)}
                  placeholder="e.g. Mario's Pizzeria"
                  required
                />
              </label>

              <label>
                <span className="field-label">Cuisine Type</span>
                <input
                  type="text"
                  value={form.cuisine_type}
                  onChange={(event) => set("cuisine_type", event.target.value)}
                  placeholder="Italian, Thai, Mexican..."
                />
              </label>

              <label>
                <span className="field-label">Pricing Tier</span>
                <select
                  value={form.pricing_tier}
                  onChange={(event) => set("pricing_tier", event.target.value)}
                >
                  <option value="">Select pricing</option>
                  {PRICING_TIERS.map((tier) => (
                    <option key={tier} value={tier}>{tier}</option>
                  ))}
                </select>
              </label>

              <label className="full-row">
                <span className="field-label">Description</span>
                <textarea
                  rows={4}
                  value={form.description}
                  onChange={(event) => set("description", event.target.value)}
                  placeholder="Tell people what makes this place special..."
                />
              </label>
            </div>
          </fieldset>

          <fieldset className="form-fieldset">
            <legend className="form-legend">Location & Contact</legend>
            <div className="form-grid two-col">
              <label className="full-row">
                <span className="field-label">Street Address</span>
                <input value={form.street} onChange={(event) => set("street", event.target.value)} />
              </label>
              <label>
                <span className="field-label">City <span className="required">*</span></span>
                <input value={form.city} onChange={(event) => set("city", event.target.value)} required />
              </label>
              <label>
                <span className="field-label">State</span>
                <input value={form.state} onChange={(event) => set("state", event.target.value)} />
              </label>
              <label>
                <span className="field-label">ZIP Code</span>
                <input value={form.zip_code} onChange={(event) => set("zip_code", event.target.value)} />
              </label>
              <label>
                <span className="field-label">Country</span>
                <input value={form.country} onChange={(event) => set("country", event.target.value)} />
              </label>
              <label>
                <span className="field-label">Phone</span>
                <input value={form.phone} onChange={(event) => set("phone", event.target.value)} />
              </label>
              <label>
                <span className="field-label">Email</span>
                <input type="email" value={form.email} onChange={(event) => set("email", event.target.value)} />
              </label>
              <label>
                <span className="field-label">Latitude</span>
                <input type="number" step="any" value={form.latitude} onChange={(event) => set("latitude", event.target.value)} />
              </label>
              <label>
                <span className="field-label">Longitude</span>
                <input type="number" step="any" value={form.longitude} onChange={(event) => set("longitude", event.target.value)} />
              </label>
            </div>
          </fieldset>

          <fieldset className="form-fieldset">
            <legend className="form-legend">Hours</legend>
            <div className="hours-grid">
              {DAY_KEYS.map((day) => (
                <label key={day} className="hours-row">
                  <span className="hours-day">{day}</span>
                  <input
                    type="text"
                    value={hoursForm[day]}
                    onChange={(event) =>
                      setHoursForm((prev) => ({ ...prev, [day]: event.target.value }))
                    }
                    placeholder="e.g. 11:00 AM - 9:00 PM"
                  />
                </label>
              ))}
            </div>
          </fieldset>

          <fieldset className="form-fieldset">
            <legend className="form-legend">Amenities</legend>
            <div className="amenities-grid">
              {DEFAULT_AMENITIES.map((label) => (
                <AmenityCheckbox
                  key={label}
                  label={label}
                  checked={selectedAmenities.includes(label)}
                  onChange={() => toggleAmenity(label)}
                />
              ))}
            </div>

            <div className="custom-amenity-row">
              <input
                type="text"
                value={customAmenity}
                onChange={(event) => setCustomAmenity(event.target.value)}
                placeholder="Add custom amenity"
              />
              <button type="button" className="btn-secondary" onClick={addCustomAmenity}>
                Add
              </button>
            </div>

            {selectedAmenities.length > 0 && (
              <div className="selected-amenities">
                {selectedAmenities.map((label) => (
                  <span key={label} className="rc-amenity-tag">{label}</span>
                ))}
              </div>
            )}
          </fieldset>

          <div className="form-actions">
            <button type="submit" className="btn-primary" disabled={submitting}>
              {submitting ? "Creating..." : "Create Restaurant"}
            </button>
            <button
              type="button"
              className="btn-secondary"
              onClick={() => navigate("/owner/restaurants")}
              disabled={submitting}
            >
              Cancel
            </button>
          </div>
        </form>
      </div>
    </div>
  );
}
