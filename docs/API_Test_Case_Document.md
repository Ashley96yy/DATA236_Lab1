# API Test Case Document

## Title Page

**Project:** Dine Finder API  
**Backend Framework:** FastAPI  
**Test Type:** Manual API Testing via Swagger UI  
**Environment:** Local / Development  
**Prepared For:** Manual verification only  
**Important Note:** This document contains manual test cases only. No tests were executed or simulated.

---

## 1. Document Scope

This document provides manual QA test cases for all FastAPI endpoints currently exposed by the project.  
All test cases are intended to be executed manually in Swagger UI.

**Swagger URL:** `http://127.0.0.1:8000/docs`  
**API Base URL:** `http://127.0.0.1:8000/api/v1`

---

## 2. General Test Data / Preconditions

Use the following placeholders during manual testing:

- `USER_JWT` = access token returned from a successful user login
- `OWNER_JWT` = access token returned from a successful owner login
- `VALID_RESTAURANT_ID` = an existing restaurant ID
- `INVALID_RESTAURANT_ID` = a non-existing restaurant ID, for example `999999`
- `VALID_REVIEW_ID` = an existing review ID owned by the logged-in user
- `OTHER_USER_REVIEW_ID` = an existing review ID owned by another user
- `CLAIMABLE_RESTAURANT_ID` = an existing unclaimed restaurant ID
- `CLAIMED_BY_OTHER_OWNER_ID` = an existing restaurant already claimed by another owner

Suggested manual setup sequence:

1. Create a new user account.
2. Log in as that user and save the returned JWT.
3. Create or identify an existing restaurant.
4. Create a review as that user.
5. Create a new owner account.
6. Log in as that owner and save the returned JWT.
7. Claim or create an owner-managed restaurant.

**Common Success Response Pattern**

- `200 OK`, `201 Created`, or `204 No Content`

**Common Error Response Pattern**

```json
{
  "error": {
    "code": "ERROR_CODE",
    "message": "Human-readable message"
  }
}
```

---

# 3. API Test Cases

---

## API 1. Root Health Check

### Endpoint Information

- **Method:** `GET`
- **Path:** `/health`
- **Description:** Root application health check

### Request Details

- **Headers:** None
- **Path Parameters:** None
- **Query Parameters:** None
- **Request Body:** None

### Test Cases

| Test Case ID | Scenario | Input | Expected Result |
|---|---|---|---|
| HC-001 | Valid root health check | `GET /health` | `200 OK`; response contains `{"status":"ok"}` |
| HC-002 | Verify no auth required | No Authorization header | `200 OK`; endpoint remains publicly accessible |

### Expected Result

- **Status Code:** `200 OK`
- **Response JSON:**

```json
{
  "status": "ok"
}
```

---

## API 2. Versioned Health Check

### Endpoint Information

- **Method:** `GET`
- **Path:** `/api/v1/health`
- **Description:** Versioned API health check with database ping

### Request Details

- **Headers:** None
- **Path Parameters:** None
- **Query Parameters:** None
- **Request Body:** None

### Test Cases

| Test Case ID | Scenario | Input | Expected Result |
|---|---|---|---|
| HC-003 | Valid versioned health check | `GET /api/v1/health` | `200 OK`; response contains `{"status":"ok"}` |
| HC-004 | Verify public accessibility | No Authorization header | `200 OK`; endpoint accessible without login |

### Expected Result

- **Status Code:** `200 OK`
- **Response JSON:**

```json
{
  "status": "ok"
}
```

---

## API 3. User Signup

### Endpoint Information

- **Method:** `POST`
- **Path:** `/api/v1/auth/signup`
- **Description:** Register a new user

### Request Details

- **Headers:** `Content-Type: application/json`
- **Path Parameters:** None
- **Query Parameters:** None
- **Request Body Example:**

```json
{
  "name": "QA User One",
  "email": "qa_user_one@example.com",
  "password": "Passw0rd!"
}
```

### Test Cases

| Test Case ID | Scenario | Input | Expected Result |
|---|---|---|---|
| AUTH-U-001 | ✅ Create new user | Valid unique name/email/password | `201 Created`; returns user object with `id`, `name`, `email` |
| AUTH-U-002 | ❌ Duplicate email | Reuse existing email | `409 Conflict`; error message indicates email already exists |
| AUTH-U-003 | ❌ Password too short | Password shorter than 8 chars | `422 Unprocessable Entity`; validation error |
| AUTH-U-004 | ⚠️ Email case normalization | Use uppercase email | `201 Created`; stored/returned email is normalized to lowercase |

### Expected Result

- **Status Code:** `201 Created`
- **Response JSON:**

```json
{
  "id": 1,
  "name": "QA User One",
  "email": "qa_user_one@example.com"
}
```

---

## API 4. User Login

### Endpoint Information

- **Method:** `POST`
- **Path:** `/api/v1/auth/login`
- **Description:** Log in as a user and obtain JWT

### Request Details

- **Headers:** `Content-Type: application/json`
- **Request Body Example:**

```json
{
  "email": "qa_user_one@example.com",
  "password": "Passw0rd!"
}
```

### Test Cases

| Test Case ID | Scenario | Input | Expected Result |
|---|---|---|---|
| AUTH-U-005 | ✅ Valid login | Correct email/password | `200 OK`; returns `access_token`, `token_type`, and `user` |
| AUTH-U-006 | ❌ Wrong password | Correct email, wrong password | `401 Unauthorized`; invalid credentials error |
| AUTH-U-007 | ❌ Unknown email | Non-existing email | `401 Unauthorized` |
| AUTH-U-008 | ⚠️ Email case normalization | Uppercase email with correct password | `200 OK`; login still succeeds |

