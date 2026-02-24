import { Navigate, Route, Routes, useLocation } from "react-router-dom";

import ProtectedRoute from "./components/ProtectedRoute";
import PublicRoute from "./components/PublicRoute";
import TopNav from "./components/TopNav";
import { useAuth } from "./contexts/AuthContext";
import AddRestaurantPage from "./pages/AddRestaurantPage";
import ExplorePage from "./pages/ExplorePage";
import LoginPage from "./pages/LoginPage";
import OwnerLoginPage from "./pages/OwnerLoginPage";
import OwnerSignupPage from "./pages/OwnerSignupPage";
import PreferencesPage from "./pages/PreferencesPage";
import ProfilePage from "./pages/ProfilePage";
import RestaurantDetailPage from "./pages/RestaurantDetailPage";
import SignupPage from "./pages/SignupPage";

export default function App() {
  const location = useLocation();
  const { isAuthReady } = useAuth();

  const isAuthRoute =
    location.pathname === "/login" ||
    location.pathname === "/signup" ||
    location.pathname === "/owner/login" ||
    location.pathname === "/owner/signup";

  if (!isAuthReady) {
    return <div className="page-status">Loading…</div>;
  }

  return (
    <div className="app-shell">
      {!isAuthRoute ? <TopNav /> : null}
      <main className={isAuthRoute ? "page-plain" : "page-wrap"}>
        <Routes>
          {/* ── Public ── */}
          <Route path="/" element={<ExplorePage />} />
          <Route path="/restaurant/:id" element={<RestaurantDetailPage />} />

          {/* ── Auth (public only) ── */}
          <Route
            path="/login"
            element={<PublicRoute><LoginPage /></PublicRoute>}
          />
          <Route
            path="/signup"
            element={<PublicRoute><SignupPage /></PublicRoute>}
          />
          <Route
            path="/owner/login"
            element={<PublicRoute><OwnerLoginPage /></PublicRoute>}
          />
          <Route
            path="/owner/signup"
            element={<PublicRoute><OwnerSignupPage /></PublicRoute>}
          />

          {/* ── Protected ── */}
          <Route
            path="/add-restaurant"
            element={<ProtectedRoute><AddRestaurantPage /></ProtectedRoute>}
          />
          <Route
            path="/profile"
            element={<ProtectedRoute><ProfilePage /></ProtectedRoute>}
          />
          <Route
            path="/preferences"
            element={<ProtectedRoute><PreferencesPage /></ProtectedRoute>}
          />

          {/* ── Fallback ── */}
          <Route path="*" element={<Navigate to="/" replace />} />
        </Routes>
      </main>
    </div>
  );
}
