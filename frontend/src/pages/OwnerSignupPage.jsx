import { useState } from "react";
import { Link, useNavigate } from "react-router-dom";

import ProjectLogo from "../components/ProjectLogo";
import api, { extractApiError } from "../services/api";

export default function OwnerSignupPage() {
  const navigate = useNavigate();
  const [form, setForm] = useState({
    name: "",
    email: "",
    password: "",
    confirmPassword: "",
    restaurant_location: ""
  });
  const [error, setError] = useState("");
  const [loading, setLoading] = useState(false);

  const handleChange = (event) => {
    const { name, value } = event.target;
    setForm((prev) => ({ ...prev, [name]: value }));
  };

  const handleSubmit = async (event) => {
    event.preventDefault();
    setError("");

    if (form.password !== form.confirmPassword) {
      setError("Passwords do not match.");
      return;
    }

    setLoading(true);
    try {
      await api.post("/auth/owner/signup", {
        name: form.name.trim(),
        email: form.email.trim(),
        password: form.password,
        restaurant_location: form.restaurant_location.trim()
      });
      navigate("/owner/login", { replace: true });
    } catch (requestError) {
      setError(extractApiError(requestError, "Owner signup failed."));
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="auth-shell">
      <header className="auth-topbar">
        <ProjectLogo />
      </header>

      <div className="auth-stage">
        <section className="auth-form-panel">
          <h1 className="auth-title">Create owner account</h1>
          <p className="auth-policy">Register as a restaurant owner.</p>

          <form onSubmit={handleSubmit} className="form-grid">
            <label>
              Name
              <input type="text" name="name" value={form.name} onChange={handleChange} required />
            </label>
            <label>
              Email
              <input type="email" name="email" value={form.email} onChange={handleChange} required />
            </label>
            <label>
              Restaurant Location
              <input
                type="text"
                name="restaurant_location"
                value={form.restaurant_location}
                onChange={handleChange}
                required
              />
            </label>
            <label>
              Password
              <input
                type="password"
                name="password"
                value={form.password}
                onChange={handleChange}
                required
              />
            </label>
            <label>
              Confirm Password
              <input
                type="password"
                name="confirmPassword"
                value={form.confirmPassword}
                onChange={handleChange}
                required
              />
            </label>
            {error ? <p className="error-text">{error}</p> : null}
            <button type="submit" disabled={loading} className="primary-action">
              {loading ? "Creating..." : "Create Owner Account"}
            </button>
          </form>
          <p className="auth-bottom-text">
            Already an owner? <Link to="/owner/login">Sign in</Link>
          </p>
          <p className="auth-bottom-text">
            Not an owner? <Link to="/signup">User Signup</Link>
          </p>
        </section>

        <aside className="auth-hero">
          <img src="/login.png" alt="Owner signup page illustration" />
        </aside>
      </div>
    </div>
  );
}
