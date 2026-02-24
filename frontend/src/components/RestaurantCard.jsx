import FavoriteButton from "./FavoriteButton";

function StarRating({ rating }) {
  const stars = Math.round(rating);
  return (
    <span className="star-rating" aria-label={`${rating} out of 5`}>
      {[1, 2, 3, 4, 5].map((i) => (
        <span key={i} className={i <= stars ? "star filled" : "star"}>★</span>
      ))}
    </span>
  );
}

/**
 * Shared restaurant card used on ExplorePage, DashboardPage (favorites + history).
 * Props:
 *   restaurant  — RestaurantCard shape from backend
 *   onClick     — navigate to detail page
 *   showFav     — whether to show the favorite button (default true)
 */
export default function RestaurantCard({ restaurant, onClick, showFav = true }) {
  const amenityList = Array.isArray(restaurant.amenities)
    ? restaurant.amenities.slice(0, 3)
    : [];

  return (
    <article
      className="restaurant-card"
      onClick={onClick}
      tabIndex={0}
      onKeyDown={(e) => e.key === "Enter" && onClick()}
      role="button"
      aria-label={`View details for ${restaurant.name}`}
    >
      <div className="rc-photo">
        {restaurant.cover_photo_url ? (
          <img src={restaurant.cover_photo_url} alt={restaurant.name} />
        ) : (
          <div className="rc-photo-placeholder">
            <span>🍴</span>
          </div>
        )}
        {restaurant.pricing_tier && (
          <span className="rc-badge">{restaurant.pricing_tier}</span>
        )}
        {showFav && (
          <FavoriteButton restaurantId={restaurant.id} className="rc-fav-btn" />
        )}
      </div>
      <div className="rc-body">
        <h3 className="rc-name">{restaurant.name}</h3>
        <p className="rc-meta">
          {restaurant.cuisine_type && (
            <span className="rc-cuisine">{restaurant.cuisine_type}</span>
          )}
          <span className="rc-location">
            {restaurant.city}{restaurant.state ? `, ${restaurant.state}` : ""}
          </span>
        </p>
        {restaurant.average_rating > 0 ? (
          <div className="rc-rating">
            <StarRating rating={restaurant.average_rating} />
            <span className="rc-review-count">({restaurant.review_count})</span>
          </div>
        ) : (
          <p className="rc-no-reviews">No reviews yet</p>
        )}
        {restaurant.description && (
          <p className="rc-description">
            {restaurant.description.slice(0, 100)}
            {restaurant.description.length > 100 ? "…" : ""}
          </p>
        )}
        {amenityList.length > 0 && (
          <div className="rc-amenities">
            {amenityList.map((a) => (
              <span key={a} className="rc-amenity-tag">{a}</span>
            ))}
          </div>
        )}
      </div>
    </article>
  );
}
