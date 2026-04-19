import { useRef, useState } from "react";
import { useNavigate } from "react-router-dom";

import { extractApiError, ownerApi, ownerMgmtApi } from "../services/api";
import { CUISINE_OPTIONS } from "../constants/cuisine";

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
      const newRestaurant = response.data;

      // Automatically upload photos if any were selected
      if (photoFiles.length > 0) {
        setUploading(true);
        const formData = new FormData();
        photoFiles.forEach((f) => formData.append("files", f));
        try {
          await ownerApi.post(`/restaurants/${newRestaurant.id}/photos`, formData, {
            headers: { "Content-Type": "multipart/form-data" },
          });
        } catch (err) {
          console.error("Auto-upload failed:", err);
          // We don't block the redirect, but maybe we should show an alert?
          // For now, let's just proceed as the restaurant was created.
        }
      }

      navigate(`/restaurant/${newRestaurant.id}`);
    } catch (err) {
      setFormError(extractApiError(err, "Failed to create restaurant."));
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

  return (
    <div className="owner-page">
      <div className="owner-page-header">
        <h1 className="owner-page-title">Post a Restaurant</h1>
      </div>

      <div className="page-card">
        {formError && <div className="alert alert--error">{formError}</div>}
        {photoError && <div className="alert alert--error">{photoError}</div>}

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
                <select
                  value={form.cuisine_type}
                  onChange={(event) => set("cuisine_type", event.target.value)}
                >
                  <option value="">Select cuisine</option>
                  {CUISINE_OPTIONS.map((cuisine) => (
                    <option key={cuisine} value={cuisine}>{cuisine}</option>
                  ))}
                </select>
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

          {/* ── Photos ── */}
          <fieldset className="form-fieldset">
            <legend className="form-legend">Restaurant Photos</legend>
            <p className="muted" style={{ marginBottom: 12 }}>
              Add up to 5 photos. If you don't upload any, a default image based on your cuisine choice will be used.
            </p>
            <div className="photo-preview-grid">
              {photoPreviewUrls.map((url, i) => (
                <div key={i} className="photo-thumb-wrap">
                  <img src={url} alt={`Preview ${i + 1}`} className="photo-thumb" />
                  <button type="button" className="photo-remove-btn" onClick={() => removePhoto(i)}>
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
          </fieldset>

          <div className="form-actions">
            <button
              type="submit"
              className="btn-primary"
              disabled={submitting}
            >
              {submitting ? (uploading ? "Uploading Photos..." : "Creating...") : "Create Restaurant"}
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
