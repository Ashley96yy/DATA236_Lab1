import { Link } from "react-router-dom";

export default function ProjectLogo({ to = "/", compact = false }) {
  return (
    <Link to={to} className={`project-logo${compact ? " compact" : ""}`} aria-label="Dine Finder home">
      <img src="/app_logo.png" alt="Dine Finder logo" className="project-logo-image" />
    </Link>
  );
}
