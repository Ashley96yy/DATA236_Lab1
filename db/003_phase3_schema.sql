-- Phase 3 schema migration
-- Aligns `restaurants` table with IMPLEMENTATION_PLAN.md section 3.1
-- Adds `restaurant_photos` table (new).
--
-- Safe to run on an existing yelp_lab1 DB.
-- Legacy columns (address, contact_info, hours) are kept — NOT dropped —
-- so existing seed data is preserved. They are ignored by the application layer.
--
-- Run: mysql -u root -p yelp_lab1 < db/003_phase3_schema.sql

USE yelp_lab1;

-- ─────────────────────────────────────────────────────────────────────────────
-- 1. Rename price_tier (ENUM) → pricing_tier (VARCHAR 10)
--    CHANGE preserves existing "$" / "$$" / "$$$" / "$$$$" values.
-- ─────────────────────────────────────────────────────────────────────────────
ALTER TABLE restaurants
  CHANGE COLUMN price_tier pricing_tier VARCHAR(10) NULL;

-- ─────────────────────────────────────────────────────────────────────────────
-- 2. Relax cuisine_type to nullable
--    (plan marks it optional; current schema has NOT NULL)
-- ─────────────────────────────────────────────────────────────────────────────
ALTER TABLE restaurants
  MODIFY COLUMN cuisine_type VARCHAR(100) NULL;

-- ─────────────────────────────────────────────────────────────────────────────
-- 3. Add missing columns
--    Placed after existing columns to avoid full table rebuild ordering issues.
-- ─────────────────────────────────────────────────────────────────────────────
ALTER TABLE restaurants
  ADD COLUMN street            VARCHAR(255)  NULL AFTER city,
  ADD COLUMN state             VARCHAR(50)   NULL AFTER street,
  ADD COLUMN country           VARCHAR(100)  NULL AFTER state,
  ADD COLUMN latitude          FLOAT         NULL AFTER country,
  ADD COLUMN longitude         FLOAT         NULL AFTER latitude,
  ADD COLUMN phone             VARCHAR(30)   NULL AFTER longitude,
  ADD COLUMN email             VARCHAR(255)  NULL AFTER phone,
  ADD COLUMN hours_json        JSON          NULL AFTER email,
  ADD COLUMN amenities         JSON          NULL AFTER hours_json,
  ADD COLUMN claimed_by_owner_id BIGINT UNSIGNED NULL AFTER created_by_user_id,
  ADD CONSTRAINT fk_restaurants_claimed_by_owner
    FOREIGN KEY (claimed_by_owner_id) REFERENCES owners(id)
    ON DELETE SET NULL;

-- ─────────────────────────────────────────────────────────────────────────────
-- 4. Create restaurant_photos table (new — did not exist before Phase 3)
-- ─────────────────────────────────────────────────────────────────────────────
CREATE TABLE IF NOT EXISTS restaurant_photos (
  id                    BIGINT UNSIGNED NOT NULL AUTO_INCREMENT,
  restaurant_id         BIGINT UNSIGNED NOT NULL,
  photo_url             VARCHAR(500)    NOT NULL,
  uploaded_by_user_id   BIGINT UNSIGNED NULL,
  uploaded_by_owner_id  BIGINT UNSIGNED NULL,
  created_at            TIMESTAMP       NOT NULL DEFAULT CURRENT_TIMESTAMP,
  PRIMARY KEY (id),
  KEY idx_restaurant_photos_restaurant_id (restaurant_id),
  CONSTRAINT fk_restaurant_photos_restaurant
    FOREIGN KEY (restaurant_id) REFERENCES restaurants(id)
    ON DELETE CASCADE,
  CONSTRAINT fk_restaurant_photos_user
    FOREIGN KEY (uploaded_by_user_id) REFERENCES users(id)
    ON DELETE SET NULL,
  CONSTRAINT fk_restaurant_photos_owner
    FOREIGN KEY (uploaded_by_owner_id) REFERENCES owners(id)
    ON DELETE SET NULL
);
