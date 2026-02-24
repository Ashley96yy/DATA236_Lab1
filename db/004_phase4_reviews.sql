-- Phase 4 migration: align reviews table for Phase 4
-- The reviews table already exists from 001_init_schema.sql.
-- This migration makes comment nullable (plan specifies it as optional).
--
-- Apply with: mysql -u root -p yelp_lab1 < db/004_phase4_reviews.sql

USE yelp_lab1;

ALTER TABLE reviews
  MODIFY COLUMN comment TEXT NULL;
