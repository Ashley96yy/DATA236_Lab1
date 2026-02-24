import { useState } from "react";
import { Link, useNavigate } from "react-router-dom";

import ProjectLogo from "../components/ProjectLogo";
import { useOwnerAuth } from "../contexts/OwnerAuthContext";
import api, { extractApiError, ownerApi } from "../services/api";

export default function OwnerLoginPage() {
  const navigate = useNavigate();
  const { ownerLogin } = useOwnerAuth();
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
        password: form.password,
      });

      const token = loginResponse.data.access_token;
      const meResponse = await ownerApi.get("/owners/me", {
        headers: { Authorization: `Bearer ${token}` },
      });

      ownerLogin({ accessToken: token, owner: meResponse.data });
      navigate("/owner/dashboard", { replace: true });
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
          <p className="auth-bottom-text">
            Not an owner? <Link to="/login">User Login</Link>
          </p>
        </section>

        <aside className="auth-hero">
          <img src="/login.png" alt="Owner login page illustration" />
        </aside>
      </div>
    </div>
  );
}
