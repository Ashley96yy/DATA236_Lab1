-- Lab1 Yelp MVP seed data
-- Execute after: db/001_init_schema.sql
-- Note: password_hash values below are bcrypt hashes.
-- Demo plaintext:
--   alice@example.com -> Passw0rd!
--   bob@example.com   -> Passw0rd!

USE yelp_lab1;

START TRANSACTION;

-- 1) Users
INSERT INTO users (
  name,
  email,
  password_hash,
  phone,
  about_me,
  city,
  country,
  languages,
  gender,
  avatar_url
)
SELECT
  'Alice Chen',
  'alice@example.com',
  '$2b$12$bdnJludA3g.NCQNUNGSy4.DYU6jbC9CiWmcoKVjQAu35YpOEIgIie',
  '4081234567',
  'Love trying new restaurants',
  'San Jose',
  'US',
  JSON_ARRAY('English', 'Chinese'),
  'female',
  'https://example.com/avatar-alice.jpg'
WHERE NOT EXISTS (
  SELECT 1 FROM users WHERE email = 'alice@example.com'
);

INSERT INTO users (
  name,
  email,
  password_hash,
  phone,
  about_me,
  city,
  country,
  languages,
  gender,
  avatar_url
)
SELECT
  'Bob Lee',
  'bob@example.com',
  '$2b$12$bdnJludA3g.NCQNUNGSy4.DYU6jbC9CiWmcoKVjQAu35YpOEIgIie',
  '6691234567',
  'Weekend foodie',
  'Santa Clara',
  'US',
  JSON_ARRAY('English'),
  'male',
  'https://example.com/avatar-bob.jpg'
WHERE NOT EXISTS (
  SELECT 1 FROM users WHERE email = 'bob@example.com'
);

SET @alice_id = (SELECT id FROM users WHERE email = 'alice@example.com' LIMIT 1);
SET @bob_id = (SELECT id FROM users WHERE email = 'bob@example.com' LIMIT 1);

-- 2) Preferences
INSERT INTO user_preferences (
  user_id,
  cuisines,
  price_range,
  preferred_locations,
  search_radius_km,
  dietary_needs,
  ambiance,
  sort_preference
)
SELECT
  @alice_id,
  JSON_ARRAY('Italian', 'Japanese'),
  '$$',
  JSON_ARRAY('San Jose', 'Santa Clara'),
  10,
  JSON_ARRAY('vegetarian'),
  JSON_ARRAY('casual', 'romantic'),
  'rating'
WHERE @alice_id IS NOT NULL
  AND NOT EXISTS (SELECT 1 FROM user_preferences WHERE user_id = @alice_id);

INSERT INTO user_preferences (
  user_id,
  cuisines,
  price_range,
  preferred_locations,
  search_radius_km,
  dietary_needs,
  ambiance,
  sort_preference
)
SELECT
  @bob_id,
  JSON_ARRAY('American', 'Mexican'),
  '$$$',
  JSON_ARRAY('Santa Clara', 'Sunnyvale'),
  15,
  JSON_ARRAY('halal'),
  JSON_ARRAY('family-friendly'),
  'popularity'
WHERE @bob_id IS NOT NULL
  AND NOT EXISTS (SELECT 1 FROM user_preferences WHERE user_id = @bob_id);

-- 3) Restaurants
INSERT INTO restaurants (
  created_by_user_id,
  name,
  cuisine_type,
  address,
  city,
  zip_code,
  description,
  contact_info,
  hours,
  price_tier
)
SELECT
  @alice_id,
  'Pasta Paradise',
  'Italian',
  '123 Main St',
  'San Jose',
  '95112',
  'Fresh handmade pasta and cozy atmosphere',
  '408-555-0101',
  '10:00-22:00',
  '$$'
WHERE NOT EXISTS (
  SELECT 1 FROM restaurants WHERE name = 'Pasta Paradise' AND city = 'San Jose'
);

INSERT INTO restaurants (
  created_by_user_id,
  name,
  cuisine_type,
  address,
  city,
  zip_code,
  description,
  contact_info,
  hours,
  price_tier
)
SELECT
  @bob_id,
  'Green Leaf Cafe',
  'Vegan',
  '88 Park Ave',
  'Santa Clara',
  '95050',
  'Plant-based menu with casual seating',
  '408-555-0202',
  '09:00-21:00',
  '$'
WHERE NOT EXISTS (
  SELECT 1 FROM restaurants WHERE name = 'Green Leaf Cafe' AND city = 'Santa Clara'
);

