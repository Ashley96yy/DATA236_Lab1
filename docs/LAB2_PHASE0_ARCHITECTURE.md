# Lab 2 Phase 0 Architecture Note

## Purpose

This note defines the initial Lab 2 boundaries before implementation begins.

## Target Services

### 1. user-service
- user signup/login
- user profile
- user preferences
- favorites
- history

### 2. owner-service
- owner signup/login
- owner profile
- owner dashboard
- claim restaurant

### 3. restaurant-service
- restaurant create
- restaurant search
- restaurant details
- restaurant photo metadata

### 4. review-api-service
- receives review create/update/delete requests
- validates requests
- publishes Kafka events

### 5. review-worker-service
- consumes review Kafka topics
- processes events
- writes results to MongoDB

## Initial Kafka Topics

- `review.created`
- `review.updated`
- `review.deleted`
- `restaurant.created`

## Initial MongoDB Collections

- `users`
- `owners`
- `user_preferences`
- `sessions`
- `restaurants`
- `reviews`
- `favorites`
- `restaurant_photos`
- `activity_logs`

## Initial Redux Slices

- `authSlice`
- `restaurantSlice`
- `reviewSlice`
- `favoritesSlice`

## Phase 0 Deliverables

- service directory skeleton
- shared backend module skeleton
- deployment directory skeleton
- JMeter directory skeleton
- written architecture note