### Expected Result

- **Status Code:** `200 OK`
- **Response JSON:**

```json
{
  "access_token": "<USER_JWT>",
  "token_type": "bearer",
  "user": {
    "id": 1,
    "name": "QA User One",
    "email": "qa_user_one@example.com"
  }
}
```

---

## API 5. User Signup Alias

### Endpoint Information

- **Method:** `POST`
- **Path:** `/api/v1/auth/user/signup`
- **Description:** Alias route for user signup

### Request Details

- **Headers:** `Content-Type: application/json`
- **Request Body Example:**

```json
{
  "name": "QA User Two",
  "email": "qa_user_two@example.com",
  "password": "Passw0rd!"
}
```

### Test Cases

| Test Case ID | Scenario | Input | Expected Result |
|---|---|---|---|
| AUTH-U-009 | ✅ Alias signup works | Valid unique user payload | `201 Created`; same behavior as `/auth/signup` |
| AUTH-U-010 | ❌ Duplicate email on alias route | Existing user email | `409 Conflict` |

### Expected Result

- **Status Code:** `201 Created`
- **Response JSON:** Same structure as API 3

---

## API 6. User Login Alias

### Endpoint Information

- **Method:** `POST`
- **Path:** `/api/v1/auth/user/login`
- **Description:** Alias route for user login

### Request Details

- **Headers:** `Content-Type: application/json`
- **Request Body Example:**

```json
{
  "email": "qa_user_one@example.com",
  "password": "Passw0rd!"
}
```

### Test Cases

| Test Case ID | Scenario | Input | Expected Result |
|---|---|---|---|
| AUTH-U-011 | ✅ Alias login works | Valid credentials | `200 OK`; same behavior as `/auth/login` |
| AUTH-U-012 | ❌ Invalid credentials via alias route | Wrong password | `401 Unauthorized` |

### Expected Result

- **Status Code:** `200 OK`
- **Response JSON:** Same structure as API 4

---

## API 7. Owner Signup

### Endpoint Information

- **Method:** `POST`
- **Path:** `/api/v1/auth/owner/signup`
- **Description:** Register a new restaurant owner

### Request Details

- **Headers:** `Content-Type: application/json`
- **Request Body Example:**

```json
{
  "name": "QA Owner One",
  "email": "qa_owner_one@example.com",
  "password": "Passw0rd!",
  "restaurant_location": "San Jose, CA"
}
```

### Test Cases

| Test Case ID | Scenario | Input | Expected Result |
|---|---|---|---|
| AUTH-O-001 | ✅ Create new owner | Valid unique owner payload | `201 Created`; returns owner object |
| AUTH-O-002 | ❌ Duplicate owner email | Existing owner email | `409 Conflict` |
| AUTH-O-003 | ❌ Missing restaurant_location | Empty or missing field | `422 Unprocessable Entity` |
| AUTH-O-004 | ⚠️ Email case normalization | Uppercase owner email | `201 Created`; email returned lowercase |

### Expected Result

- **Status Code:** `201 Created`
- **Response JSON:**

```json
{
  "id": 1,
  "name": "QA Owner One",
  "email": "qa_owner_one@example.com",
  "restaurant_location": "San Jose, CA"
}
```

---

## API 8. Owner Login

### Endpoint Information

- **Method:** `POST`
- **Path:** `/api/v1/auth/owner/login`
- **Description:** Log in as an owner and obtain owner JWT

### Request Details

- **Headers:** `Content-Type: application/json`
- **Request Body Example:**

```json
{
  "email": "qa_owner_one@example.com",
  "password": "Passw0rd!"
}
```

### Test Cases

| Test Case ID | Scenario | Input | Expected Result |
|---|---|---|---|
| AUTH-O-005 | ✅ Valid owner login | Correct email/password | `200 OK`; returns owner token and owner object |
| AUTH-O-006 | ❌ Wrong password | Correct owner email, wrong password | `401 Unauthorized` |
| AUTH-O-007 | ❌ Unknown owner email | Non-existing owner email | `401 Unauthorized` |

### Expected Result

- **Status Code:** `200 OK`
- **Response JSON:**

```json
{
  "access_token": "<OWNER_JWT>",
  "token_type": "bearer",
  "owner": {
    "id": 1,
    "name": "QA Owner One",
    "email": "qa_owner_one@example.com",
    "restaurant_location": "San Jose, CA"
  }
}
```

---

## API 9. Current User Profile via Auth Route

### Endpoint Information

- **Method:** `GET`
- **Path:** `/api/v1/auth/me`
- **Description:** Return current logged-in user

### Request Details

- **Headers:** `Authorization: Bearer USER_JWT`
- **Request Body:** None

### Test Cases

| Test Case ID | Scenario | Input | Expected Result |
|---|---|---|---|
| AUTH-U-013 | ✅ Valid token | Valid user JWT | `200 OK`; returns current user |
| AUTH-U-014 | 🔐 Missing token | No Authorization header | `401 Unauthorized` |
| AUTH-U-015 | 🔐 Owner token used on user route | `Authorization: Bearer OWNER_JWT` | `401 Unauthorized` |
| AUTH-U-016 | 🔐 Invalid token | Malformed or expired token | `401 Unauthorized` |

### Expected Result

- **Status Code:** `200 OK`
- **Response JSON:**

