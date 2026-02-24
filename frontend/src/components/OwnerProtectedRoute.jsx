import { Navigate } from "react-router-dom";

import { useOwnerAuth } from "../contexts/OwnerAuthContext";

export default function OwnerProtectedRoute({ children }) {
  const { isOwnerAuthenticated, isOwnerAuthReady } = useOwnerAuth();

  if (!isOwnerAuthReady) {
    return <div className="page-status">Checking owner session...</div>;
  }

  if (!isOwnerAuthenticated) {
    return <Navigate to="/owner/login" replace />;
  }

  return children;
}
