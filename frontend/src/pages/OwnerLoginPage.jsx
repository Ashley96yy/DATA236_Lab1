import { useState } from "react";
import { Link, useNavigate } from "react-router-dom";

import ProjectLogo from "../components/ProjectLogo";
import api, { extractApiError } from "../services/api";

const OWNER_TOKEN_KEY = "yelp_lab1_owner_token";
const OWNER_PROFILE_KEY = "yelp_lab1_owner";

export default function OwnerLoginPage() {
  const navigate = useNavigate();
  const [form, setForm] = useState({ email: "", password: "" });
  const [error, setError] = useState("");
  const [loading, setLoading] = useState(false);

  const handleChange = (event) => {
    const { name, value } = event.target;
    setForm((prev) => ({ ...prev, [name]: value }));
  };

  const handleSubmit = async (event) => {
    event.preventDefault();
    setError("");
    setLoading(true);

    try {
      const loginResponse = await api.post("/auth/owner/login", {
        email: form.email.trim(),
        password: form.password
      });

      const token = loginResponse.data.access_token;
      localStorage.setItem(OWNER_TOKEN_KEY, token);

      const meResponse = await api.get("/owners/me", {
        headers: { Authorization: `Bearer ${token}` }
      });
      localStorage.setItem(OWNER_PROFILE_KEY, JSON.stringify(meResponse.data));

      navigate("/", { replace: true });
    } catch (requestError) {
      setError(extractApiError(requestError, "Owner login failed."));
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
          <h1 className="auth-title">Owner login</h1>
          <p className="auth-policy">Sign in to your owner account.</p>

          <form onSubmit={handleSubmit} className="form-grid">
            <label>
              Email
              <input
                type="email"
                name="email"
                value={form.email}
                onChange={handleChange}
                required
                autoComplete="email"
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
                autoComplete="current-password"
              />
            </label>
            {error ? <p className="error-text">{error}</p> : null}
            <button type="submit" disabled={loading} className="primary-action">
              {loading ? "Logging in..." : "Log In as Owner"}
            </button>
          </form>
          <p className="auth-bottom-text">
            New owner? <Link to="/owner/signup">Create owner account</Link>
          </p>
        </section>

        <aside className="auth-hero">
          <img src="/login.png" alt="Owner login page illustration" />
        </aside>
      </div>
    </div>
  );
}