```json
{
  "id": 1,
  "name": "QA User One",
  "email": "qa_user_one@example.com"
}
```

---

## API 10. Get User Profile

### Endpoint Information

- **Method:** `GET`
- **Path:** `/api/v1/users/me`
- **Description:** Get current user profile details

### Request Details

- **Headers:** `Authorization: Bearer USER_JWT`
- **Request Body:** None

### Test Cases

| Test Case ID | Scenario | Input | Expected Result |
|---|---|---|---|
| USER-001 | ✅ Get current profile | Valid user token | `200 OK`; returns profile fields |
| USER-002 | 🔐 No token | Missing Authorization header | `401 Unauthorized` |
| USER-003 | 🔐 Wrong token type | Owner token | `401 Unauthorized` |

### Expected Result

- **Status Code:** `200 OK`
- **Response JSON:**

```json
{
  "id": 1,
  "name": "QA User One",
  "email": "qa_user_one@example.com",
  "phone": null,
  "about_me": null,
  "city": null,
  "state": null,
  "country": null,
  "languages": null,
  "gender": null,
  "avatar_url": null
}
```

---

## API 11. Update User Profile

### Endpoint Information

- **Method:** `PUT`
- **Path:** `/api/v1/users/me`
- **Description:** Update current user profile

### Request Details

- **Headers:** `Authorization: Bearer USER_JWT`, `Content-Type: application/json`
- **Request Body Example:**

```json
{
  "name": "QA User One Updated",
  "phone": "4081234567",
  "about_me": "I enjoy trying new restaurants.",
  "city": "San Jose",
  "state": "CA",
  "country": "US",
  "languages": "English,Chinese",
  "gender": "other"
}
```

### Test Cases

| Test Case ID | Scenario | Input | Expected Result |
|---|---|---|---|
| USER-004 | ✅ Update profile with valid data | Valid payload | `200 OK`; returned profile reflects updates |
| USER-005 | ❌ Invalid state format | `state: "California"` | `422 Unprocessable Entity` |
| USER-006 | ❌ Unsupported country code | `country: "ZZ"` | `422 Unprocessable Entity` |
| USER-007 | ⚠️ Partial update | Send only `city` | `200 OK`; only provided field changes |
| USER-008 | 🔐 Missing token | No Authorization header | `401 Unauthorized` |

### Expected Result

- **Status Code:** `200 OK`
- **Response JSON:** Same structure as API 10 with updated values

---

## API 12. Get User Preferences

### Endpoint Information

- **Method:** `GET`
- **Path:** `/api/v1/users/me/preferences`
- **Description:** Get current user's dining preferences

### Request Details

- **Headers:** `Authorization: Bearer USER_JWT`
- **Request Body:** None

### Test Cases

| Test Case ID | Scenario | Input | Expected Result |
|---|---|---|---|
| PREF-001 | ✅ Get preferences | Valid user token | `200 OK`; returns preference object |
| PREF-002 | ⚠️ First-time user with no preferences | User without saved preferences | `200 OK`; returns defaults / empty arrays |
| PREF-003 | 🔐 Missing token | No Authorization header | `401 Unauthorized` |

### Expected Result

- **Status Code:** `200 OK`
- **Response JSON:**

```json
{
  "cuisines": [],
  "price_range": null,
  "preferred_locations": [],
  "search_radius_km": null,
  "dietary_needs": [],
  "ambiance": [],
  "sort_preference": "rating"
}
```

---

## API 13. Update User Preferences

### Endpoint Information

- **Method:** `PUT`
- **Path:** `/api/v1/users/me/preferences`
- **Description:** Create or update user dining preferences

### Request Details

- **Headers:** `Authorization: Bearer USER_JWT`, `Content-Type: application/json`
- **Request Body Example:**

```json
{
  "cuisines": ["Italian", "Japanese"],
  "price_range": "$$",
  "preferred_locations": ["San Jose", "Santa Clara"],
  "search_radius_km": 15,
  "dietary_needs": ["vegetarian"],
  "ambiance": ["casual", "quiet"],
  "sort_preference": "rating"
}
```

### Test Cases

| Test Case ID | Scenario | Input | Expected Result |
|---|---|---|---|
| PREF-004 | ✅ Save valid preferences | Valid payload | `200 OK`; preferences saved and returned |
| PREF-005 | ❌ Invalid sort_preference | `sort_preference: "random"` | `422 Unprocessable Entity` |
| PREF-006 | ❌ Negative search_radius_km | `-5` | `422 Unprocessable Entity` |
| PREF-007 | ⚠️ Partial preference update | Send only `price_range` | `200 OK`; existing other values remain |
| PREF-008 | 🔐 Missing token | No Authorization header | `401 Unauthorized` |

### Expected Result

- **Status Code:** `200 OK`
- **Response JSON:** Same structure as API 12 with updated values

---

## API 14. Upload User Avatar

### Endpoint Information

- **Method:** `POST`
- **Path:** `/api/v1/users/me/avatar`
- **Description:** Upload current user's avatar image

### Request Details

- **Headers:** `Authorization: Bearer USER_JWT`
- **Content Type:** `multipart/form-data`
- **Form Field:** `file`
- **Request Body:** Not JSON. Use Swagger file upload control.

### Test Cases

