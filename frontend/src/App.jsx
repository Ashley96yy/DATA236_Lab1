import { Navigate, Route, Routes, useLocation } from "react-router-dom";

import OwnerProtectedRoute from "./components/OwnerProtectedRoute";
import ProtectedRoute from "./components/ProtectedRoute";
import PublicRoute from "./components/PublicRoute";
import AIChatWidget from "./components/AIChatWidget";
import TopNav from "./components/TopNav";
import { useAuth } from "./contexts/AuthContext";
import { FavoritesProvider } from "./contexts/FavoritesContext";
import { OwnerAuthProvider } from "./contexts/OwnerAuthContext";
import AddRestaurantPage from "./pages/AddRestaurantPage";
import DashboardPage from "./pages/DashboardPage";
import ExplorePage from "./pages/ExplorePage";
import LoginPage from "./pages/LoginPage";
import OwnerDashboardPage from "./pages/OwnerDashboardPage";
import OwnerLoginPage from "./pages/OwnerLoginPage";
import OwnerProfilePage from "./pages/OwnerProfilePage";
import OwnerRestaurantEditPage from "./pages/OwnerRestaurantEditPage";
import OwnerRestaurantReviewsPage from "./pages/OwnerRestaurantReviewsPage";
import OwnerRestaurantsPage from "./pages/OwnerRestaurantsPage";
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
    <OwnerAuthProvider>
      <FavoritesProvider>
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

              {/* ── User Protected ── */}
              <Route
                path="/add-restaurant"
                element={<ProtectedRoute><AddRestaurantPage /></ProtectedRoute>}
              />
              <Route
                path="/dashboard"
                element={<ProtectedRoute><DashboardPage /></ProtectedRoute>}
              />
              <Route
                path="/profile"
                element={<ProtectedRoute><ProfilePage /></ProtectedRoute>}
              />
              <Route
                path="/preferences"
                element={<ProtectedRoute><PreferencesPage /></ProtectedRoute>}
              />

              {/* ── Owner Protected ── */}
              <Route
                path="/owner/dashboard"
                element={<OwnerProtectedRoute><OwnerDashboardPage /></OwnerProtectedRoute>}
              />
              <Route
                path="/owner/profile"
                element={<OwnerProtectedRoute><OwnerProfilePage /></OwnerProtectedRoute>}
              />
              <Route
                path="/owner/restaurants"
                element={<OwnerProtectedRoute><OwnerRestaurantsPage /></OwnerProtectedRoute>}
              />
              <Route
                path="/owner/restaurants/:id/edit"
                element={<OwnerProtectedRoute><OwnerRestaurantEditPage /></OwnerProtectedRoute>}
              />
              <Route
                path="/owner/restaurants/:id/reviews"
                element={<OwnerProtectedRoute><OwnerRestaurantReviewsPage /></OwnerProtectedRoute>}
              />

              {/* ── Fallback ── */}
              <Route path="*" element={<Navigate to="/" replace />} />
            </Routes>
          </main>
          {!isAuthRoute ? <AIChatWidget /> : null}
        </div>
      </FavoritesProvider>
    </OwnerAuthProvider>
  );
}
