-- Lab1 Yelp MVP quick check queries
-- Run after:
--   db/001_init_schema.sql
--   db/002_seed_sample_data.sql

USE yelp_lab1;

-- 1) Row counts by table
SELECT 'users' AS table_name, COUNT(*) AS row_count FROM users
UNION ALL
SELECT 'user_preferences', COUNT(*) FROM user_preferences
UNION ALL
SELECT 'restaurants', COUNT(*) FROM restaurants
UNION ALL
SELECT 'reviews', COUNT(*) FROM reviews
UNION ALL
SELECT 'favorites', COUNT(*) FROM favorites
UNION ALL
SELECT 'user_history', COUNT(*) FROM user_history;

-- 2) Seed users and basic profile fields
SELECT
  id,
  name,
  email,
  city,
  country,
  JSON_LENGTH(languages) AS language_count
FROM users
WHERE email IN ('alice@example.com', 'bob@example.com')
ORDER BY email;

-- 3) Preferences linked correctly
SELECT
  u.email,
  up.price_range,
  up.sort_preference,
  JSON_LENGTH(up.cuisines) AS cuisine_count,
  JSON_LENGTH(up.dietary_needs) AS dietary_count
FROM user_preferences up
JOIN users u ON u.id = up.user_id
ORDER BY u.email;

-- 4) Restaurant list with derived rating metrics
SELECT
  r.id,
  r.name,
  r.city,
  r.cuisine_type,
  r.price_tier,
  ROUND(AVG(rv.rating), 2) AS avg_rating,
  COUNT(rv.id) AS review_count
FROM restaurants r
LEFT JOIN reviews rv ON rv.restaurant_id = r.id
GROUP BY r.id, r.name, r.city, r.cuisine_type, r.price_tier
ORDER BY r.name;

-- 5) Review ownership + restaurant mapping
SELECT
  rv.id AS review_id,
  u.email AS reviewer_email,
  r.name AS restaurant_name,
  rv.rating,
  rv.comment,
  rv.created_at
FROM reviews rv
JOIN users u ON u.id = rv.user_id
JOIN restaurants r ON r.id = rv.restaurant_id
ORDER BY rv.id;

-- 6) Favorites mapping
SELECT
  u.email,
  r.name AS favorite_restaurant,
  f.created_at
FROM favorites f
JOIN users u ON u.id = f.user_id
JOIN restaurants r ON r.id = f.restaurant_id
ORDER BY u.email, r.name;

-- 7) User history timeline
SELECT
  u.email,
  uh.action,
  r.name AS restaurant_name,
  uh.metadata,
  uh.created_at
FROM user_history uh
JOIN users u ON u.id = uh.user_id
LEFT JOIN restaurants r ON r.id = uh.restaurant_id
ORDER BY uh.created_at DESC, uh.id DESC;

-- 8) Optional: quick auth lookup check for login path
-- (API should verify password hash in application code.)
SELECT
  id,
  email,
  password_hash
FROM users
WHERE email = 'alice@example.com';