| Test Case ID | Scenario | Input | Expected Result |
|---|---|---|---|
| USER-009 | ✅ Upload valid PNG/JPG/WEBP | Small valid image file | `201 Created`; returns `avatar_url` |
| USER-010 | ❌ Unsupported extension | `.gif` or `.bmp` | `400 Bad Request` |
| USER-011 | ❌ Wrong MIME type | Non-image file renamed as image | `400 Bad Request` |
| USER-012 | ❌ File too large | Image larger than 5MB | `413 Payload Too Large` |
| USER-013 | 🔐 Missing token | No Authorization header | `401 Unauthorized` |

### Expected Result

- **Status Code:** `201 Created`
- **Response JSON:**

```json
{
  "avatar_url": "http://127.0.0.1:8000/uploads/avatars/<generated-file-name>.png"
}
```

---

## API 15. Create Restaurant (User)

### Endpoint Information

- **Method:** `POST`
- **Path:** `/api/v1/restaurants`
- **Description:** Create a restaurant listing as a user

### Request Details

- **Headers:** `Authorization: Bearer USER_JWT`, `Content-Type: application/json`
- **Request Body Example:**

```json
{
  "name": "QA Bistro",
  "cuisine_type": "Italian",
  "description": "Cozy handmade pasta place.",
  "street": "123 Test St",
  "city": "San Jose",
  "state": "CA",
  "zip_code": "95112",
  "country": "USA",
  "latitude": 37.3382,
  "longitude": -121.8863,
  "phone": "4085550001",
  "email": "qabistro@example.com",
  "hours_json": {
    "Mon": "10am-9pm",
    "Tue": "10am-9pm"
  },
  "pricing_tier": "$$",
  "amenities": ["WiFi", "Outdoor Seating"]
}
```

### Test Cases

| Test Case ID | Scenario | Input | Expected Result |
|---|---|---|---|
| REST-001 | ✅ Create restaurant with full valid payload | Valid restaurant JSON | `201 Created`; returns restaurant detail |
| REST-002 | ✅ Create restaurant with minimal required fields | Only `name` and `city` plus optional nulls | `201 Created` |
| REST-003 | ❌ Missing required field | Omit `name` or `city` | `422 Unprocessable Entity` |
| REST-004 | ❌ Invalid pricing_tier | `pricing_tier: "$$$$$"` | `422 Unprocessable Entity` |
| REST-005 | 🔐 Missing user token | No Authorization header | `401 Unauthorized` |
| REST-006 | 🔐 Wrong token type | Owner token | `401 Unauthorized` |

### Expected Result

- **Status Code:** `201 Created`
- **Response JSON:** Restaurant detail object with `id`, data fields, ratings, and timestamps

---

## API 16. Search Restaurants

### Endpoint Information

- **Method:** `GET`
- **Path:** `/api/v1/restaurants`
- **Description:** Public search, filter, sort, and paginate restaurants

### Request Details

- **Headers:** None
- **Query Parameters:** `name`, `cuisine`, `keywords`, `city`, `zip`, `sort`, `page`, `limit`
- **Request Body:** None

### Test Cases

| Test Case ID | Scenario | Input | Expected Result |
|---|---|---|---|
| REST-007 | ✅ Basic list request | No query parameters | `200 OK`; paginated restaurant list |
| REST-008 | ✅ Search by name | `?name=sushi` | `200 OK`; matching restaurants returned |
| REST-009 | ✅ Filter by cuisine and city | `?cuisine=Italian&city=San Jose` | `200 OK` |
| REST-010 | ✅ Sort by rating | `?sort=rating` | `200 OK`; sorted response |
| REST-011 | ✅ Sort by review_count | `?sort=review_count` | `200 OK`; sorted response |
| REST-012 | ❌ Invalid sort value | `?sort=random` | `422 Unprocessable Entity` |
| REST-013 | ❌ Invalid page value | `?page=0` | `422 Unprocessable Entity` |
| REST-014 | ❌ Invalid limit value | `?limit=1000` | `422 Unprocessable Entity` |
| REST-015 | ⚠️ No matching results | Unused filters | `200 OK`; `items` empty, `total` maybe `0` |

### Expected Result

- **Status Code:** `200 OK`
- **Response JSON:**

```json
{
  "items": [
    {
      "id": 1,
      "name": "Sample Restaurant",
      "cuisine_type": "Italian",
      "description": "Example",
      "city": "San Jose",
      "state": "CA",
      "pricing_tier": "$$",
      "amenities": ["WiFi"],
      "average_rating": 4.5,
      "review_count": 10,
      "cover_photo_url": null
    }
  ],
  "total": 1,
  "page": 1,
  "limit": 10
}
```

---

## API 17. Get Restaurant Details

### Endpoint Information

- **Method:** `GET`
- **Path:** `/api/v1/restaurants/{restaurant_id}`
- **Description:** Public restaurant detail endpoint

### Request Details

- **Headers:** None
- **Path Parameters:** `restaurant_id`
- **Request Body:** None

### Test Cases

| Test Case ID | Scenario | Input | Expected Result |
|---|---|---|---|
| REST-016 | ✅ Existing restaurant | Valid existing `restaurant_id` | `200 OK`; full restaurant detail returned |
| REST-017 | ❌ Non-existing restaurant | `restaurant_id=999999` | `404 Not Found` |
| REST-018 | ❌ Invalid path type | Non-integer path parameter | `422 Unprocessable Entity` |

### Expected Result

- **Status Code:** `200 OK`
- **Response JSON:** Restaurant detail object including ratings and photos

---

## API 18. Upload Restaurant Photos

### Endpoint Information

- **Method:** `POST`
- **Path:** `/api/v1/restaurants/{restaurant_id}/photos`
- **Description:** Upload restaurant photos as creator user or claimed owner

