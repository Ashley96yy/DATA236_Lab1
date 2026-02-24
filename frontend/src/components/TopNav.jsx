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
          {isAuthenticated && <Link to="/add-restaurant">+ Add Restaurant</Link>}
          {!isAuthenticated && <Link to="/login">Login</Link>}
          {!isAuthenticated && <Link to="/signup">Sign Up</Link>}
          {!isAuthenticated && <Link to="/owner/login">Owner Login</Link>}
          {isAuthenticated && <Link to="/profile">Profile</Link>}
          {isAuthenticated && <Link to="/preferences">Preferences</Link>}
        </nav>
        {isAuthenticated && (
          <div className="nav-user">
            <span className="nav-user-name">{user?.name || "User"}</span>
            <button type="button" className="btn-logout" onClick={handleLogout}>
              Logout
            </button>
          </div>
        )}
      </div>
    </header>
  );
}
