import { useState } from "react";
import { Link, useNavigate } from "react-router-dom";

import ProjectLogo from "../components/ProjectLogo";
import { useAuth } from "../contexts/AuthContext";
import api, { extractApiError } from "../services/api";

export default function LoginPage() {
  const navigate = useNavigate();
  const { login } = useAuth();
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
      const response = await api.post("/auth/login", {
        email: form.email.trim(),
        password: form.password
      });
      login({
        accessToken: response.data.access_token,
        user: response.data.user
      });
      navigate("/profile", { replace: true });
    } catch (requestError) {
      setError(extractApiError(requestError, "Login failed."));
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
          <h1 className="auth-title">Log in to Dine Finder</h1>
          <p className="auth-policy">
            Use your email and password to continue.
          </p>

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
              {loading ? "Logging in..." : "Log In"}
            </button>
          </form>
          <p className="auth-bottom-text">
            New to Dine Finder? <Link to="/signup">Sign up</Link>
          </p>
        </section>

        <aside className="auth-hero">
          <img src="/login.png" alt="Login page illustration" />
        </aside>
      </div>
    </div>
  );
}