INSERT INTO restaurants (
  created_by_user_id,
  name,
  cuisine_type,
  address,
  city,
  zip_code,
  description,
  contact_info,
  hours,
  price_tier
)
SELECT
  @alice_id,
  'Sunset Terrace',
  'French',
  '456 Ocean Dr',
  'San Jose',
  '95113',
  'Upscale dinner with romantic ambiance',
  '408-555-0303',
  '17:00-23:00',
  '$$$'
WHERE NOT EXISTS (
  SELECT 1 FROM restaurants WHERE name = 'Sunset Terrace' AND city = 'San Jose'
);

SET @pasta_id = (
  SELECT id FROM restaurants
  WHERE name = 'Pasta Paradise' AND city = 'San Jose'
  LIMIT 1
);
SET @green_id = (
  SELECT id FROM restaurants
  WHERE name = 'Green Leaf Cafe' AND city = 'Santa Clara'
  LIMIT 1
);
SET @sunset_id = (
  SELECT id FROM restaurants
  WHERE name = 'Sunset Terrace' AND city = 'San Jose'
  LIMIT 1
);

-- 4) Reviews (one review per user per restaurant due to unique constraint)
INSERT INTO reviews (restaurant_id, user_id, rating, comment, photo_url)
SELECT
  @pasta_id,
  @alice_id,
  5,
  'Excellent pasta and friendly service.',
  NULL
WHERE @pasta_id IS NOT NULL
  AND @alice_id IS NOT NULL
  AND NOT EXISTS (
    SELECT 1 FROM reviews WHERE restaurant_id = @pasta_id AND user_id = @alice_id
  );

INSERT INTO reviews (restaurant_id, user_id, rating, comment, photo_url)
SELECT
  @green_id,
  @alice_id,
  4,
  'Great vegan options and relaxed vibe.',
  NULL
WHERE @green_id IS NOT NULL
  AND @alice_id IS NOT NULL
  AND NOT EXISTS (
    SELECT 1 FROM reviews WHERE restaurant_id = @green_id AND user_id = @alice_id
  );

INSERT INTO reviews (restaurant_id, user_id, rating, comment, photo_url)
SELECT
  @sunset_id,
  @bob_id,
  5,
  'Perfect place for special occasions.',
  NULL
WHERE @sunset_id IS NOT NULL
  AND @bob_id IS NOT NULL
  AND NOT EXISTS (
    SELECT 1 FROM reviews WHERE restaurant_id = @sunset_id AND user_id = @bob_id
  );

-- 5) Favorites
INSERT INTO favorites (user_id, restaurant_id)
SELECT @alice_id, @sunset_id
WHERE @alice_id IS NOT NULL
  AND @sunset_id IS NOT NULL
  AND NOT EXISTS (
    SELECT 1 FROM favorites WHERE user_id = @alice_id AND restaurant_id = @sunset_id
  );

INSERT INTO favorites (user_id, restaurant_id)
SELECT @bob_id, @pasta_id
WHERE @bob_id IS NOT NULL
  AND @pasta_id IS NOT NULL
  AND NOT EXISTS (
    SELECT 1 FROM favorites WHERE user_id = @bob_id AND restaurant_id = @pasta_id
  );

-- 6) User history
INSERT INTO user_history (user_id, restaurant_id, action, metadata)
SELECT
  @alice_id,
  @pasta_id,
  'reviewed',
  JSON_OBJECT('rating', 5, 'source', 'seed')
WHERE @alice_id IS NOT NULL
  AND @pasta_id IS NOT NULL
  AND NOT EXISTS (
    SELECT 1 FROM user_history
    WHERE user_id = @alice_id
      AND restaurant_id = @pasta_id
      AND action = 'reviewed'
  );

INSERT INTO user_history (user_id, restaurant_id, action, metadata)
SELECT
  @alice_id,
  @sunset_id,
  'favorited',
  JSON_OBJECT('source', 'seed')
WHERE @alice_id IS NOT NULL
  AND @sunset_id IS NOT NULL
  AND NOT EXISTS (
    SELECT 1 FROM user_history
    WHERE user_id = @alice_id
      AND restaurant_id = @sunset_id
      AND action = 'favorited'
  );

INSERT INTO user_history (user_id, restaurant_id, action, metadata)
SELECT
  @bob_id,
  @sunset_id,
  'reviewed',
  JSON_OBJECT('rating', 5, 'source', 'seed')
WHERE @bob_id IS NOT NULL
  AND @sunset_id IS NOT NULL
  AND NOT EXISTS (
    SELECT 1 FROM user_history
    WHERE user_id = @bob_id
      AND restaurant_id = @sunset_id
      AND action = 'reviewed'
  );

COMMIT;
