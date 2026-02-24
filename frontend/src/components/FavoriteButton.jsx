import { useNavigate } from "react-router-dom";

import { useAuth } from "../contexts/AuthContext";
import { useFavorites } from "../contexts/FavoritesContext";

/**
 * Heart toggle button.
 * - Visible only to authenticated users.
 * - Unauthenticated click → redirect to /login.
 * - e.stopPropagation() so clicking the heart doesn't trigger the card click.
 *
 * Props:
 *   restaurantId  — number
 *   className     — extra CSS class (e.g. "rc-fav-btn" for card overlay,
 *                   "detail-fav-btn" for detail hero)
 */
export default function FavoriteButton({ restaurantId, className = "" }) {
  const { isAuthenticated } = useAuth();
  const { isFavorited, toggle } = useFavorites();
  const navigate = useNavigate();

  function handleClick(e) {
    e.stopPropagation();
    e.preventDefault();
    if (!isAuthenticated) {
      navigate("/login");
      return;
    }
    toggle(restaurantId);
  }

  const favorited = isAuthenticated && isFavorited(restaurantId);

  return (
    <button
      type="button"
      className={`fav-btn ${favorited ? "fav-btn--active" : ""} ${className}`}
      onClick={handleClick}
      aria-label={favorited ? "Remove from favorites" : "Add to favorites"}
      title={favorited ? "Remove from favorites" : "Add to favorites"}
    >
      {favorited ? "❤️" : "🤍"}
    </button>
  );
}
