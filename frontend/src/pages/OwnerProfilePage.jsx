import { useEffect, useState } from "react";

import { useOwnerAuth } from "../contexts/OwnerAuthContext";
import { extractApiError, ownerMgmtApi } from "../services/api";

export default function OwnerProfilePage() {
  const { refreshCurrentOwner } = useOwnerAuth();
  const [form, setForm] = useState({ name: "", restaurant_location: "" });
  const [email, setEmail] = useState("");
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
        const resp = await ownerMgmtApi.getProfile();
        if (!active) return;
        const { name, email: ownerEmail, restaurant_location } = resp.data;
        setEmail(ownerEmail || "");
        setForm({ name: name || "", restaurant_location: restaurant_location || "" });
      } catch (err) {
        if (active) setError(extractApiError(err, "Failed to load profile."));
      } finally {
        if (active) setLoading(false);
      }
    })();
    return () => { active = false; };
  }, []);

  const handleChange = (e) => {
    const { name, value } = e.target;
    setForm((prev) => ({ ...prev, [name]: value }));
  };

  const handleSubmit = async (e) => {
    e.preventDefault();
    setError("");
    setSuccess("");
    setSaving(true);
    try {
      const payload = {};
      if (form.name.trim()) payload.name = form.name.trim();
      if (form.restaurant_location.trim()) payload.restaurant_location = form.restaurant_location.trim();
      await ownerMgmtApi.updateProfile(payload);
      await refreshCurrentOwner();
      setSuccess("Profile updated.");
    } catch (err) {
      setError(extractApiError(err, "Failed to update profile."));
    } finally {
      setSaving(false);
    }
  };

  if (loading) return <div className="page-status">Loading profile...</div>;

  return (
    <section className="page-card">
      <h1 className="auth-title">Owner Profile</h1>
      <p className="muted">Manage your owner account details.</p>

      <form onSubmit={handleSubmit} className="form-grid">
        <label>
          Name
          <input
            type="text"
            name="name"
            value={form.name}
            onChange={handleChange}
            required
            minLength={1}
            maxLength={100}
          />
        </label>
        <label>
          Email (read-only)
          <input type="email" value={email} disabled />
        </label>
        <label className="full-row">
          Restaurant Location
          <input
            type="text"
            name="restaurant_location"
            value={form.restaurant_location}
            onChange={handleChange}
            placeholder="e.g. San Jose, CA"
            maxLength={255}
          />
        </label>

        {error ? <p className="error-text full-row">{error}</p> : null}
        {success ? <p className="success-text full-row">{success}</p> : null}

        <button type="submit" disabled={saving} className="full-row">
          {saving ? "Saving..." : "Save Profile"}
        </button>
      </form>
    </section>
  );
}
