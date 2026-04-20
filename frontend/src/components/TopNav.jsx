import { Link, useNavigate } from "react-router-dom";

import ProjectLogo from "./ProjectLogo";
import { useAuth } from "../contexts/AuthContext";
import { useOwnerAuth } from "../contexts/OwnerAuthContext";

export default function TopNav() {
  const navigate = useNavigate();
  const { user, logout, isAuthenticated } = useAuth();
  const { owner, ownerLogout, isOwnerAuthenticated } = useOwnerAuth();

  const handleLogout = () => {
    logout();
    navigate("/login", { replace: true });
  };

  const handleOwnerLogout = () => {
    ownerLogout();
    navigate("/owner/login", { replace: true });
  };

  return (
    <header className="top-nav">
      <div className="top-nav-inner">
        <ProjectLogo to="/" compact />

        <nav className="top-links">
          {!isOwnerAuthenticated && <Link to="/">Explore</Link>}

          {/* User links */}
          {isAuthenticated && (
            <>
              <Link to="/dashboard">Dashboard</Link>
              <Link to="/profile">Profile</Link>
              <Link to="/preferences">Preferences</Link>
            </>
          )}

          {/* Owner links */}
          {isOwnerAuthenticated && (
            <>
              <Link to="/owner/dashboard">Owner Dashboard</Link>
              <Link to="/owner/restaurants">My Restaurants</Link>
              <Link to="/owner/restaurants/new">Post Restaurant</Link>
              <Link to="/owner/profile">Owner Profile</Link>
            </>
          )}

          {/* Guest links */}
          {!isAuthenticated && !isOwnerAuthenticated && (
            <>
              <Link to="/login">User Login</Link>
              <Link to="/signup">Sign Up</Link>
              <Link to="/owner/login">Owner Login</Link>
            </>
          )}
        </nav>

        <div className="nav-user-group">
          {isAuthenticated && (
            <div className="nav-user">
              <Link to="/profile" className="nav-avatar-link" title="My Profile">
                {user?.avatar_url ? (
                  <img src={user.avatar_url} alt="Profile" className="nav-avatar-img" />
                ) : (
                  <div className="nav-avatar-placeholder">
                    {user?.name?.charAt(0).toUpperCase() || "U"}
                  </div>
                )}
              </Link>
              <span className="nav-user-name">{user?.name || "User"}</span>
              <button type="button" className="btn-logout" onClick={handleLogout}>
                Logout
              </button>
            </div>
          )}
          {isOwnerAuthenticated && (
            <div className="nav-user nav-user--owner">
              <span className="nav-user-name">{owner?.name || "Owner"}</span>
              <button type="button" className="btn-logout" onClick={handleOwnerLogout}>
                Logout
              </button>
            </div>
          )}
        </div>
      </div>
    </header>
  );
}
