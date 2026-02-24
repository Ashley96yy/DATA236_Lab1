import { useEffect, useState } from "react";
import { useNavigate, useParams } from "react-router-dom";

import api, { extractApiError, ownerMgmtApi } from "../services/api";

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
    hours_json: r.hours_json ? JSON.stringify(r.hours_json, null, 2) : "",
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

  useEffect(() => {
    let active = true;
    (async () => {
      setLoading(true);
      setError("");
      try {
        const resp = await api.get(`/restaurants/${id}`);
        if (active) setForm(restaurantToForm(resp.data));
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
          <input
            type="text"
            name="cuisine_type"
            value={form.cuisine_type}
            onChange={handleChange}
            maxLength={100}
          />
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
