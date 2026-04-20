import { useEffect, useRef, useState } from "react";
import { useNavigate, useParams } from "react-router-dom";

import api, { extractApiError, ownerApi, ownerMgmtApi } from "../services/api";
import { CUISINE_OPTIONS } from "../constants/cuisine";

const PRICING_TIERS = ["$", "$$", "$$$", "$$$$"];

const EMPTY_FORM = {
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
  amenities: "",
  hours_json: "",
};

function restaurantToForm(r) {
  return {
    name: r.name || "",
    cuisine_type: r.cuisine_type || "",
    description: r.description || "",
    street: r.street || "",
    city: r.city || "",
    state: r.state || "",
    zip_code: r.zip_code || "",
    country: r.country || "",
    latitude: r.latitude != null ? String(r.latitude) : "",
    longitude: r.longitude != null ? String(r.longitude) : "",
    phone: r.phone || "",
    email: r.email || "",
    pricing_tier: r.pricing_tier || "",
    amenities: Array.isArray(r.amenities) ? r.amenities.join(", ") : "",
    hours_json: (r.hours_json || r.hours) ? JSON.stringify(r.hours_json || r.hours, null, 2) : "",
  };
}

export default function OwnerRestaurantEditPage() {
  const { id } = useParams();
  const navigate = useNavigate();
  const [form, setForm] = useState(EMPTY_FORM);
  const [loading, setLoading] = useState(true);
  const [saving, setSaving] = useState(false);
  const [error, setError] = useState("");
  const [success, setSuccess] = useState("");
  const [restaurantData, setRestaurantData] = useState(null);

  // Photo states
  const photoInputRef = useRef(null);
  const [photoFiles, setPhotoFiles] = useState([]);
  const [photoPreviewUrls, setPhotoPreviewUrls] = useState([]);
  const [uploading, setUploading] = useState(false);
  const [photoError, setPhotoError] = useState("");
  const [photoSuccess, setPhotoSuccess] = useState("");

  useEffect(() => {
    let active = true;
    (async () => {
      setLoading(true);
      setError("");
      try {
        const resp = await api.get(`/restaurants/${id}`);
        if (active) {
          setForm(restaurantToForm(resp.data));
          setRestaurantData(resp.data);
        }
      } catch (err) {
        if (active) setError(extractApiError(err, "Failed to load restaurant."));
      } finally {
        if (active) setLoading(false);
      }
    })();
    return () => { active = false; };
  }, [id]);

  const handleChange = (e) => {
    const { name, value } = e.target;
    setForm((prev) => ({ ...prev, [name]: value }));
  };

  const handleSubmit = async (e) => {
    e.preventDefault();
    setError("");
    setSuccess("");

    // Validate hours_json if provided
    let parsedHours = undefined;
    if (form.hours_json.trim()) {
      try {
        parsedHours = JSON.parse(form.hours_json);
      } catch {
        setError("Hours JSON is not valid JSON. Please fix it before saving.");
        return;
      }
    }

    setSaving(true);
    try {
      const payload = {};
      if (form.name.trim()) payload.name = form.name.trim();
      if (form.cuisine_type.trim()) payload.cuisine_type = form.cuisine_type.trim();
      if (form.description.trim()) payload.description = form.description.trim();
      if (form.street.trim()) payload.street = form.street.trim();
      if (form.city.trim()) payload.city = form.city.trim();
      if (form.state.trim()) payload.state = form.state.trim();
      if (form.zip_code.trim()) payload.zip_code = form.zip_code.trim();
      if (form.country.trim()) payload.country = form.country.trim();
      if (form.latitude.trim()) payload.latitude = parseFloat(form.latitude);
      if (form.longitude.trim()) payload.longitude = parseFloat(form.longitude);
      if (form.phone.trim()) payload.phone = form.phone.trim();
      if (form.email.trim()) payload.email = form.email.trim();
      if (form.pricing_tier) payload.pricing_tier = form.pricing_tier;
      if (form.amenities.trim()) {
        payload.amenities = form.amenities
          .split(",")
          .map((a) => a.trim())
          .filter(Boolean);
      }
      if (parsedHours !== undefined) payload.hours_json = parsedHours;

      await ownerMgmtApi.updateRestaurant(id, payload);
      setSuccess("Restaurant updated successfully.");
      window.scrollTo(0, 0);
    } catch (err) {
      const msg = extractApiError(err, "Failed to update restaurant.");
      if (err?.response?.status === 403) {
        setError("You don't own this restaurant.");
      } else {
        setError(msg);
      }
    } finally {
      setSaving(false);
    }
  };

  const handlePhotoSelect = (e) => {
    const files = Array.from(e.target.files || []);
    const total = (restaurantData?.photos?.length || 0) + photoFiles.length + files.length;
    if (total > 5) {
      setPhotoError("Maximum 5 photos allowed per restaurant.");
      return;
    }
    setPhotoError("");
    setPhotoFiles((prev) => [...prev, ...files]);
    const newPreviews = files.map((f) => URL.createObjectURL(f));
    setPhotoPreviewUrls((prev) => [...prev, ...newPreviews]);
    e.target.value = "";
  };

  const removePhotoFile = (index) => {
    URL.revokeObjectURL(photoPreviewUrls[index]);
    setPhotoFiles((prev) => prev.filter((_, i) => i !== index));
    setPhotoPreviewUrls((prev) => prev.filter((_, i) => i !== index));
  };

  const handlePhotoUpload = async () => {
    if (photoFiles.length === 0) return;
    setPhotoError("");
    setPhotoSuccess("");
    setUploading(true);

    const formData = new FormData();
    photoFiles.forEach((f) => formData.append("files", f));

    try {
      await ownerApi.post(`/restaurants/${id}/photos`, formData, {
        headers: { "Content-Type": "multipart/form-data" },
      });
      setPhotoSuccess(`${photoFiles.length} photo(s) uploaded successfully!`);
      setPhotoFiles([]);
      setPhotoPreviewUrls([]);
      // Reload restaurant to show new photos
      const resp = await api.get(`/restaurants/${id}`);
      setRestaurantData(resp.data);
      setForm(restaurantToForm(resp.data));
    } catch (err) {
      setPhotoError(extractApiError(err, "Photo upload failed."));
    } finally {
      setUploading(false);
    }
  };

  const handleDeletePhoto = async (photoId) => {
    if (!window.confirm("Delete this photo?")) return;
    setPhotoError("");
    setPhotoSuccess("");
    try {
      await ownerApi.delete(`/restaurants/${id}/photos/${photoId}`);
      setPhotoSuccess("Photo deleted.");
      // Reload restaurant
      const resp = await api.get(`/restaurants/${id}`);
      setRestaurantData(resp.data);
      setForm(restaurantToForm(resp.data));
    } catch (err) {
      setPhotoError(extractApiError(err, "Failed to delete photo."));
    }
  };

  if (loading) return <div className="page-status">Loading restaurant...</div>;

  return (
    <div className="owner-page">
      <div className="owner-page-header">
        <h1 className="owner-page-title">Edit Restaurant</h1>
        <button
          type="button"
          className="btn-owner-nav"
          onClick={() => navigate(-1)}
        >
          ← Back
        </button>
      </div>

      {error && <div className="alert alert--error">{error}</div>}
      {success && <div className="alert alert--success">{success}</div>}

      <section className="page-card" style={{ marginBottom: 24 }}>
        <h2 className="section-heading">Restaurant Photos</h2>
        {photoError && <div className="alert alert--error">{photoError}</div>}
        {photoSuccess && <div className="alert alert--success">{photoSuccess}</div>}

        <div className="photo-preview-grid">
          {/* Existing photos */}
          {restaurantData?.photos?.map((p) => (
            <div key={p.id} className="photo-thumb-wrap">
              <img src={p.photo_url} alt="Restaurant" className="photo-thumb" />
              <button
                type="button"
                className="photo-remove-btn"
                onClick={() => handleDeletePhoto(p.id)}
                title="Delete photo"
              >
                ×
              </button>
            </div>
          ))}

          {/* New files pending upload */}
          {photoPreviewUrls.map((url, i) => (
            <div key={`new-${i}`} className="photo-thumb-wrap" style={{ opacity: 0.7 }}>
              <img src={url} alt="New upload" className="photo-thumb" />
              <button
                type="button"
                className="photo-remove-btn"
                onClick={() => removePhotoFile(i)}
                title="Remove from queue"
              >
                ×
              </button>
            </div>
          ))}

          {(restaurantData?.photos?.length || 0) + photoFiles.length < 5 && (
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

        {photoFiles.length > 0 && (
          <button
            type="button"
            className="btn-primary"
            style={{ marginTop: 16 }}
            onClick={handlePhotoUpload}
            disabled={uploading}
          >
            {uploading ? "Uploading..." : `Upload ${photoFiles.length} New Photo(s)`}
          </button>
        )}
      </section>

      <form onSubmit={handleSubmit} className="form-grid two-col owner-edit-form">
        {/* Basic info */}
        <label className="full-row">
          Restaurant Name *
          <input
            type="text"
            name="name"
            value={form.name}
            onChange={handleChange}
            required
            maxLength={200}
          />
        </label>
        <label>
          Cuisine Type
          <select
            name="cuisine_type"
            value={form.cuisine_type}
            onChange={handleChange}
          >
            <option value="">— Select —</option>
            {CUISINE_OPTIONS.map((c) => (
              <option key={c} value={c}>{c}</option>
            ))}
          </select>
        </label>
        <label>
          Pricing Tier
          <select name="pricing_tier" value={form.pricing_tier} onChange={handleChange}>
            <option value="">— Select —</option>
            {PRICING_TIERS.map((t) => (
              <option key={t} value={t}>{t}</option>
            ))}
          </select>
        </label>
        <label className="full-row">
          Description
          <textarea
            name="description"
            value={form.description}
            onChange={handleChange}
            rows={3}
          />
        </label>

        {/* Address */}
        <label className="full-row">
          Street
          <input type="text" name="street" value={form.street} onChange={handleChange} maxLength={255} />
        </label>
        <label>
          City
          <input type="text" name="city" value={form.city} onChange={handleChange} maxLength={100} />
        </label>
        <label>
          State
          <input type="text" name="state" value={form.state} onChange={handleChange} maxLength={50} />
        </label>
        <label>
          ZIP Code
          <input type="text" name="zip_code" value={form.zip_code} onChange={handleChange} maxLength={20} />
        </label>
        <label>
          Country
          <input type="text" name="country" value={form.country} onChange={handleChange} maxLength={100} />
        </label>

        {/* Contact */}
        <label>
          Phone
          <input type="text" name="phone" value={form.phone} onChange={handleChange} maxLength={30} />
        </label>
        <label>
          Email
          <input type="email" name="email" value={form.email} onChange={handleChange} maxLength={255} />
        </label>

        {/* Coordinates */}
        <label>
          Latitude
          <input
            type="number"
            name="latitude"
            value={form.latitude}
            onChange={handleChange}
            step="any"
            min="-90"
            max="90"
          />
        </label>
        <label>
          Longitude
          <input
            type="number"
            name="longitude"
            value={form.longitude}
            onChange={handleChange}
            step="any"
            min="-180"
            max="180"
          />
        </label>

        {/* Amenities */}
        <label className="full-row">
          Amenities
          <input
            type="text"
            name="amenities"
            value={form.amenities}
            onChange={handleChange}
            placeholder="Comma-separated: WiFi, Outdoor Seating, Parking"
          />
          <span className="field-hint">Separate each amenity with a comma.</span>
        </label>

        {/* Hours JSON */}
        <label className="full-row">
          Hours (JSON)
          <textarea
            name="hours_json"
            value={form.hours_json}
            onChange={handleChange}
            rows={5}
            placeholder={'{\n  "mon": "9am-9pm",\n  "tue": "9am-9pm"\n}'}
            className="hours-textarea"
          />
          <span className="field-hint">Must be valid JSON or leave blank.</span>
        </label>

        <div className="full-row owner-form-actions">
          <button type="submit" disabled={saving} className="btn-primary">
            {saving ? "Saving..." : "Save Changes"}
          </button>
          <button
            type="button"
            className="btn-secondary"
            onClick={() => navigate(-1)}
            disabled={saving}
          >
            Cancel
          </button>
        </div>
      </form>
    </div>
  );
}
