import { useEffect, useRef, useState } from "react";

import { useAuth } from "../contexts/AuthContext";
import api, { extractApiError } from "../services/api";

const EMPTY_FORM = {
  name: "",
  phone: "",
  about_me: "",
  city: "",
  state: "",
  country: "",
  languages: "",
  gender: ""
};

const COUNTRY_OPTIONS = [
  { code: "CA", label: "Canada" },
  { code: "CN", label: "China" },
  { code: "FR", label: "France" },
  { code: "DE", label: "Germany" },
  { code: "IN", label: "India" },
  { code: "JP", label: "Japan" },
  { code: "MX", label: "Mexico" },
  { code: "KR", label: "South Korea" },
  { code: "GB", label: "United Kingdom" },
  { code: "US", label: "United States" }
];

const LANGUAGE_OPTIONS = [
  "Arabic",
  "Bengali",
  "Chinese",
  "English",
  "French",
  "German",
  "Hindi",
  "Italian",
  "Japanese",
  "Korean",
  "Portuguese",
  "Punjabi",
  "Russian",
  "Spanish",
  "Tamil",
  "Telugu",
  "Turkish",
  "Urdu",
  "Vietnamese"
];

const US_STATE_OPTIONS = [
  "AK",
  "AL",
  "AR",
  "AZ",
  "CA",
  "CO",
  "CT",
  "DC",
  "DE",
  "FL",
  "GA",
  "HI",
  "IA",
  "ID",
  "IL",
  "IN",
  "KS",
  "KY",
  "LA",
  "MA",
  "MD",
  "ME",
  "MI",
  "MN",
  "MO",
  "MS",
  "MT",
  "NC",
  "ND",
  "NE",
  "NH",
  "NJ",
  "NM",
  "NV",
  "NY",
  "OH",
  "OK",
  "OR",
  "PA",
  "RI",
  "SC",
  "SD",
  "TN",
  "TX",
  "UT",
  "VA",
  "VT",
  "WA",
  "WI",
  "WV",
  "WY"
];

function toPrimaryLanguage(value) {
  if (!value) {
    return "";
  }
  if (value.includes(",")) {
    return value.split(",")[0].trim();
  }
  return value.trim();
}

function profileToForm(profile) {
  return {
    name: profile?.name || "",
    phone: profile?.phone || "",
    about_me: profile?.about_me || "",
    city: profile?.city || "",
    state: profile?.state || "",
    country: profile?.country || "",
    languages: toPrimaryLanguage(profile?.languages || ""),
    gender: profile?.gender || ""
  };
}

