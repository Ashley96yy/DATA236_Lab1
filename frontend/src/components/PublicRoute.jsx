import { Navigate } from "react-router-dom";

import { useAuth } from "../contexts/AuthContext";

export default function PublicRoute({ children }) {
  const { isAuthenticated, isAuthReady } = useAuth();

  if (!isAuthReady) {
    return <div className="page-status">Checking session...</div>;
  }

  if (isAuthenticated) {
    return <Navigate to="/profile" replace />;
  }

  return children;
}
