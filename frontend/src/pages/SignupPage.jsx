import { useState } from "react";
import { Link, useNavigate } from "react-router-dom";

import ProjectLogo from "../components/ProjectLogo";
import api, { extractApiError } from "../services/api";

export default function SignupPage() {
  const navigate = useNavigate();
  const [form, setForm] = useState({
    name: "",
    email: "",
    password: "",
    confirmPassword: ""
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
      await api.post("/auth/signup", {
        name: form.name.trim(),
        email: form.email.trim(),
        password: form.password
      });
      navigate("/login", { replace: true });
    } catch (requestError) {
      setError(extractApiError(requestError, "Signup failed."));
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
          <h1 className="auth-title">Create your Dine Finder account</h1>
          <p className="auth-policy">Use your email to create an account.</p>

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
              {loading ? "Creating..." : "Create Account"}
            </button>
          </form>
          <p className="auth-bottom-text">
            Already have an account? <Link to="/login">Sign in</Link>
          </p>
          <p className="auth-bottom-text">
            Want to register as owner? <Link to="/owner/signup">Owner Signup</Link>
          </p>
        </section>

        <aside className="auth-hero">
          <img src="/login.png" alt="Signup page illustration" />
        </aside>
      </div>
    </div>
  );
}
