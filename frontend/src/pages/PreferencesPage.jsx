import { useEffect, useState } from "react";

import api, { extractApiError } from "../services/api";

const EMPTY_FORM = {
  cuisines: "",
  price_range: "",
  preferred_locations: "",
  search_radius_km: "",
  dietary_needs: "",
  ambiance: "",
  sort_preference: "rating"
};

function toCommaList(value) {
  if (!value || !Array.isArray(value)) {
    return "";
  }
  return value.join(", ");
}

function toList(value) {
  if (!value) {
    return [];
  }
  return value
    .split(",")
    .map((item) => item.trim())
    .filter(Boolean);
}

function preferencesToForm(data) {
  return {
    cuisines: toCommaList(data?.cuisines),
    price_range: data?.price_range || "",
    preferred_locations: toCommaList(data?.preferred_locations),
    search_radius_km: data?.search_radius_km ?? "",
    dietary_needs: toCommaList(data?.dietary_needs),
    ambiance: toCommaList(data?.ambiance),
    sort_preference: data?.sort_preference || "rating"
  };
}

export default function PreferencesPage() {
  const [form, setForm] = useState(EMPTY_FORM);
  const [loading, setLoading] = useState(true);
  const [saving, setSaving] = useState(false);
  const [error, setError] = useState("");
  const [success, setSuccess] = useState("");

  useEffect(() => {
    let active = true;

    async function loadPreferences() {
      setLoading(true);
      setError("");
      try {
        const response = await api.get("/users/me/preferences");
        if (active) {
          setForm(preferencesToForm(response.data));
        }
      } catch (requestError) {
        if (active) {
          setError(extractApiError(requestError, "Failed to load preferences."));
        }
      } finally {
        if (active) {
          setLoading(false);
        }
      }
    }

    loadPreferences();
    return () => {
      active = false;
    };
  }, []);

  const handleChange = (event) => {
    const { name, value } = event.target;
    setForm((prev) => ({ ...prev, [name]: value }));
  };

  const handleSubmit = async (event) => {
    event.preventDefault();
    setSaving(true);
    setError("");
    setSuccess("");

    const payload = {
      cuisines: toList(form.cuisines),
      price_range: form.price_range || null,
      preferred_locations: toList(form.preferred_locations),
      search_radius_km:
        form.search_radius_km === "" ? null : Number.parseInt(form.search_radius_km, 10),
      dietary_needs: toList(form.dietary_needs),
      ambiance: toList(form.ambiance),
      sort_preference: form.sort_preference || "rating"
    };

    try {
      const response = await api.put("/users/me/preferences", payload);
      setForm(preferencesToForm(response.data));
      setSuccess("Preferences updated.");
    } catch (requestError) {
      setError(extractApiError(requestError, "Failed to update preferences."));
    } finally {
      setSaving(false);
    }
  };

  if (loading) {
    return <div className="page-status">Loading preferences...</div>;
  }

  return (
    <section className="page-card">
      <h1>Preferences</h1>
      <p className="muted">Used by AI assistant and restaurant recommendation flow.</p>
      <form onSubmit={handleSubmit} className="form-grid two-col">
        <label>
          Cuisines (comma separated)
          <input type="text" name="cuisines" value={form.cuisines} onChange={handleChange} />
        </label>
        <label>
          Price Range
          <select name="price_range" value={form.price_range} onChange={handleChange}>
            <option value="">Select</option>
            <option value="$">$</option>
            <option value="$$">$$</option>
            <option value="$$$">$$$</option>
            <option value="$$$$">$$$$</option>
          </select>
        </label>
        <label>
          Preferred Locations (comma separated)
          <input
            type="text"
            name="preferred_locations"
            value={form.preferred_locations}
            onChange={handleChange}
          />
        </label>
        <label>
          Search Radius (km)
          <input
            type="number"
            name="search_radius_km"
            min={0}
            value={form.search_radius_km}
            onChange={handleChange}
          />
        </label>
        <label>
          Dietary Needs (comma separated)
          <input
            type="text"
            name="dietary_needs"
            value={form.dietary_needs}
            onChange={handleChange}
          />
        </label>
        <label>
          Ambiance (comma separated)
          <input type="text" name="ambiance" value={form.ambiance} onChange={handleChange} />
        </label>
        <label>
          Sort Preference
          <select name="sort_preference" value={form.sort_preference} onChange={handleChange}>
            <option value="rating">rating</option>
            <option value="distance">distance</option>
            <option value="popularity">popularity</option>
            <option value="price">price</option>
          </select>
        </label>
        {error ? <p className="error-text full-row">{error}</p> : null}
        {success ? <p className="success-text full-row">{success}</p> : null}
        <button type="submit" disabled={saving}>
          {saving ? "Saving..." : "Save Preferences"}
        </button>
      </form>
    </section>
  );
}
