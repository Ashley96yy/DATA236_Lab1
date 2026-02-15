-- Lab1 Yelp MVP schema
-- MySQL 8.0+

CREATE DATABASE IF NOT EXISTS yelp_lab1
  CHARACTER SET utf8mb4
  COLLATE utf8mb4_unicode_ci;

USE yelp_lab1;

CREATE TABLE IF NOT EXISTS users (
  id BIGINT UNSIGNED NOT NULL AUTO_INCREMENT,
  name VARCHAR(100) NOT NULL,
  email VARCHAR(255) NOT NULL,
  password_hash VARCHAR(255) NOT NULL,
  phone VARCHAR(30) NULL,
  about_me TEXT NULL,
  city VARCHAR(100) NULL,
  country CHAR(2) NULL,
  languages JSON NULL,
  gender ENUM('male', 'female', 'non_binary', 'other', 'prefer_not_to_say') NULL,
  avatar_url VARCHAR(500) NULL,
  created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
  updated_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
  PRIMARY KEY (id),
  UNIQUE KEY uk_users_email (email)
);

CREATE TABLE IF NOT EXISTS user_preferences (
  id BIGINT UNSIGNED NOT NULL AUTO_INCREMENT,
  user_id BIGINT UNSIGNED NOT NULL,
  cuisines JSON NULL,
  price_range ENUM('$', '$$', '$$$', '$$$$') NULL,
  preferred_locations JSON NULL,
  search_radius_km INT UNSIGNED NULL,
  dietary_needs JSON NULL,
  ambiance JSON NULL,
  sort_preference ENUM('rating', 'distance', 'popularity', 'price') NOT NULL DEFAULT 'rating',
  updated_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
  PRIMARY KEY (id),
  UNIQUE KEY uk_user_preferences_user_id (user_id),
  CONSTRAINT fk_user_preferences_user
    FOREIGN KEY (user_id) REFERENCES users(id)
    ON DELETE CASCADE
);

CREATE TABLE IF NOT EXISTS restaurants (
  id BIGINT UNSIGNED NOT NULL AUTO_INCREMENT,
  created_by_user_id BIGINT UNSIGNED NULL,
  name VARCHAR(200) NOT NULL,
  cuisine_type VARCHAR(100) NOT NULL,
  address VARCHAR(255) NOT NULL,
  city VARCHAR(100) NOT NULL,
  zip_code VARCHAR(20) NULL,
  description TEXT NULL,
  contact_info VARCHAR(120) NULL,
  hours VARCHAR(120) NULL,
  price_tier ENUM('$', '$$', '$$$', '$$$$') NULL,
  created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
  updated_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
  PRIMARY KEY (id),
  KEY idx_restaurants_name (name),
  KEY idx_restaurants_city (city),
  KEY idx_restaurants_cuisine (cuisine_type),
  KEY idx_restaurants_city_cuisine (city, cuisine_type),
  CONSTRAINT fk_restaurants_created_by_user
    FOREIGN KEY (created_by_user_id) REFERENCES users(id)
    ON DELETE SET NULL
);

CREATE TABLE IF NOT EXISTS reviews (
  id BIGINT UNSIGNED NOT NULL AUTO_INCREMENT,
  restaurant_id BIGINT UNSIGNED NOT NULL,
  user_id BIGINT UNSIGNED NOT NULL,
  rating TINYINT UNSIGNED NOT NULL,
  comment TEXT NOT NULL,
  photo_url VARCHAR(500) NULL,
  created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
  updated_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
  PRIMARY KEY (id),
  UNIQUE KEY uk_reviews_user_restaurant (user_id, restaurant_id),
  KEY idx_reviews_restaurant_id (restaurant_id),
  KEY idx_reviews_user_id (user_id),
  CONSTRAINT chk_reviews_rating CHECK (rating BETWEEN 1 AND 5),
  CONSTRAINT fk_reviews_restaurant
    FOREIGN KEY (restaurant_id) REFERENCES restaurants(id)
    ON DELETE CASCADE,
  CONSTRAINT fk_reviews_user
    FOREIGN KEY (user_id) REFERENCES users(id)
    ON DELETE CASCADE
);

CREATE TABLE IF NOT EXISTS favorites (
  id BIGINT UNSIGNED NOT NULL AUTO_INCREMENT,
  user_id BIGINT UNSIGNED NOT NULL,
  restaurant_id BIGINT UNSIGNED NOT NULL,
  created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
  PRIMARY KEY (id),
  UNIQUE KEY uk_favorites_user_restaurant (user_id, restaurant_id),
  KEY idx_favorites_user_id (user_id),
  KEY idx_favorites_restaurant_id (restaurant_id),
  CONSTRAINT fk_favorites_user
    FOREIGN KEY (user_id) REFERENCES users(id)
    ON DELETE CASCADE,
  CONSTRAINT fk_favorites_restaurant
    FOREIGN KEY (restaurant_id) REFERENCES restaurants(id)
    ON DELETE CASCADE
);

CREATE TABLE IF NOT EXISTS user_history (
  id BIGINT UNSIGNED NOT NULL AUTO_INCREMENT,
  user_id BIGINT UNSIGNED NOT NULL,
  restaurant_id BIGINT UNSIGNED NULL,
  action ENUM('viewed', 'reviewed', 'favorited', 'added_restaurant', 'searched') NOT NULL,
  metadata JSON NULL,
  created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
  PRIMARY KEY (id),
  KEY idx_user_history_user_created (user_id, created_at),
  KEY idx_user_history_restaurant_id (restaurant_id),
  CONSTRAINT fk_user_history_user
    FOREIGN KEY (user_id) REFERENCES users(id)
    ON DELETE CASCADE,
  CONSTRAINT fk_user_history_restaurant
    FOREIGN KEY (restaurant_id) REFERENCES restaurants(id)
    ON DELETE SET NULL
);
