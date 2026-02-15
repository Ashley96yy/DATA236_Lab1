# API Contract v1 (MVP)

## 1) Conventions
- Base URL: `/api/v1`
- Auth: `Authorization: Bearer <JWT>`
- Content-Type: `application/json`
- Time format: ISO 8601 (e.g. `2026-02-15T20:30:00Z`)
- Pagination query: `page` (default 1), `size` (default 10)

## 2) Health
### GET `/health`
Response 200
```json
{ "status": "ok" }
```

## 3) Auth
### POST `/auth/signup`
Request
```json
{
  "name": "Alice",
  "email": "alice@example.com",
  "password": "Passw0rd!"
}
```
Response 201
```json
{
  "id": 1,
  "name": "Alice",
  "email": "alice@example.com"
}
```

### POST `/auth/login`
Request
```json
{
  "email": "alice@example.com",
  "password": "Passw0rd!"
}
```
Response 200
```json
{
  "access_token": "jwt-token",
  "token_type": "bearer",
  "user": {
    "id": 1,
    "name": "Alice",
    "email": "alice@example.com"
  }
}
```

## 4) User Profile
### GET `/users/me`
Response 200
```json
{
  "id": 1,
  "name": "Alice",
  "email": "alice@example.com",
  "phone": "1234567890",
  "about_me": "I love food",
  "city": "San Jose",
  "country": "US",
  "languages": "English,Chinese",
  "gender": "female",
  "avatar_url": "https://..."
}
```

### PUT `/users/me`
Request
```json
{
  "name": "Alice Chen",
  "phone": "1234567890",
  "about_me": "I love food",
  "city": "San Jose",
  "country": "US",
  "languages": "English,Chinese",
  "gender": "female",
  "avatar_url": "https://..."
}
```
Response 200: same shape as `GET /users/me`

## 5) User Preferences
### GET `/users/me/preferences`
Response 200
```json
{
  "cuisines": ["Italian", "Japanese"],
  "price_range": "$$",
  "preferred_locations": ["San Jose", "Santa Clara"],
  "search_radius_km": 10,
  "dietary_needs": ["vegetarian"],
  "ambiance": ["casual", "family-friendly"],
  "sort_preference": "rating"
}
```

### PUT `/users/me/preferences`
Request/Response 200: same shape as above

## 6) Restaurants
### POST `/restaurants`
Request
```json
{
  "name": "Pasta Place",
  "cuisine_type": "Italian",
  "address": "123 Main St",
  "city": "San Jose",
  "zip_code": "95112",
  "description": "Fresh pasta",
  "contact_info": "408-000-0000",
  "hours": "10:00-22:00",
  "price_tier": "$$"
}
```
Response 201
```json
{ "id": 101, "message": "created" }
```

### GET `/restaurants`
Query params
`name`, `cuisine`, `keyword`, `city`, `zip`, `sort`, `page`, `size`
Response 200
```json
{
  "items": [
    {
      "id": 101,
      "name": "Pasta Place",
      "cuisine_type": "Italian",
      "city": "San Jose",
      "price_tier": "$$",
      "avg_rating": 4.5,
      "review_count": 23
    }
  ],
  "page": 1,
  "size": 10,
  "total": 1
}
```

### GET `/restaurants/{restaurant_id}`
Response 200
```json
{
  "id": 101,
  "name": "Pasta Place",
  "cuisine_type": "Italian",
  "address": "123 Main St",
  "city": "San Jose",
  "zip_code": "95112",
  "description": "Fresh pasta",
  "contact_info": "408-000-0000",
  "hours": "10:00-22:00",
  "price_tier": "$$",
  "avg_rating": 4.5,
  "review_count": 23
}
```

## 7) Reviews
### GET `/restaurants/{restaurant_id}/reviews`
Response 200
```json
{
  "items": [
    {
      "id": 5001,
      "user_id": 1,
      "user_name": "Alice",
      "rating": 5,
      "comment": "Great!",
      "created_at": "2026-02-15T20:30:00Z"
    }
  ]
}
```

### POST `/restaurants/{restaurant_id}/reviews`
Request
```json
{
  "rating": 5,
  "comment": "Great!",
  "photo_url": "https://..."
}
```
Response 201
```json
{ "id": 5001, "message": "created" }
```

### PUT `/reviews/{review_id}`
Request
```json
{
  "rating": 4,
  "comment": "Still good"
}
```
Response 200
```json
{ "id": 5001, "message": "updated" }
```

### DELETE `/reviews/{review_id}`
Response 200
```json
{ "message": "deleted" }
```

## 8) Favorites
### POST `/restaurants/{restaurant_id}/favorite`
Response 200
```json
{ "message": "favorited" }
```

### DELETE `/restaurants/{restaurant_id}/favorite`
Response 200
```json
{ "message": "unfavorited" }
```

### GET `/users/me/favorites`
Response 200
```json
{
  "items": [
    {
      "id": 101,
      "name": "Pasta Place",
      "cuisine_type": "Italian",
      "city": "San Jose",
      "price_tier": "$$",
      "avg_rating": 4.5
    }
  ]
}
```

## 9) History
### GET `/users/me/history`
Response 200
```json
{
  "items": [
    {
      "restaurant_id": 101,
      "restaurant_name": "Pasta Place",
      "action": "reviewed",
      "timestamp": "2026-02-15T20:30:00Z"
    }
  ]
}
```

## 10) AI Assistant
### POST `/ai-assistant/chat`
Request
```json
{
  "message": "I want a romantic dinner tonight",
  "conversation_history": [
    { "role": "user", "content": "I like Italian food" },
    { "role": "assistant", "content": "Got it." }
  ]
}
```
Response 200
```json
{
  "reply": "Based on your preferences, here are good options.",
  "recommendations": [
    {
      "restaurant_id": 101,
      "name": "Pasta Place",
      "rating": 4.5,
      "price_tier": "$$",
      "cuisine_type": "Italian",
      "reason": "Matches your cuisine and budget preferences"
    }
  ],
  "applied_filters": {
    "cuisine": ["Italian"],
    "price_range": "$$",
    "ambiance": ["romantic"]
  }
}
```

## 11) Common Error Response
All 4xx/5xx:
```json
{
  "error": {
    "code": "VALIDATION_ERROR",
    "message": "rating must be between 1 and 5"
  }
}
```
