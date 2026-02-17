import { Link, useNavigate } from "react-router-dom";

import ProjectLogo from "./ProjectLogo";
import { useAuth } from "../contexts/AuthContext";

export default function TopNav() {
  const navigate = useNavigate();
  const { user, logout } = useAuth();

  const handleLogout = () => {
    logout();
    navigate("/login", { replace: true });
  };

  return (
    <header className="top-nav">
      <div className="top-nav-inner">
        <ProjectLogo to="/profile" compact />
        <nav className="top-links">
          <Link to="/profile">Profile</Link>
          <Link to="/preferences">Preferences</Link>
        </nav>
        <div className="nav-user">
          <span>{user?.name || "User"}</span>
          <button type="button" onClick={handleLogout}>
            Logout
          </button>
        </div>
      </div>
    </header>
  );
}
