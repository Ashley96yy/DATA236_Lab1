import { useEffect, useRef, useState } from "react";

import api, { extractApiError } from "../services/api";

const EMPTY_FORM = {
  cuisines: [],
  price_range: "",
  location: "",
  search_radius_km: "",
  dietary_needs: [],
  ambiance: [],
  sort_preference: "rating"
};

const CUISINE_OPTIONS = [
  "American",
  "Chinese",
  "French",
  "Indian",
  "Italian",
  "Japanese",
  "Korean",
  "Mediterranean",
  "Mexican",
  "Thai",
  "Vietnamese"
];

const DIETARY_OPTIONS = [
  "Dairy-free",
  "Gluten-free",
  "Halal",
  "Kosher",
  "Keto",
  "Nut-free",
  "Pescatarian",
  "Vegan",
  "Vegetarian"
];

const AMBIANCE_OPTIONS = [
  "Casual",
  "Family-friendly",
  "Fine Dining",
  "Outdoor",
  "Quiet",
  "Romantic",
  "Trendy"
];

function preferencesToForm(data) {
  const firstLocation = Array.isArray(data?.preferred_locations)
    ? data.preferred_locations[0] || ""
    : "";

  return {
    cuisines: Array.isArray(data?.cuisines) ? data.cuisines : [],
    price_range: data?.price_range || "",
    location: firstLocation,
    search_radius_km: data?.search_radius_km ?? "",
    dietary_needs: Array.isArray(data?.dietary_needs) ? data.dietary_needs : [],
    ambiance: Array.isArray(data?.ambiance) ? data.ambiance : [],
    sort_preference: data?.sort_preference || "rating"
  };
}

function mergeOptions(baseOptions, selectedOptions) {
  return [...new Set([...baseOptions, ...(selectedOptions || [])])];
}

function MultiSelectDropdown({ label, name, options, selectedValues, onToggle }) {
  const [isOpen, setIsOpen] = useState(false);
  const containerRef = useRef(null);
  const summaryText =
    selectedValues.length > 0 ? selectedValues.join(", ") : `Select ${label.toLowerCase()}`;

  useEffect(() => {
    if (!isOpen) {
      return undefined;
    }

    const handlePointerDown = (event) => {
      if (containerRef.current && !containerRef.current.contains(event.target)) {
        setIsOpen(false);
      }
    };

    const handleEscape = (event) => {
      if (event.key === "Escape") {
        setIsOpen(false);
      }
    };

    document.addEventListener("mousedown", handlePointerDown);
    document.addEventListener("touchstart", handlePointerDown);
    document.addEventListener("keydown", handleEscape);

    return () => {
      document.removeEventListener("mousedown", handlePointerDown);
      document.removeEventListener("touchstart", handlePointerDown);
      document.removeEventListener("keydown", handleEscape);
    };
  }, [isOpen]);

  return (
    <div className="field-group full-row">
      <span className="field-label">{label}</span>
      <div className={`multi-select-dropdown ${isOpen ? "open" : ""}`} ref={containerRef}>
        <button
          type="button"
          className="multi-select-trigger"
          onClick={() => setIsOpen((prev) => !prev)}
          aria-expanded={isOpen}
        >
          <span className="multi-select-trigger-text" title={summaryText}>
            {summaryText}
          </span>
          <span className="multi-select-trigger-icon" aria-hidden="true">
            {isOpen ? "▴" : "▾"}
          </span>
        </button>
        {isOpen ? (
          <div className="multi-select-menu">
            {options.map((option) => (
              <label key={option} className="multi-select-option">
                <input
                  type="checkbox"
                  checked={selectedValues.includes(option)}
                  onChange={() => onToggle(name, option)}
                />
                <span>{option}</span>
              </label>
            ))}
            <div className="multi-select-actions">
              <button
                type="button"
                className="multi-select-done"
                onClick={() => setIsOpen(false)}
              >
                Done
              </button>
            </div>
          </div>
        ) : null}
      </div>
    </div>
  );
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

  const handleMultiSelectToggle = (fieldName, optionValue) => {
    setForm((prev) => {
      const currentValues = prev[fieldName] || [];
      const exists = currentValues.includes(optionValue);
      return {
        ...prev,
        [fieldName]: exists
          ? currentValues.filter((value) => value !== optionValue)
          : [...currentValues, optionValue]
      };
    });
  };

  const handleSubmit = async (event) => {
    event.preventDefault();
    setSaving(true);
    setError("");
    setSuccess("");

    const payload = {
      cuisines: form.cuisines,
      price_range: form.price_range || null,
      preferred_locations: form.location.trim() ? [form.location.trim()] : [],
      search_radius_km:
        form.search_radius_km === "" ? null : Number.parseInt(form.search_radius_km, 10),
      dietary_needs: form.dietary_needs,
      ambiance: form.ambiance,
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

  const cuisineOptions = mergeOptions(CUISINE_OPTIONS, form.cuisines);
  const dietaryOptions = mergeOptions(DIETARY_OPTIONS, form.dietary_needs);
  const ambianceOptions = mergeOptions(AMBIANCE_OPTIONS, form.ambiance);

  return (
    <section className="page-card">
      <h1>Preferences</h1>
      <p className="muted">Set your dining preferences for personalized recommendations.</p>
      <form onSubmit={handleSubmit} className="form-grid two-col">
        <MultiSelectDropdown
          label="Cuisine"
          name="cuisines"
          options={cuisineOptions}
          selectedValues={form.cuisines}
          onToggle={handleMultiSelectToggle}
        />
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
          Location
          <input
            type="text"
            name="location"
            value={form.location}
            onChange={handleChange}
            placeholder="City or neighborhood"
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
        <MultiSelectDropdown
          label="Dietary Restrictions"
          name="dietary_needs"
          options={dietaryOptions}
          selectedValues={form.dietary_needs}
          onToggle={handleMultiSelectToggle}
        />
        <MultiSelectDropdown
          label="Ambiance"
          name="ambiance"
          options={ambianceOptions}
          selectedValues={form.ambiance}
          onToggle={handleMultiSelectToggle}
        />
        <label>
          Sort Preference
          <select name="sort_preference" value={form.sort_preference} onChange={handleChange}>
            <option value="rating">Rating</option>
            <option value="distance">Distance</option>
            <option value="popularity">Popularity</option>
            <option value="price">Price</option>
          </select>
        </label>
        {error ? <p className="error-text full-row">{error}</p> : null}
        {success ? <p className="success-text full-row">{success}</p> : null}
        <button type="submit" disabled={saving} className="preferences-submit">
          {saving ? "Saving..." : "Save Preferences"}
        </button>
      </form>
    </section>
  );
}