export default function ProfilePage() {
  const { refreshCurrentUser } = useAuth();
  const fileInputRef = useRef(null);
  const [email, setEmail] = useState("");
  const [avatarUrl, setAvatarUrl] = useState("");
  const [form, setForm] = useState(EMPTY_FORM);
  const [loading, setLoading] = useState(true);
  const [saving, setSaving] = useState(false);
  const [avatarUploading, setAvatarUploading] = useState(false);
  const [avatarError, setAvatarError] = useState("");
  const [error, setError] = useState("");
  const [success, setSuccess] = useState("");

  useEffect(() => {
    let active = true;

    async function loadProfile() {
      setLoading(true);
      setError("");
      try {
        const response = await api.get("/users/me");
        if (!active) {
          return;
        }
        setEmail(response.data.email || "");
        setAvatarUrl(response.data.avatar_url || "");
        setForm(profileToForm(response.data));
      } catch (requestError) {
        if (active) {
          setError(extractApiError(requestError, "Failed to load profile."));
        }
      } finally {
        if (active) {
          setLoading(false);
        }
      }
    }

    loadProfile();
    return () => {
      active = false;
    };
  }, []);

  const handleChange = (event) => {
    const { name, value } = event.target;
    setForm((prev) => {
      if (name === "country") {
        const upperCountry = value.toUpperCase();
        return {
          ...prev,
          country: upperCountry,
          state: upperCountry === "US" ? prev.state : ""
        };
      }
      return { ...prev, [name]: value };
    });
  };

  const handleAvatarButtonClick = () => {
    fileInputRef.current?.click();
  };

  const handleAvatarChange = async (event) => {
    const file = event.target.files?.[0];
    if (!file) {
      return;
    }

    setAvatarError("");
    setAvatarUploading(true);

    try {
      const formData = new FormData();
      formData.append("file", file);
      const response = await api.post("/users/me/avatar", formData, {
        headers: { "Content-Type": "multipart/form-data" }
      });
      setAvatarUrl(response.data.avatar_url);
      await refreshCurrentUser();
    } catch (requestError) {
      setAvatarError(extractApiError(requestError, "Failed to upload avatar."));
    } finally {
      setAvatarUploading(false);
      event.target.value = "";
    }
  };

  const handleSubmit = async (event) => {
    event.preventDefault();
    setError("");
    setSuccess("");
    setSaving(true);

    const payload = {
      name: form.name.trim() || null,
      phone: form.phone.trim() || null,
      about_me: form.about_me.trim() || null,
      city: form.city.trim() || null,
      state: form.state.trim() ? form.state.trim().toUpperCase() : null,
      country: form.country.trim() ? form.country.trim().toUpperCase() : null,
      languages: form.languages.trim() || null,
      gender: form.gender || null
    };

    try {
      const response = await api.put("/users/me", payload);
      setEmail(response.data.email || "");
      setForm(profileToForm(response.data));
      await refreshCurrentUser();
      setSuccess("Profile updated.");
    } catch (requestError) {
      setError(extractApiError(requestError, "Failed to update profile."));
    } finally {
      setSaving(false);
    }
  };

  if (loading) {
    return <div className="page-status">Loading profile...</div>;
  }

  return (
    <section className="page-card">
      <h1 className="auth-title">Profile</h1>
      <p className="muted">Manage your user details for Week 1.</p>
      <div className="profile-avatar-section">
        <div className="profile-avatar-header">
          <h2>Your Profile Photo</h2>
          <button
            type="button"
            className="profile-avatar-btn"
            onClick={handleAvatarButtonClick}
            disabled={avatarUploading}
          >
            {avatarUploading ? "Uploading..." : avatarUrl ? "Edit" : "Upload"}
          </button>
        </div>
        <div className="profile-avatar-box">
          {avatarUrl ? (
            <img src={avatarUrl} alt="Profile avatar" className="profile-avatar-image" />
          ) : (
            <div className="profile-avatar-placeholder">No photo</div>
          )}
        </div>
        <input
          ref={fileInputRef}
          type="file"
          accept="image/png,image/jpeg,image/webp,image/gif"
          onChange={handleAvatarChange}
          hidden
        />
        {avatarError ? <p className="error-text">{avatarError}</p> : null}
      </div>
      <hr className="profile-divider" />
      <form onSubmit={handleSubmit} className="form-grid two-col">
        <label>
          Name
          <input type="text" name="name" value={form.name} onChange={handleChange} required />
        </label>
        <label>
          Email (read-only)
          <input type="email" value={email} disabled />
        </label>
        <label>
          Phone
          <input type="text" name="phone" value={form.phone} onChange={handleChange} />
        </label>
        <label>
          City
          <input type="text" name="city" value={form.city} onChange={handleChange} />
        </label>
        <label>
          State (abbreviation)
          <select
            name="state"
            value={form.state}
            onChange={handleChange}
            disabled={form.country !== "US"}
          >
            <option value="">
              {form.country === "US" ? "Select state" : "Select country first (US only)"}
            </option>
            {US_STATE_OPTIONS.map((stateCode) => (
              <option key={stateCode} value={stateCode}>
                {stateCode}
              </option>
            ))}
          </select>
        </label>
        <label>
          Country
          <select name="country" value={form.country} onChange={handleChange}>
            <option value="">Select country</option>
            {COUNTRY_OPTIONS.map((country) => (
              <option key={country.code} value={country.code}>
                {country.label}
              </option>
            ))}
          </select>
        </label>
        <label>
          Primary Language
          <select name="languages" value={form.languages} onChange={handleChange}>
            <option value="">Select language</option>
            {LANGUAGE_OPTIONS.map((language) => (
              <option key={language} value={language}>
                {language}
              </option>
            ))}
          </select>
        </label>
        <label>
          Gender
          <select name="gender" value={form.gender} onChange={handleChange}>
            <option value="">Select</option>
            <option value="female">Female</option>
            <option value="male">Male</option>
            <option value="other">Other</option>
          </select>
        </label>
        <label className="full-row">
          About Me
          <textarea name="about_me" value={form.about_me} onChange={handleChange} rows={4} />
        </label>
        {error ? <p className="error-text full-row">{error}</p> : null}
        {success ? <p className="success-text full-row">{success}</p> : null}
        <button type="submit" disabled={saving}>
          {saving ? "Saving..." : "Save Profile"}
        </button>
      </form>
    </section>
  );
}
