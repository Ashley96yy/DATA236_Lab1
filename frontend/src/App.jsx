import { Link, Navigate, Route, Routes, useLocation } from "react-router-dom";

import ProtectedRoute from "./components/ProtectedRoute";
import PublicRoute from "./components/PublicRoute";
import TopNav from "./components/TopNav";
import { useAuth } from "./contexts/AuthContext";
import LoginPage from "./pages/LoginPage";
import PreferencesPage from "./pages/PreferencesPage";
import ProfilePage from "./pages/ProfilePage";
import SignupPage from "./pages/SignupPage";

function ExplorePage() {
  return (
    <section className="page-card">
      <h1 className="auth-title">Explore Restaurants</h1>
      <p className="muted">Phase 0 public home page placeholder.</p>
      <p>
        Continue with <Link to="/login">Login</Link> or <Link to="/signup">Signup</Link>.
      </p>
    </section>
  );
}

function PlaceholderPage({ title, description }) {
  return (
    <section className="page-card">
      <h1>{title}</h1>
      <p className="muted">{description}</p>
    </section>
  );
}

export default function App() {
  const location = useLocation();
  const { isAuthenticated, isAuthReady } = useAuth();
  const isAuthRoute =
    location.pathname === "/login" ||
    location.pathname === "/signup" ||
    location.pathname === "/owner/login" ||
    location.pathname === "/owner/signup";

  if (!isAuthReady) {
    return <div className="page-status">Loading...</div>;
  }

  return (
    <div className="app-shell">
      {!isAuthRoute ? <TopNav /> : null}
      <main className={isAuthRoute ? "page-plain" : "page-wrap"}>
        <Routes>
          <Route path="/" element={<ExplorePage />} />
          <Route
            path="/login"
            element={
              <PublicRoute>
                <LoginPage />
              </PublicRoute>
            }
          />
          <Route
            path="/signup"
            element={
              <PublicRoute>
                <SignupPage />
              </PublicRoute>
            }
          />
          <Route
            path="/owner/login"
            element={
              <PublicRoute>
                <PlaceholderPage
                  title="Owner Login"
                  description="Phase 0 route placeholder for owner login."
                />
              </PublicRoute>
            }
          />
          <Route
            path="/owner/signup"
            element={
              <PublicRoute>
                <PlaceholderPage
                  title="Owner Signup"
                  description="Phase 0 route placeholder for owner signup."
                />
              </PublicRoute>
            }
          />
          <Route
            path="/restaurant/:id"
            element={
              <PlaceholderPage
                title="Restaurant Details"
                description="Phase 0 route placeholder for public restaurant details."
              />
            }
          />
          <Route
            path="/profile"
            element={
              <ProtectedRoute>
                <ProfilePage />
              </ProtectedRoute>
            }
          />
          <Route
            path="/preferences"
            element={
              <ProtectedRoute>
                <PreferencesPage />
              </ProtectedRoute>
            }
          />
          <Route
            path="/add-restaurant"
            element={
              <ProtectedRoute>
                <PlaceholderPage
                  title="Add Restaurant"
                  description="Phase 0 route placeholder for protected add-restaurant page."
                />
              </ProtectedRoute>
            }
          />
          <Route path="*" element={<Navigate to="/" replace />} />
        </Routes>
      </main>
    </div>
  );
}
