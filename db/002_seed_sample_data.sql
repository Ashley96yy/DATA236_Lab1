-- Lab1 Yelp MVP seed data
-- Execute after: db/001_init_schema.sql
-- Note: password_hash values below are bcrypt hashes.
-- Demo plaintext:
--   alice@example.com -> Passw0rd!
--   bob@example.com   -> Passw0rd!
--   charlie@example.com / diana@example.com / ethan@example.com / fiona@example.com
--   all use: Passw0rd!

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
  'Charlie Park',
  'charlie@example.com',
  '$2b$12$bdnJludA3g.NCQNUNGSy4.DYU6jbC9CiWmcoKVjQAu35YpOEIgIie',
  '6501234567',
  'Exploring new spots after work',
  'Sunnyvale',
  'US',
  JSON_ARRAY('English', 'Korean'),
  'male',
  'https://example.com/avatar-charlie.jpg'
WHERE NOT EXISTS (
  SELECT 1 FROM users WHERE email = 'charlie@example.com'
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
  'Diana Wong',
  'diana@example.com',
  '$2b$12$bdnJludA3g.NCQNUNGSy4.DYU6jbC9CiWmcoKVjQAu35YpOEIgIie',
  '5101234567',
  'Weekend brunch and date-night fan',
  'Mountain View',
  'US',
  JSON_ARRAY('English', 'Cantonese'),
  'female',
  'https://example.com/avatar-diana.jpg'
WHERE NOT EXISTS (
  SELECT 1 FROM users WHERE email = 'diana@example.com'
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
  'Ethan Kim',
  'ethan@example.com',
  '$2b$12$bdnJludA3g.NCQNUNGSy4.DYU6jbC9CiWmcoKVjQAu35YpOEIgIie',
  '4087654321',
  'Looking for budget-friendly comfort food',
  'San Jose',
  'US',
  JSON_ARRAY('English'),
  'male',
  'https://example.com/avatar-ethan.jpg'
WHERE NOT EXISTS (
  SELECT 1 FROM users WHERE email = 'ethan@example.com'
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
  'Fiona Garcia',
  'fiona@example.com',
  '$2b$12$bdnJludA3g.NCQNUNGSy4.DYU6jbC9CiWmcoKVjQAu35YpOEIgIie',
  '6697654321',
  'Enjoys seafood and celebration dinners',
  'Palo Alto',
  'US',
  JSON_ARRAY('English', 'Spanish'),
  'female',
  'https://example.com/avatar-fiona.jpg'
WHERE NOT EXISTS (
  SELECT 1 FROM users WHERE email = 'fiona@example.com'
);

SET @alice_id = (SELECT id FROM users WHERE email = 'alice@example.com' LIMIT 1);
SET @bob_id = (SELECT id FROM users WHERE email = 'bob@example.com' LIMIT 1);
SET @charlie_id = (SELECT id FROM users WHERE email = 'charlie@example.com' LIMIT 1);
SET @diana_id = (SELECT id FROM users WHERE email = 'diana@example.com' LIMIT 1);
SET @ethan_id = (SELECT id FROM users WHERE email = 'ethan@example.com' LIMIT 1);
SET @fiona_id = (SELECT id FROM users WHERE email = 'fiona@example.com' LIMIT 1);

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
  @charlie_id,
  JSON_ARRAY('Korean', 'Japanese', 'Vietnamese'),
  '$$',
  JSON_ARRAY('Sunnyvale', 'Santa Clara', 'San Jose'),
  12,
  JSON_ARRAY('dairy-free'),
  JSON_ARRAY('casual', 'trendy'),
  'rating'
WHERE @charlie_id IS NOT NULL
  AND NOT EXISTS (SELECT 1 FROM user_preferences WHERE user_id = @charlie_id);

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
  @diana_id,
  JSON_ARRAY('French', 'Mediterranean', 'Mexican'),
  '$$$',
  JSON_ARRAY('Mountain View', 'Palo Alto'),
  15,
  JSON_ARRAY('vegetarian'),
  JSON_ARRAY('romantic', 'quiet'),
  'rating'
WHERE @diana_id IS NOT NULL
  AND NOT EXISTS (SELECT 1 FROM user_preferences WHERE user_id = @diana_id);

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
  @ethan_id,
  JSON_ARRAY('American', 'Mexican', 'Chinese'),
  '$',
  JSON_ARRAY('San Jose', 'Sunnyvale'),
  20,
  JSON_ARRAY('halal'),
  JSON_ARRAY('family-friendly', 'casual'),
  'popularity'
WHERE @ethan_id IS NOT NULL
  AND NOT EXISTS (SELECT 1 FROM user_preferences WHERE user_id = @ethan_id);

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
  @fiona_id,
  JSON_ARRAY('Seafood', 'Italian', 'Spanish'),
  '$$$',
  JSON_ARRAY('Palo Alto', 'Mountain View', 'San Jose'),
  18,
  JSON_ARRAY('gluten-free'),
  JSON_ARRAY('romantic', 'outdoor'),
  'rating'
WHERE @fiona_id IS NOT NULL
  AND NOT EXISTS (SELECT 1 FROM user_preferences WHERE user_id = @fiona_id);

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

-- 3b) Additional restaurants for AI assistant testing coverage
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
  t.created_by_user_id,
  t.name,
  t.cuisine_type,
  t.address,
  t.city,
  t.zip_code,
  t.description,
  t.contact_info,
  t.hours,
  t.price_tier
FROM (
  SELECT
    @alice_id AS created_by_user_id,
    'Sakura Noodle House' AS name,
    'Japanese' AS cuisine_type,
    '210 Japantown Way' AS address,
    'San Jose' AS city,
    '95112' AS zip_code,
    'Casual ramen bar with izakaya plates and quick service' AS description,
    '408-555-0404' AS contact_info,
    '11:00-23:30' AS hours,
    '$$' AS price_tier
  UNION ALL SELECT
    @bob_id, 'Spice Route Kitchen', 'Indian', '900 El Camino Real', 'Sunnyvale', '94087',
    'Family-friendly curry house with halal-friendly and vegetarian choices',
    '408-555-0505', '11:30-22:00', '$$'
  UNION ALL SELECT
    @charlie_id, 'Tacos Del Sol', 'Mexican', '73 Market St', 'San Jose', '95113',
    'Budget tacos, late-night bites, and vegan-friendly fillings',
    '408-555-0606', '10:00-00:30', '$'
  UNION ALL SELECT
    @fiona_id, 'Ocean Breeze Grill', 'Seafood', '18 Shoreline Blvd', 'Mountain View', '94043',
    'Romantic seafood dining with outdoor patio and sunset views',
    '650-555-0707', '16:30-22:30', '$$$'
  UNION ALL SELECT
    @diana_id, 'Cedar & Olive', 'Mediterranean', '55 Main St', 'Cupertino', '95014',
    'Quiet Mediterranean spot with hummus platters and halal options',
    '408-555-0808', '11:00-21:30', '$$'
  UNION ALL SELECT
    @charlie_id, 'Seoul Garden BBQ', 'Korean', '770 Benton St', 'Santa Clara', '95050',
    'Interactive grill tables, casual groups, and family-friendly portions',
    '408-555-0909', '12:00-22:00', '$$'
  UNION ALL SELECT
    @ethan_id, 'Pho Corner 24', 'Vietnamese', '409 Story Rd', 'San Jose', '95122',
    'Comforting noodle soups, quick lunches, and open-late service',
    '408-555-1010', '10:00-23:59', '$'
  UNION ALL SELECT
    @fiona_id, 'Harvest Table Bistro', 'American', '300 University Ave', 'Palo Alto', '94301',
    'Modern American dinner spot with date-night ambiance and craft desserts',
    '650-555-1111', '17:00-22:00', '$$$'
  UNION ALL SELECT
    @alice_id, 'Napoli Stone Oven', 'Italian', '102 Murphy Ave', 'Sunnyvale', '94086',
    'Wood-fired pizzas, handmade pasta, and a warm casual room',
    '408-555-1212', '11:30-22:30', '$$'
  UNION ALL SELECT
    @diana_id, 'Bombay Curry Club', 'Indian', '4701 Great America Pkwy', 'Santa Clara', '95054',
    'Spicy curries, tandoori grills, and vegetarian platters',
    '408-555-1313', '11:00-22:00', '$$'
  UNION ALL SELECT
    @charlie_id, 'Verde Vida Kitchen', 'Vegan', '212 Castro St', 'Mountain View', '94041',
    'Creative vegan bowls, gluten-free desserts, and bright casual seating',
    '650-555-1414', '09:00-21:00', '$$'
  UNION ALL SELECT
    @ethan_id, 'Golden Wok Express', 'Chinese', '19 De Anza Blvd', 'Cupertino', '95014',
    'Fast stir-fry classics, lunch combos, and budget portions',
    '408-555-1515', '10:30-21:30', '$'
  UNION ALL SELECT
    @fiona_id, 'Luna Tapas Lounge', 'Spanish', '480 Santana Row', 'San Jose', '95128',
    'Romantic tapas lounge with sangria, jazz nights, and cozy lighting',
    '408-555-1616', '17:00-23:30', '$$$'
  UNION ALL SELECT
    @bob_id, 'Morning Bloom Cafe', 'American', '1200 Franklin St', 'Santa Clara', '95050',
    'Brunch cafe with vegetarian options and family-friendly booths',
    '408-555-1717', '07:30-15:00', '$$'
  UNION ALL SELECT
    @alice_id, 'Bay Sushi Lab', 'Japanese', '715 Emerson St', 'Palo Alto', '94301',
    'Premium omakase and creative rolls for special occasions',
    '650-555-1818', '17:00-22:00', '$$$'
  UNION ALL SELECT
    @ethan_id, 'Smoky Trail BBQ', 'American', '899 Wolfe Rd', 'Sunnyvale', '94086',
    'Slow-smoked meats, large platters, and casual weekend crowds',
    '408-555-1919', '11:00-22:00', '$$'
  UNION ALL SELECT
    @diana_id, 'Casa Azul Cantina', 'Mexican', '320 Castro St', 'Mountain View', '94041',
    'Colorful cantina with outdoor seating, margaritas, and date-night vibe',
    '650-555-2020', '12:00-23:00', '$$'
  UNION ALL SELECT
    @fiona_id, 'Quiet Garden Tea House', 'Japanese', '88 Stevens Creek Blvd', 'Cupertino', '95014',
    'Quiet tea pairings, small plates, and minimalist ambiance',
    '408-555-2121', '10:00-20:00', '$$'
) AS t
LEFT JOIN restaurants r
  ON r.name = t.name
  AND r.city = t.city
WHERE r.id IS NULL;

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
SET @sakura_id = (
  SELECT id FROM restaurants
  WHERE name = 'Sakura Noodle House' AND city = 'San Jose'
  LIMIT 1
);
SET @spice_id = (
  SELECT id FROM restaurants
  WHERE name = 'Spice Route Kitchen' AND city = 'Sunnyvale'
  LIMIT 1
);
SET @tacos_id = (
  SELECT id FROM restaurants
  WHERE name = 'Tacos Del Sol' AND city = 'San Jose'
  LIMIT 1
);
SET @ocean_id = (
  SELECT id FROM restaurants
  WHERE name = 'Ocean Breeze Grill' AND city = 'Mountain View'
  LIMIT 1
);
SET @cedar_id = (
  SELECT id FROM restaurants
  WHERE name = 'Cedar & Olive' AND city = 'Cupertino'
  LIMIT 1
);
SET @seoul_id = (
  SELECT id FROM restaurants
  WHERE name = 'Seoul Garden BBQ' AND city = 'Santa Clara'
  LIMIT 1
);
SET @pho_id = (
  SELECT id FROM restaurants
  WHERE name = 'Pho Corner 24' AND city = 'San Jose'
  LIMIT 1
);
SET @harvest_id = (
  SELECT id FROM restaurants
  WHERE name = 'Harvest Table Bistro' AND city = 'Palo Alto'
  LIMIT 1
);
SET @napoli_id = (
  SELECT id FROM restaurants
  WHERE name = 'Napoli Stone Oven' AND city = 'Sunnyvale'
  LIMIT 1
);
SET @bombay_id = (
  SELECT id FROM restaurants
  WHERE name = 'Bombay Curry Club' AND city = 'Santa Clara'
  LIMIT 1
);
SET @verde_id = (
  SELECT id FROM restaurants
  WHERE name = 'Verde Vida Kitchen' AND city = 'Mountain View'
  LIMIT 1
);
SET @golden_id = (
  SELECT id FROM restaurants
  WHERE name = 'Golden Wok Express' AND city = 'Cupertino'
  LIMIT 1
);
SET @luna_id = (
  SELECT id FROM restaurants
  WHERE name = 'Luna Tapas Lounge' AND city = 'San Jose'
  LIMIT 1
);
SET @morning_id = (
  SELECT id FROM restaurants
  WHERE name = 'Morning Bloom Cafe' AND city = 'Santa Clara'
  LIMIT 1
);
SET @sushi_id = (
  SELECT id FROM restaurants
  WHERE name = 'Bay Sushi Lab' AND city = 'Palo Alto'
  LIMIT 1
);
SET @smoky_id = (
  SELECT id FROM restaurants
  WHERE name = 'Smoky Trail BBQ' AND city = 'Sunnyvale'
  LIMIT 1
);
SET @azul_id = (
  SELECT id FROM restaurants
  WHERE name = 'Casa Azul Cantina' AND city = 'Mountain View'
  LIMIT 1
);
SET @quiet_id = (
  SELECT id FROM restaurants
  WHERE name = 'Quiet Garden Tea House' AND city = 'Cupertino'
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

-- More reviews to improve ranking quality for AI recommendations
INSERT INTO reviews (restaurant_id, user_id, rating, comment, photo_url)
SELECT
  t.restaurant_id,
  t.user_id,
  t.rating,
  t.comment,
  t.photo_url
FROM (
  SELECT @sakura_id AS restaurant_id, @alice_id AS user_id, 5 AS rating, 'Rich broth and quick service for weeknight dinner.' AS comment, NULL AS photo_url
  UNION ALL SELECT @sakura_id, @charlie_id, 4, 'Solid ramen and good value for downtown San Jose.', NULL
  UNION ALL SELECT @spice_id, @bob_id, 4, 'Great curries and family portions.', NULL
  UNION ALL SELECT @spice_id, @diana_id, 5, 'Loved the paneer dishes and warm service.', NULL
  UNION ALL SELECT @tacos_id, @charlie_id, 4, 'Good budget tacos with fast turnaround.', 'https://example.com/review-tacos-1.jpg'
  UNION ALL SELECT @tacos_id, @ethan_id, 5, 'Late-night spot with vegan-friendly fillings.', NULL
  UNION ALL SELECT @ocean_id, @alice_id, 5, 'Fresh seafood and perfect sunset patio.', 'https://example.com/review-ocean-1.jpg'
  UNION ALL SELECT @ocean_id, @fiona_id, 4, 'Great for celebrations and date nights.', NULL
  UNION ALL SELECT @cedar_id, @diana_id, 5, 'Quiet vibe and excellent mezze platters.', NULL
  UNION ALL SELECT @cedar_id, @bob_id, 4, 'Consistent quality and friendly staff.', NULL
  UNION ALL SELECT @seoul_id, @ethan_id, 4, 'Fun grill experience for groups.', NULL
  UNION ALL SELECT @seoul_id, @fiona_id, 5, 'Loved the marinated short ribs.', NULL
  UNION ALL SELECT @pho_id, @alice_id, 4, 'Comforting broth and quick lunch service.', NULL
  UNION ALL SELECT @pho_id, @bob_id, 4, 'Reliable noodle soups and fair prices.', NULL
  UNION ALL SELECT @harvest_id, @fiona_id, 5, 'Elegant ambiance and top-notch desserts.', 'https://example.com/review-harvest-1.jpg'
  UNION ALL SELECT @harvest_id, @charlie_id, 4, 'Good cocktails and creative menu.', NULL
  UNION ALL SELECT @napoli_id, @alice_id, 5, 'Wood-fired crust was excellent.', NULL
  UNION ALL SELECT @napoli_id, @ethan_id, 4, 'Great pasta portions for the price.', NULL
  UNION ALL SELECT @bombay_id, @diana_id, 4, 'Balanced spices and great naan.', NULL
  UNION ALL SELECT @bombay_id, @charlie_id, 5, 'One of the best curry spots nearby.', NULL
  UNION ALL SELECT @verde_id, @alice_id, 4, 'Healthy bowls and creative sauces.', NULL
  UNION ALL SELECT @verde_id, @charlie_id, 5, 'Best vegan lunch option in Mountain View.', 'https://example.com/review-verde-1.jpg'
  UNION ALL SELECT @golden_id, @bob_id, 3, 'Fast service, decent portions for a quick meal.', NULL
  UNION ALL SELECT @golden_id, @ethan_id, 4, 'Good value and easy parking.', NULL
  UNION ALL SELECT @luna_id, @fiona_id, 5, 'Excellent tapas and romantic lighting.', 'https://example.com/review-luna-1.jpg'
  UNION ALL SELECT @luna_id, @diana_id, 4, 'Great sangria and music on weekends.', NULL
  UNION ALL SELECT @morning_id, @bob_id, 4, 'Nice brunch menu and family seating.', NULL
  UNION ALL SELECT @morning_id, @charlie_id, 5, 'Excellent coffee and quick service.', NULL
  UNION ALL SELECT @sushi_id, @alice_id, 5, 'Premium fish quality and polished service.', NULL
  UNION ALL SELECT @sushi_id, @fiona_id, 4, 'Great omakase for special occasions.', NULL
  UNION ALL SELECT @smoky_id, @ethan_id, 4, 'Ribs were tender and smoky.', NULL
  UNION ALL SELECT @smoky_id, @bob_id, 4, 'Large portions and fair prices.', NULL
  UNION ALL SELECT @azul_id, @diana_id, 5, 'Outdoor patio and cocktails were excellent.', 'https://example.com/review-azul-1.jpg'
  UNION ALL SELECT @azul_id, @charlie_id, 4, 'Lively vibe and good taco sampler.', NULL
  UNION ALL SELECT @quiet_id, @alice_id, 4, 'Peaceful setting for tea and light meals.', NULL
  UNION ALL SELECT @quiet_id, @fiona_id, 5, 'Loved the calm ambiance and seasonal tea set.', NULL
) AS t
LEFT JOIN reviews r
  ON r.restaurant_id = t.restaurant_id
  AND r.user_id = t.user_id
WHERE t.restaurant_id IS NOT NULL
  AND t.user_id IS NOT NULL
  AND r.id IS NULL;

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

INSERT INTO favorites (user_id, restaurant_id)
SELECT t.user_id, t.restaurant_id
FROM (
  SELECT @charlie_id AS user_id, @verde_id AS restaurant_id
  UNION ALL SELECT @diana_id, @ocean_id
  UNION ALL SELECT @ethan_id, @tacos_id
  UNION ALL SELECT @fiona_id, @luna_id
  UNION ALL SELECT @alice_id, @sushi_id
  UNION ALL SELECT @bob_id, @morning_id
  UNION ALL SELECT @charlie_id, @seoul_id
  UNION ALL SELECT @diana_id, @cedar_id
) AS t
LEFT JOIN favorites f
  ON f.user_id = t.user_id
  AND f.restaurant_id = t.restaurant_id
WHERE t.user_id IS NOT NULL
  AND t.restaurant_id IS NOT NULL
  AND f.id IS NULL;

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

INSERT INTO user_history (user_id, restaurant_id, action, metadata)
SELECT
  t.user_id,
  t.restaurant_id,
  t.action,
  t.metadata
FROM (
  SELECT @charlie_id AS user_id, @verde_id AS restaurant_id, 'favorited' AS action, JSON_OBJECT('source', 'seed') AS metadata
  UNION ALL SELECT @diana_id, @ocean_id, 'favorited', JSON_OBJECT('source', 'seed')
  UNION ALL SELECT @ethan_id, @tacos_id, 'reviewed', JSON_OBJECT('rating', 5, 'source', 'seed')
  UNION ALL SELECT @fiona_id, @luna_id, 'reviewed', JSON_OBJECT('rating', 5, 'source', 'seed')
  UNION ALL SELECT @alice_id, @sushi_id, 'viewed', JSON_OBJECT('source', 'seed')
  UNION ALL SELECT @bob_id, @morning_id, 'viewed', JSON_OBJECT('source', 'seed')
  UNION ALL SELECT @charlie_id, @seoul_id, 'viewed', JSON_OBJECT('source', 'seed')
  UNION ALL SELECT @diana_id, @cedar_id, 'reviewed', JSON_OBJECT('rating', 5, 'source', 'seed')
) AS t
LEFT JOIN user_history h
  ON h.user_id = t.user_id
  AND h.restaurant_id = t.restaurant_id
  AND h.action = t.action
WHERE t.user_id IS NOT NULL
  AND t.restaurant_id IS NOT NULL
  AND h.id IS NULL;

-- Note:
--   Restaurant cover photos are stored in restaurant_photos (introduced in db/003_phase3_schema.sql).
--   This seed file remains compatible with db/001_init_schema.sql only.
--   If you already ran Phase 3 migration, seed restaurant_photos in a follow-up script.

COMMIT;