### Request Details

- **Headers:** `Authorization: Bearer USER_JWT` or `Authorization: Bearer OWNER_JWT`
- **Content Type:** `multipart/form-data`
- **Form Field:** `files` (multiple files supported)
- **Request Body:** Not JSON. Use Swagger file upload control.

### Test Cases

| Test Case ID | Scenario | Input | Expected Result |
|---|---|---|---|
| REST-019 | ✅ User uploads photo to own restaurant | Creator user token + valid image | `201 Created`; returns uploaded photo list |
| REST-020 | ✅ Owner uploads photo to claimed restaurant | Claimed owner token + valid image | `201 Created` |
| REST-021 | ❌ Missing token | No Authorization header | `401 Unauthorized` |
| REST-022 | ❌ Invalid token | Malformed token | `401 Unauthorized` |
| REST-023 | ❌ Unauthorized user | Valid token but user does not own restaurant | `403 Forbidden` |
| REST-024 | ❌ Unauthorized owner | Owner token but restaurant not claimed by owner | `403 Forbidden` |
| REST-025 | ❌ Invalid restaurant ID | Non-existing `restaurant_id` | `404 Not Found` |
| REST-026 | ⚠️ Too many or bad files | Upload invalid/empty file set | `400 Bad Request` |

### Expected Result

- **Status Code:** `201 Created`
- **Response JSON:**

```json
{
  "photos": [
    {
      "id": 1,
      "photo_url": "http://127.0.0.1:8000/uploads/restaurant_photos/<file-name>.jpg"
    }
  ]
}
```

---

## API 19. Create Review

### Endpoint Information

- **Method:** `POST`
- **Path:** `/api/v1/restaurants/{restaurant_id}/reviews`
- **Description:** Submit one review per user per restaurant

### Request Details

- **Headers:** `Authorization: Bearer USER_JWT`, `Content-Type: application/json`
- **Path Parameters:** `restaurant_id`
- **Request Body Example:**

```json
{
  "rating": 5,
  "comment": "Excellent food and service."
}
```

### Test Cases

| Test Case ID | Scenario | Input | Expected Result |
|---|---|---|---|
| REV-001 | ✅ Create valid review | Valid restaurant ID + valid payload | `201 Created` |
| REV-002 | ❌ Duplicate review by same user | Review same restaurant again | `409 Conflict` |
| REV-003 | ❌ Invalid rating high | `rating: 6` | `422 Unprocessable Entity` |
| REV-004 | ❌ Invalid rating low | `rating: 0` | `422 Unprocessable Entity` |
| REV-005 | ❌ Non-existing restaurant | Invalid `restaurant_id` | `404 Not Found` |
| REV-006 | 🔐 Missing token | No Authorization header | `401 Unauthorized` |

### Expected Result

- **Status Code:** `201 Created`
- **Response JSON:**

```json
{
  "id": 1,
  "restaurant_id": 1,
  "rating": 5,
  "comment": "Excellent food and service.",
  "user_name": "QA User One",
  "created_at": "2026-03-20T00:00:00",
  "updated_at": "2026-03-20T00:00:00"
}
```

---

## API 20. List Reviews for Restaurant

### Endpoint Information

- **Method:** `GET`
- **Path:** `/api/v1/restaurants/{restaurant_id}/reviews`
- **Description:** Public paginated review list for a restaurant

### Request Details

- **Headers:** None
- **Path Parameters:** `restaurant_id`
- **Query Parameters:** `page`, `limit`
- **Request Body:** None

### Test Cases

| Test Case ID | Scenario | Input | Expected Result |
|---|---|---|---|
| REV-007 | ✅ List reviews | Valid restaurant ID | `200 OK`; returns paginated reviews |
| REV-008 | ✅ Paginated list | `?page=1&limit=5` | `200 OK` |
| REV-009 | ❌ Invalid page | `page=0` | `422 Unprocessable Entity` |
| REV-010 | ❌ Invalid limit | `limit=500` | `422 Unprocessable Entity` |
| REV-011 | ⚠️ Restaurant with no reviews | Valid restaurant ID without reviews | `200 OK`; empty list |

### Expected Result

- **Status Code:** `200 OK`
- **Response JSON:** Dictionary containing paginated review items

---

## API 21. Update Review

### Endpoint Information

- **Method:** `PUT`
- **Path:** `/api/v1/reviews/{review_id}`
- **Description:** Update current user's own review

### Request Details

- **Headers:** `Authorization: Bearer USER_JWT`, `Content-Type: application/json`
- **Path Parameters:** `review_id`
- **Request Body Example:**

```json
{
  "rating": 4,
  "comment": "Updated review after second visit."
}
```

### Test Cases

| Test Case ID | Scenario | Input | Expected Result |
|---|---|---|---|
| REV-012 | ✅ Update own review | Valid own `review_id` + valid payload | `200 OK`; review updated |
| REV-013 | ❌ Update another user's review | `OTHER_USER_REVIEW_ID` | `403 Forbidden` |
| REV-014 | ❌ Non-existing review | Invalid `review_id` | `404 Not Found` |
| REV-015 | ❌ Invalid rating | `rating: 10` | `422 Unprocessable Entity` |
| REV-016 | 🔐 Missing token | No Authorization header | `401 Unauthorized` |

### Expected Result

- **Status Code:** `200 OK`
- **Response JSON:** Same structure as API 19 with updated values

---

## API 22. Delete Review

