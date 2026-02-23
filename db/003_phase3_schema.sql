-- Phase 3 schema migration
-- Aligns `restaurants` table with IMPLEMENTATION_PLAN.md section 3.1
-- Adds `restaurant_photos` table (new).
--
-- Pre-flight check (all confirmed BIGINT UNSIGNED):
--   users.id, owners.id, restaurants.id — all BIGINT UNSIGNED ✓
--
-- Safe to run on an existing yelp_lab1 DB.
-- Legacy columns (address, contact_info, hours) are kept — NOT dropped —
-- so existing seed data is preserved. They are ignored by the application layer.
--
-- Run: mysql -u root -p yelp_lab1 < db/003_phase3_schema.sql

USE yelp_lab1;

-- ─────────────────────────────────────────────────────────────────────────────
-- 1. Alter restaurants: rename price_tier, relax cuisine_type, add new columns
--    (single statement to avoid multiple table rebuilds)
-- ─────────────────────────────────────────────────────────────────────────────
ALTER TABLE restaurants
  CHANGE COLUMN price_tier pricing_tier VARCHAR(10) NULL,
  MODIFY COLUMN cuisine_type VARCHAR(100) NULL,
  ADD COLUMN street VARCHAR(255) NULL,
  ADD COLUMN state VARCHAR(50) NULL,
  ADD COLUMN country VARCHAR(100) NULL,
  ADD COLUMN latitude FLOAT NULL,
  ADD COLUMN longitude FLOAT NULL,
  ADD COLUMN phone VARCHAR(30) NULL,
  ADD COLUMN email VARCHAR(255) NULL,
  ADD COLUMN hours_json JSON NULL,
  ADD COLUMN amenities JSON NULL,
  ADD COLUMN claimed_by_owner_id BIGINT UNSIGNED NULL;

-- ─────────────────────────────────────────────────────────────────────────────
-- 2. Add FK for claimed_by_owner_id (separate statement required by MySQL)
-- ─────────────────────────────────────────────────────────────────────────────
ALTER TABLE restaurants
  ADD CONSTRAINT fk_restaurants_claimed_by_owner
  FOREIGN KEY (claimed_by_owner_id) REFERENCES owners(id)
  ON DELETE SET NULL;

-- ─────────────────────────────────────────────────────────────────────────────
-- 3. Create restaurant_photos table (new — did not exist before Phase 3)
-- ─────────────────────────────────────────────────────────────────────────────
CREATE TABLE IF NOT EXISTS restaurant_photos (
  id BIGINT UNSIGNED NOT NULL AUTO_INCREMENT,
  restaurant_id BIGINT UNSIGNED NOT NULL,
  photo_url VARCHAR(500) NOT NULL,
  uploaded_by_user_id BIGINT UNSIGNED NULL,
  uploaded_by_owner_id BIGINT UNSIGNED NULL,
  created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
  PRIMARY KEY (id),
  CONSTRAINT fk_photos_restaurant
    FOREIGN KEY (restaurant_id) REFERENCES restaurants(id)
    ON DELETE CASCADE,
  CONSTRAINT fk_photos_uploaded_by_user
    FOREIGN KEY (uploaded_by_user_id) REFERENCES users(id)
    ON DELETE SET NULL,
  CONSTRAINT fk_photos_uploaded_by_owner
    FOREIGN KEY (uploaded_by_owner_id) REFERENCES owners(id)
    ON DELETE SET NULL
);
