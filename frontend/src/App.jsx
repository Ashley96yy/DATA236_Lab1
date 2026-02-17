import { Navigate, Route, Routes, useLocation } from "react-router-dom";

import ProtectedRoute from "./components/ProtectedRoute";
import PublicRoute from "./components/PublicRoute";
import TopNav from "./components/TopNav";
import { useAuth } from "./contexts/AuthContext";
import LoginPage from "./pages/LoginPage";
import PreferencesPage from "./pages/PreferencesPage";
import ProfilePage from "./pages/ProfilePage";
import SignupPage from "./pages/SignupPage";

function HomeRedirect() {
  const { isAuthReady, isAuthenticated } = useAuth();

  if (!isAuthReady) {
    return <div className="page-status">Loading...</div>;
  }
  return <Navigate to={isAuthenticated ? "/profile" : "/login"} replace />;
}

export default function App() {
  const location = useLocation();
  const { isAuthenticated } = useAuth();
  const isAuthRoute = location.pathname === "/login" || location.pathname === "/signup";

  return (
    <div className="app-shell">
      {isAuthenticated ? <TopNav /> : null}
      <main className={isAuthRoute ? "page-plain" : "page-wrap"}>
        <Routes>
          <Route path="/" element={<HomeRedirect />} />
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
          <Route path="*" element={<Navigate to="/" replace />} />
        </Routes>
      </main>
    </div>
  );
}