### Endpoint Information

- **Method:** `DELETE`
- **Path:** `/api/v1/reviews/{review_id}`
- **Description:** Delete current user's own review

### Request Details

- **Headers:** `Authorization: Bearer USER_JWT`
- **Path Parameters:** `review_id`
- **Request Body:** None

### Test Cases

| Test Case ID | Scenario | Input | Expected Result |
|---|---|---|---|
| REV-017 | ✅ Delete own review | Valid own `review_id` | `204 No Content` |
| REV-018 | ❌ Delete another user's review | `OTHER_USER_REVIEW_ID` | `403 Forbidden` |
| REV-019 | ❌ Delete non-existing review | Invalid `review_id` | `404 Not Found` |
| REV-020 | 🔐 Missing token | No Authorization header | `401 Unauthorized` |

### Expected Result

- **Status Code:** `204 No Content`
- **Response Body:** Empty

---

## API 23. Add Favorite

### Endpoint Information

- **Method:** `POST`
- **Path:** `/api/v1/favorites/{restaurant_id}`
- **Description:** Add a restaurant to the current user's favorites

### Request Details

- **Headers:** `Authorization: Bearer USER_JWT`
- **Path Parameters:** `restaurant_id`
- **Request Body:** None

### Test Cases

| Test Case ID | Scenario | Input | Expected Result |
|---|---|---|---|
| FAV-001 | ✅ Add favorite | Valid restaurant ID | `201 Created`; `favorited: true` |
| FAV-002 | ❌ Favorite same restaurant again | Same `restaurant_id` twice | `409 Conflict` |
| FAV-003 | ❌ Non-existing restaurant | Invalid `restaurant_id` | `404 Not Found` |
| FAV-004 | 🔐 Missing token | No Authorization header | `401 Unauthorized` |

### Expected Result

- **Status Code:** `201 Created`
- **Response JSON:**

```json
{
  "restaurant_id": 1,
  "favorited": true
}
```

---

## API 24. Remove Favorite

### Endpoint Information

- **Method:** `DELETE`
- **Path:** `/api/v1/favorites/{restaurant_id}`
- **Description:** Remove a restaurant from favorites

### Request Details

- **Headers:** `Authorization: Bearer USER_JWT`
- **Path Parameters:** `restaurant_id`
- **Request Body:** None

### Test Cases

| Test Case ID | Scenario | Input | Expected Result |
|---|---|---|---|
| FAV-005 | ✅ Remove existing favorite | Favorited `restaurant_id` | `204 No Content` |
| FAV-006 | ❌ Remove non-favorited restaurant | Restaurant not in favorites | `404 Not Found` |
| FAV-007 | 🔐 Missing token | No Authorization header | `401 Unauthorized` |

### Expected Result

- **Status Code:** `204 No Content`
- **Response Body:** Empty

---

## API 25. List Favorites

### Endpoint Information

- **Method:** `GET`
- **Path:** `/api/v1/users/me/favorites`
- **Description:** List current user's favorite restaurants

### Request Details

- **Headers:** `Authorization: Bearer USER_JWT`
- **Query Parameters:** `page`, `limit`
- **Request Body:** None

### Test Cases

| Test Case ID | Scenario | Input | Expected Result |
|---|---|---|---|
| FAV-008 | ✅ List favorites | Valid user token | `200 OK`; returns favorite restaurant list |
| FAV-009 | ✅ Pagination works | `?page=1&limit=5` | `200 OK` |
| FAV-010 | ⚠️ No favorites | User without favorites | `200 OK`; empty `items` |
| FAV-011 | ❌ Invalid page/limit | `page=0` or `limit=500` | `422 Unprocessable Entity` |
| FAV-012 | 🔐 Missing token | No Authorization header | `401 Unauthorized` |

### Expected Result

- **Status Code:** `200 OK`
- **Response JSON:**

```json
{
  "items": [],
  "total": 0
}
```

---

## API 26. Get User History

### Endpoint Information

- **Method:** `GET`
- **Path:** `/api/v1/users/me/history`
- **Description:** Return current user's reviews and restaurants added

### Request Details

- **Headers:** `Authorization: Bearer USER_JWT`
- **Request Body:** None

### Test Cases

| Test Case ID | Scenario | Input | Expected Result |
|---|---|---|---|
| HIST-001 | ✅ Get user history | Valid user token | `200 OK`; returns `my_reviews` and `my_restaurants_added` |
| HIST-002 | ⚠️ New user with no history | Fresh user | `200 OK`; both arrays empty |
| HIST-003 | 🔐 Missing token | No Authorization header | `401 Unauthorized` |
| HIST-004 | 🔐 Wrong token type | Owner token | `401 Unauthorized` |

### Expected Result

- **Status Code:** `200 OK`
- **Response JSON:**

```json
{
  "my_reviews": [],
  "my_restaurants_added": []
}
```

---

## API 27. Get Owner Profile

### Endpoint Information

- **Method:** `GET`
- **Path:** `/api/v1/owners/me`
- **Description:** Get current owner profile

### Request Details

- **Headers:** `Authorization: Bearer OWNER_JWT`
- **Request Body:** None

### Test Cases

| Test Case ID | Scenario | Input | Expected Result |
|---|---|---|---|
| OWN-001 | ✅ Get current owner | Valid owner token | `200 OK`; returns owner profile |
| OWN-002 | 🔐 Missing token | No Authorization header | `401 Unauthorized` |
| OWN-003 | 🔐 Wrong token type | User token | `401 Unauthorized` |

