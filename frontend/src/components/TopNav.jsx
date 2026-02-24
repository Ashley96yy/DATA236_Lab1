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
          <Link to="/">Explore</Link>

          {/* User links */}
          {isAuthenticated && <Link to="/add-restaurant">+ Add Restaurant</Link>}
          {isAuthenticated && <Link to="/dashboard">Dashboard</Link>}
          {isAuthenticated && <Link to="/profile">Profile</Link>}
          {isAuthenticated && <Link to="/preferences">Preferences</Link>}

          {/* Owner links */}
          {isOwnerAuthenticated && <span className="nav-divider">|</span>}
          {isOwnerAuthenticated && <Link to="/owner/dashboard">Owner Dashboard</Link>}
          {isOwnerAuthenticated && <Link to="/owner/restaurants">My Restaurants</Link>}
          {isOwnerAuthenticated && <Link to="/owner/profile">Owner Profile</Link>}

          {/* Guest links */}
          {!isAuthenticated && !isOwnerAuthenticated && <Link to="/login">Login</Link>}
          {!isAuthenticated && !isOwnerAuthenticated && <Link to="/signup">Sign Up</Link>}
          {!isOwnerAuthenticated && <Link to="/owner/login">Owner Login</Link>}
        </nav>

        <div className="nav-user-group">
          {isAuthenticated && (
            <div className="nav-user">
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
                Owner Logout
              </button>
            </div>
          )}
        </div>
      </div>
    </header>
  );
}
