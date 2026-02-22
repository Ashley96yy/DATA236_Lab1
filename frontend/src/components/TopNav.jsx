import { Link, useNavigate } from "react-router-dom";

import ProjectLogo from "./ProjectLogo";
import { useAuth } from "../contexts/AuthContext";

export default function TopNav() {
  const navigate = useNavigate();
  const { user, logout, isAuthenticated } = useAuth();

  const handleLogout = () => {
    logout();
    navigate("/login", { replace: true });
  };

  return (
    <header className="top-nav">
      <div className="top-nav-inner">
        <ProjectLogo to="/" compact />
        <nav className="top-links">
          <Link to="/">Explore</Link>
          {!isAuthenticated ? <Link to="/login">Login</Link> : null}
          {!isAuthenticated ? <Link to="/signup">Signup</Link> : null}
          {isAuthenticated ? <Link to="/profile">Profile</Link> : null}
          {isAuthenticated ? <Link to="/preferences">Preferences</Link> : null}
        </nav>
        {isAuthenticated ? (
          <div className="nav-user">
            <span>{user?.name || "User"}</span>
            <button type="button" onClick={handleLogout}>
              Logout
            </button>
          </div>
        ) : null}
      </div>
    </header>
  );
}