### Expected Result

- **Status Code:** `200 OK`
- **Response JSON:**

```json
{
  "id": 1,
  "name": "QA Owner One",
  "email": "qa_owner_one@example.com",
  "restaurant_location": "San Jose, CA"
}
```

---

## API 28. Update Owner Profile

### Endpoint Information

- **Method:** `PUT`
- **Path:** `/api/v1/owners/me`
- **Description:** Update current owner profile

### Request Details

- **Headers:** `Authorization: Bearer OWNER_JWT`, `Content-Type: application/json`
- **Request Body Example:**

```json
{
  "name": "QA Owner One Updated",
  "restaurant_location": "Santa Clara, CA"
}
```

### Test Cases

| Test Case ID | Scenario | Input | Expected Result |
|---|---|---|---|
| OWN-004 | ✅ Update owner profile | Valid payload | `200 OK`; owner profile updated |
| OWN-005 | ⚠️ Partial update | Send only one field | `200 OK` |
| OWN-006 | ❌ Empty required value style case | Blank string for `name` or `restaurant_location` | `422 Unprocessable Entity` or validation failure |
| OWN-007 | 🔐 Missing token | No Authorization header | `401 Unauthorized` |

### Expected Result

- **Status Code:** `200 OK`
- **Response JSON:** Same structure as API 27 with updated values

---

## API 29. Create Restaurant (Owner)

### Endpoint Information

- **Method:** `POST`
- **Path:** `/api/v1/owner/restaurants`
- **Description:** Create a restaurant listing as an owner

### Request Details

- **Headers:** `Authorization: Bearer OWNER_JWT`, `Content-Type: application/json`
- **Request Body Example:** Same JSON structure as API 15

```json
{
  "name": "Owner QA Grill",
  "cuisine_type": "American",
  "description": "Owner-created test restaurant.",
  "street": "456 Owner Ave",
  "city": "San Jose",
  "state": "CA",
  "zip_code": "95113",
  "country": "USA",
  "phone": "4085551234",
  "email": "ownergrill@example.com",
  "hours_json": {
    "Fri": "11am-10pm"
  },
  "pricing_tier": "$$$",
  "amenities": ["Parking", "Family Friendly"]
}
```

### Test Cases

| Test Case ID | Scenario | Input | Expected Result |
|---|---|---|---|
| OWN-R-001 | ✅ Owner creates restaurant | Valid owner payload | `201 Created`; restaurant returned |
| OWN-R-002 | ❌ Missing required fields | Omit `name` or `city` | `422 Unprocessable Entity` |
| OWN-R-003 | 🔐 Missing owner token | No Authorization header | `401 Unauthorized` |
| OWN-R-004 | 🔐 Wrong token type | User token | `401 Unauthorized` |

### Expected Result

- **Status Code:** `201 Created`
- **Response JSON:** Same structure as API 15

---

## API 30. Update Claimed Restaurant

### Endpoint Information

- **Method:** `PUT`
- **Path:** `/api/v1/owner/restaurants/{restaurant_id}`
- **Description:** Update a restaurant claimed by the current owner

### Request Details

- **Headers:** `Authorization: Bearer OWNER_JWT`, `Content-Type: application/json`
- **Path Parameters:** `restaurant_id`
- **Request Body Example:**

```json
{
  "description": "Updated owner description.",
  "pricing_tier": "$$",
  "amenities": ["WiFi", "Patio"]
}
```

### Test Cases

| Test Case ID | Scenario | Input | Expected Result |
|---|---|---|---|
| OWN-R-005 | ✅ Update claimed restaurant | Owner updates own claimed restaurant | `200 OK` |
| OWN-R-006 | ❌ Update unclaimed or other owner's restaurant | Not owned by current owner | `403 Forbidden` |
| OWN-R-007 | ❌ Non-existing restaurant | Invalid `restaurant_id` | `404 Not Found` |
| OWN-R-008 | ❌ Invalid pricing tier | `pricing_tier: "$$$$$"` | `422 Unprocessable Entity` |
| OWN-R-009 | 🔐 Missing token | No Authorization header | `401 Unauthorized` |

### Expected Result

- **Status Code:** `200 OK`
- **Response JSON:** Restaurant detail object with updated fields

---

## API 31. Claim Restaurant

### Endpoint Information

- **Method:** `POST`
- **Path:** `/api/v1/owner/restaurants/{restaurant_id}/claim`
- **Description:** Claim an unclaimed restaurant as owner

### Request Details

- **Headers:** `Authorization: Bearer OWNER_JWT`
- **Path Parameters:** `restaurant_id`
- **Request Body:** None

### Test Cases

| Test Case ID | Scenario | Input | Expected Result |
|---|---|---|---|
| OWN-R-010 | ✅ Claim unclaimed restaurant | `CLAIMABLE_RESTAURANT_ID` | `200 OK`; claim success message |
| OWN-R-011 | ❌ Claim already claimed restaurant | `CLAIMED_BY_OTHER_OWNER_ID` | `409 Conflict` |
| OWN-R-012 | ❌ Invalid restaurant ID | Non-existing `restaurant_id` | `404 Not Found` |
| OWN-R-013 | 🔐 Missing token | No Authorization header | `401 Unauthorized` |
| OWN-R-014 | 🔐 Wrong token type | User token | `401 Unauthorized` |

### Expected Result

- **Status Code:** `200 OK`
- **Response JSON:**

```json
{
  "restaurant_id": 1,
  "claimed_by_owner_id": 1,
  "message": "Restaurant claimed successfully."
}
```

---

## API 32. List Reviews for Claimed Restaurant

### Endpoint Information

- **Method:** `GET`
- **Path:** `/api/v1/owner/restaurants/{restaurant_id}/reviews`
- **Description:** Owner-only review list for a claimed restaurant

### Request Details

- **Headers:** `Authorization: Bearer OWNER_JWT`
- **Path Parameters:** `restaurant_id`
- **Query Parameters:** `page`, `limit`
- **Request Body:** None

### Test Cases

| Test Case ID | Scenario | Input | Expected Result |
|---|---|---|---|
| OWN-R-015 | ✅ View reviews for claimed restaurant | Valid claimed restaurant ID | `200 OK` |
| OWN-R-016 | ❌ View reviews for restaurant not claimed by current owner | Other owner's restaurant | `403 Forbidden` |
| OWN-R-017 | ❌ Non-existing restaurant | Invalid `restaurant_id` | `404 Not Found` |
| OWN-R-018 | ❌ Invalid pagination values | `page=0` or `limit=1000` | `422 Unprocessable Entity` |
| OWN-R-019 | 🔐 Missing token | No Authorization header | `401 Unauthorized` |

### Expected Result

- **Status Code:** `200 OK`
- **Response JSON:** Paginated review data for that restaurant

---

## API 33. Owner Dashboard

### Endpoint Information

- **Method:** `GET`
- **Path:** `/api/v1/owner/dashboard`
- **Description:** Owner analytics summary across claimed restaurants

### Request Details

- **Headers:** `Authorization: Bearer OWNER_JWT`
- **Request Body:** None

### Test Cases

| Test Case ID | Scenario | Input | Expected Result |
|---|---|---|---|
| OWN-R-020 | ✅ Get owner dashboard | Valid owner token | `200 OK`; returns claimed count, reviews, average rating, rating distribution, restaurant cards |
| OWN-R-021 | ⚠️ New owner with no claimed restaurants | Owner with no restaurants | `200 OK`; counts should be zero and list empty |
| OWN-R-022 | 🔐 Missing token | No Authorization header | `401 Unauthorized` |
| OWN-R-023 | 🔐 Wrong token type | User token | `401 Unauthorized` |

### Expected Result

- **Status Code:** `200 OK`
- **Response JSON:**

```json
{
  "claimed_count": 0,
  "total_reviews": 0,
  "avg_rating": 0,
  "rating_distribution": {
    "1": 0,
    "2": 0,
    "3": 0,
    "4": 0,
    "5": 0
  },
  "claimed_restaurants": []
}
```

---

## API 34. AI Assistant Chat

### Endpoint Information

- **Method:** `POST`
- **Path:** `/api/v1/ai-assistant/chat`
- **Description:** Authenticated AI assistant chat for restaurant recommendations

### Request Details

- **Headers:** `Authorization: Bearer USER_JWT`, `Content-Type: application/json`
- **Request Body Example:**

```json
{
  "message": "Find me a quiet Italian restaurant in San Jose under $$",
  "conversation_history": [
    {
      "role": "user",
      "content": "I want Italian food tonight."
    },
    {
      "role": "assistant",
      "content": "I can help with that. Do you have a location or budget in mind?"
    }
  ]
}
```

### Test Cases

| Test Case ID | Scenario | Input | Expected Result |
|---|---|---|---|
| AI-001 | ✅ Valid recommendation request | Valid message and valid user token | `200 OK`; returns `reply` and `suggested_restaurants` |
| AI-002 | ✅ Valid follow-up conversation | Message asks about prior suggestion with conversation history | `200 OK`; follow-up response returned |
| AI-003 | ❌ Empty message | Empty string | `422 Unprocessable Entity` or `400 Bad Request` depending on payload |
| AI-004 | ❌ Invalid role in conversation history | `role: "system"` | `422 Unprocessable Entity` |
| AI-005 | ⚠️ No strong match found | Very narrow or impossible query | `200 OK`; reply may ask user to refine search and suggestions may be empty |
| AI-006 | 🔐 Missing token | No Authorization header | `401 Unauthorized` |
| AI-007 | 🔐 Wrong token type | Owner token | `401 Unauthorized` |

### Expected Result

- **Status Code:** `200 OK`
- **Response JSON:**

```json
{
  "reply": "Here are a few restaurants that match your request.",
  "suggested_restaurants": [
    {
      "id": 1,
      "name": "Sample Restaurant",
      "reason": "Matches your cuisine request; Rated 4.5★ from 10 review(s)",
      "average_rating": 4.5,
      "pricing_tier": "$$",
      "cuisine_type": "Italian",
      "city": "San Jose"
    }
  ]
}
```

---

## 4. Final QA Notes

- Use Swagger UI's **Authorize** button for JWT-protected routes.
- Maintain separate user and owner tokens during testing.
- For file upload endpoints, use Swagger's multipart file chooser instead of JSON.
- For duplicate/conflict tests, first create the record successfully, then repeat the same request.
- For forbidden tests, log in as a different user or owner before retrying the request.

---

## 5. Recommended Manual Execution Order

1. Health checks
2. User signup/login
3. Owner signup/login
4. User profile and preferences
5. Create restaurant as user
6. Search and get restaurant details
7. Upload restaurant photos
8. Review CRUD
9. Favorites and history
10. Owner claim/create/update/dashboard flows
11. AI assistant chat

---

## 6. End of Document

**Document Title:** API Test Case Document
