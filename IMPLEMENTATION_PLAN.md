# Yelp-Style Platform — Full Implementation Plan
### Stack: React + FastAPI + MySQL + LangChain + Tavily
### For: Junior Developer Reference (Phase-by-Phase)

---

## ⚠️ GOLDEN RULES — READ BEFORE YOU START

1. **One phase at a time.** Do not touch the next phase until the current one fully passes its checklist.
2. Every phase must have: backend endpoints complete + frontend integrated + validation/errors handled + Swagger tested.
3. **Never commit secrets.** No `.env`, `venv/`, `__pycache__/`, or API keys in the repo.
4. Use meaningful commit messages:
   - `feat(auth): add user signup/login`
   - `fix(reviews): enforce review ownership`
5. **No DB logic inside route handlers.** All DB access and business rules go in `services/`.

---

## PROJECT OVERVIEW

A Yelp-style restaurant discovery + review platform with:
- **User (Reviewer)** — browse, search, review, favorite restaurants
- **Restaurant Owner** — post/claim/manage restaurant listings, view analytics
- **AI Assistant Chatbot** — natural language restaurant recommendations

---

## REPO STRUCTURE

```
root/
├── backend/          # FastAPI app
├── frontend/         # React app (Vite)
├── docs/             # Postman collection, extra docs
├── .gitignore        # must include .env, venv/, __pycache__/
└── README.md
```

**Branch strategy:**
- `main` — stable/production only
- `dev` — integration branch
- `feature/<name>` — feature branches (always branch from `dev`)

---

---

# PHASE 0 — Project Setup

**Goal:** Get the skeleton running locally. No features yet, just infrastructure.

---

## 0.1 Backend Bootstrap (FastAPI)

**Folder structure inside `backend/`:**

```
backend/
├── app/
│   ├── main.py               # FastAPI app entry point
│   ├── core/
│   │   ├── config.py         # reads .env via pydantic Settings
│   │   └── security.py       # JWT encode/decode, bcrypt helpers
│   ├── db/
│   │   └── session.py        # SQLAlchemy engine + SessionLocal
│   ├── models/               # SQLAlchemy ORM models (one file per table/group)
│   ├── schemas/              # Pydantic request/response DTOs
│   ├── api/
│   │   └── routes/           # FastAPI routers
│   └── services/             # Business logic (called by routes)
├── alembic/                  # DB migrations
├── requirements.txt
└── .env.example
```

**`requirements.txt` (minimum):**
```
fastapi
uvicorn[standard]
sqlalchemy
pymysql
alembic
pydantic[email]
pydantic-settings
python-jose[cryptography]
passlib[bcrypt]
python-multipart
langchain
tavily-python
```

**`app/main.py` — CORS + health check:**
```python
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173"],  # Vite default
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.get("/health")
def health():
    return {"status": "ok"}
```

**`.env.example` (commit this, NOT `.env`):**
```
DATABASE_URL=mysql+pymysql://user:password@localhost:3306/yelp_db
JWT_SECRET=your-secret-here
JWT_ALGORITHM=HS256
ACCESS_TOKEN_EXPIRE_MINUTES=60
TAVILY_API_KEY=your-tavily-key-here

# LLM Provider (used in Phase 7 — AI Assistant)
LLM_PROVIDER=openai              # options: openai | anthropic
OPENAI_API_KEY=your-openai-key-here
OPENAI_MODEL=gpt-4o-mini         # or gpt-4o, gpt-3.5-turbo, etc.
# If using Anthropic instead:
# ANTHROPIC_API_KEY=your-anthropic-key-here
# ANTHROPIC_MODEL=claude-3-haiku-20240307
```

---

## 0.2 Database Bootstrap (MySQL)

- Run MySQL locally (Docker recommended):
  ```bash
  docker run --name mysql-yelp -e MYSQL_ROOT_PASSWORD=root -e MYSQL_DATABASE=yelp_db -p 3306:3306 -d mysql:8
  ```
- Set up Alembic: `alembic init alembic`
- Connect `alembic/env.py` to your `DATABASE_URL` from settings.
- Confirm connection via `/health` or a `/db-check` route.

---

## 0.3 Frontend Bootstrap (React + Vite)

```bash
npm create vite@latest frontend -- --template react
cd frontend
npm install axios react-router-dom
npm install -D tailwindcss postcss autoprefixer
npx tailwindcss init -p
```

**Page routing skeleton (`App.jsx`):**
- `/` — Explore/Search (public)
- `/restaurant/:id` — Restaurant Details (public)
- `/login` — User Login
- `/signup` — User Signup
- `/owner/login` — Owner Login
- `/owner/signup` — Owner Signup
- `/profile` — User Profile (protected)
- `/preferences` — User Preferences (protected)
- `/add-restaurant` — Add Restaurant (protected)

Add a **Navbar** with links: Explore | Login | Signup | Profile (when logged in).

---

## Phase 0 Acceptance Checklist

- [ ] `uvicorn app.main:app --reload` starts without errors
- [ ] `GET /health` returns `{"status": "ok"}`
- [ ] Frontend starts with `npm run dev` and shows a home page
- [ ] Backend connects to MySQL without errors
- [ ] Swagger UI available at `http://localhost:8000/docs`
- [ ] No secrets committed (only `.env.example`)

---

---

# PHASE 1 — Authentication (User + Owner)

**Goal:** Secure signup/login for both personas using bcrypt + JWT.

---

## 1.1 Database Tables

Create SQLAlchemy models + Alembic migration.

**`users` table:**
| Column | Type | Notes |
|--------|------|-------|
| id | INT PK AUTO_INCREMENT | |
| name | VARCHAR(100) | required |
| email | VARCHAR(255) UNIQUE | required |
| password_hash | TEXT | bcrypt hash |
| created_at | DATETIME | server default |
| updated_at | DATETIME | auto-update |

**`owners` table:**
| Column | Type | Notes |
|--------|------|-------|
| id | INT PK AUTO_INCREMENT | |
| name | VARCHAR(100) | required |
| email | VARCHAR(255) UNIQUE | required |
| password_hash | TEXT | bcrypt hash |
| restaurant_location | VARCHAR(255) | required |
| created_at | DATETIME | server default |
| updated_at | DATETIME | auto-update |

---

## 1.2 Security Utilities (`app/core/security.py`)

```python
from passlib.context import CryptContext
from jose import jwt
from datetime import datetime, timedelta

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

def hash_password(plain: str) -> str:
    return pwd_context.hash(plain)

def verify_password(plain: str, hashed: str) -> bool:
    return pwd_context.verify(plain, hashed)

def create_access_token(data: dict, expires_minutes: int) -> str:
    expire = datetime.utcnow() + timedelta(minutes=expires_minutes)
    return jwt.encode({**data, "exp": expire}, SECRET_KEY, algorithm=ALGORITHM)
```

---

## 1.3 API Endpoints

| Method | Path | Auth | Description |
|--------|------|------|-------------|
| POST | `/auth/user/signup` | None | Register a new user |
| POST | `/auth/user/login` | None | Login, returns JWT |
| POST | `/auth/owner/signup` | None | Register a new owner |
| POST | `/auth/owner/login` | None | Login, returns JWT |
| GET | `/users/me` | User JWT | Returns current user info |
| GET | `/owners/me` | Owner JWT | Returns current owner info |

**Response for login:**
```json
{ "access_token": "...", "token_type": "bearer" }
```

**Create dependency functions:**
- `get_current_user(token)` — decodes JWT, returns user from DB
- `get_current_owner(token)` — decodes JWT, returns owner from DB

---

## 1.4 Frontend Pages

Pages to build (with form validation + error display):
- `/signup` — name, email, password fields
- `/login` — email, password fields
- `/owner/signup` — name, email, password, restaurant_location
- `/owner/login` — email, password

**Token storage:** Store JWT in `localStorage` (acceptable for prototype). Create an `axios` instance with the token injected via interceptor.

**After login:** Redirect to `/` or `/profile`.

**Logout:** No backend endpoint needed for JWT-based auth. Logout = remove the token from `localStorage` on the frontend and redirect to `/login`. Add a "Logout" button in the Navbar when the user is logged in.

---

## Phase 1 Acceptance Checklist

- [ ] Passwords stored as bcrypt hashes — never plaintext in DB
- [ ] Duplicate emails return a clean 409 error (not 500)
- [ ] Wrong password returns 401 with a clear message
- [ ] `GET /users/me` without token returns 401
- [ ] `GET /users/me` with valid token returns user data
- [ ] Both user and owner flows work end-to-end

---

---

# PHASE 2 — User Profile + Preferences

**Goal:** Users can view/edit their profile, upload a profile picture, and save food preferences.

---

## 2.1 Database Tables

**`user_profiles` table** (separate from `users`):
| Column | Type |
|--------|------|
| id | INT PK |
| user_id | INT FK → users.id (unique) |
| phone | VARCHAR(20) |
| about_me | TEXT |
| city | VARCHAR(100) |
| state | CHAR(2) — uppercase abbreviated, e.g. "CA" |
| country | VARCHAR(100) |
| languages | JSON array |
| gender | VARCHAR(20) |
| profile_picture_url | VARCHAR(500) |

**`user_preferences` table:**
| Column | Type |
|--------|------|
| id | INT PK |
| user_id | INT FK → users.id (unique) |
| cuisine_preferences | JSON array |
| price_range | VARCHAR(10) — "$", "$$", "$$$", "$$$$" |
| preferred_locations | JSON array |
| search_radius_km | FLOAT |
| dietary_restrictions | JSON array |
| ambiance_preferences | JSON array |
| sort_preference | VARCHAR(20) — "rating", "distance", "popularity", "price" |

---

## 2.2 API Endpoints

| Method | Path | Auth | Description |
|--------|------|------|-------------|
| GET | `/users/me` | User JWT | Returns user + profile data |
| PUT | `/users/me` | User JWT | Update profile fields |
| POST | `/users/me/profile-picture` | User JWT | Upload profile photo (multipart) |
| GET | `/users/me/preferences` | User JWT | Get preferences |
| PUT | `/users/me/preferences` | User JWT | Save preferences |

**File upload rules:**
- Accept: `image/jpeg`, `image/png`, `image/webp`
- Max size: 5MB
- Save to `backend/static/uploads/` (prototype) or S3
- Return the public URL in the response

**Validation:**
- `state` must be 2 uppercase letters if provided
- `country` must be from a valid list (enforce on frontend dropdown; validate on backend too)
- Email uniqueness check if user tries to change email

---

## 2.3 Frontend Pages

**Profile Editor page (`/profile`):**
- Show current values pre-filled
- Fields: name, email, phone, about me, city, state, country, languages, gender
- Profile picture upload with preview
- Save button

**Preferences Editor page (`/preferences`):**
- Cuisine multi-select (e.g. Italian, Mexican, Japanese...)
- Price range dropdown
- Dietary restrictions multi-select (e.g. Vegan, Halal, Gluten-free...)
- Ambiance multi-select (e.g. Romantic, Casual, Outdoor...)
- Sort preference dropdown
- Location + radius input

---

## Phase 2 Acceptance Checklist

- [ ] `GET /users/me` returns merged user + profile data
- [ ] `PUT /users/me` updates correctly and reloads on frontend
- [ ] Profile picture uploads, saves, and displays correctly
- [ ] Country dropdown is enforced; invalid country rejected
- [ ] Preferences save and reload without data loss

---

---

# PHASE 3 — Restaurant Listings (Create + Search + Details)

**Goal:** Users can add restaurant listings. Anyone can search and view restaurant details.

---

## 3.1 Database Tables

**`restaurants` table:**
| Column | Type | Notes |
|--------|------|-------|
| id | INT PK AUTO_INCREMENT | |
| name | VARCHAR(200) | required |
| cuisine_type | VARCHAR(100) | |
| description | TEXT | |
| street | VARCHAR(255) | |
| city | VARCHAR(100) | required |
| state | VARCHAR(50) | |
| zip | VARCHAR(20) | |
| country | VARCHAR(100) | |
| latitude | FLOAT | optional |
| longitude | FLOAT | optional |
| phone | VARCHAR(30) | |
| email | VARCHAR(255) | |
| hours_json | JSON | e.g. `{"Mon": "9am-10pm", ...}` |
| pricing_tier | VARCHAR(10) | "$" to "$$$$" |
| amenities | JSON | e.g. `["WiFi", "Outdoor Seating", "Parking", "Wheelchair Accessible"]` |
| created_by_user_id | INT FK → users.id | nullable |
| claimed_by_owner_id | INT FK → owners.id | nullable |
| created_at | DATETIME | |
| updated_at | DATETIME | |

**`restaurant_photos` table:**
| Column | Type | Notes |
|--------|------|-------|
| id | INT PK AUTO_INCREMENT | |
| restaurant_id | INT FK → restaurants.id | |
| photo_url | VARCHAR(500) | |
| uploaded_by_user_id | INT FK → users.id | nullable |
| uploaded_by_owner_id | INT FK → owners.id | nullable |
| created_at | DATETIME | |

> ⚠️ **Note:** The `amenities` field is referenced in Phase 6 (owner listing) and Phase 7 (AI search). It must be created here in Phase 3 so those phases can rely on it.

---

## 3.2 API Endpoints

| Method | Path | Auth | Description |
|--------|------|------|-------------|
| POST | `/restaurants` | User JWT | Create a new listing |
| GET | `/restaurants` | None | Search with filters |
| GET | `/restaurants/{id}` | None | Get restaurant details |
| POST | `/restaurants/{id}/photos` | User OR Owner JWT | Upload photos (multipart, max 5) |

> **Auth rule for photo uploads:** The endpoint accepts either a User JWT (if they created the listing) or an Owner JWT (if they have claimed the restaurant). The service layer must check which token type was provided and set `uploaded_by_user_id` or `uploaded_by_owner_id` accordingly. Reject if neither condition is met (403).

**Search query params for `GET /restaurants`:**
- `name` (string)
- `cuisine` (string)
- `keywords` (string — matches against: name, description, **and amenities**)
- `city` (string)
- `zip` (string)
- `sort` — `rating`, `review_count`, `name`
- `page`, `limit` for pagination

**MVP search:** SQL `LIKE` queries are acceptable. For `keywords`, run the `LIKE` check against `name`, `description`, and the `amenities` JSON column (use `JSON_SEARCH` or cast to string).

> Example: searching `"wifi"` should match any restaurant with `"WiFi"` in its amenities array.

---

## 3.3 Frontend Pages

**Explore/Search page (`/`):**
- Filter bar: name, cuisine, keywords, city/zip, sort dropdown
- Restaurant cards showing: name, cuisine, city, avg rating, review count, price tier
- Clicking a card → Restaurant Details page

**Restaurant Details page (`/restaurant/:id`):**
- Full info: name, description, address, hours, phone, email, pricing
- Avg rating + review count (placeholder text if no reviews yet)
- Photos section (optional for now)
- "Write a Review" button (if user logged in)

**Add Restaurant page (`/add-restaurant`):**
- Form: name, cuisine, description, street, city, state, zip, country, phone, email, hours, pricing tier
- Amenities multi-select (e.g. WiFi, Outdoor Seating, Parking, Wheelchair Accessible, Reservations...)
- Photo upload (up to 5 images, stored via `POST /restaurants/{id}/photos`)
- Protected — user must be logged in

---

## Phase 3 Acceptance Checklist

- [ ] Logged-in user can create a restaurant listing
- [ ] `amenities` JSON field saves and returns correctly
- [ ] Photos upload and display on the restaurant details page
- [ ] Explore search filters work (name, cuisine, city, zip, keywords)
- [ ] Restaurant details page shows all fields correctly (incl. amenities, hours, pricing)
- [ ] Validation errors shown user-friendly (not raw 422s)

---

---

# PHASE 4 — Reviews (Add / Edit / Delete + Rating Aggregation)

**Goal:** Users can write, edit, and delete their own reviews. Restaurant pages show aggregated ratings.

---

## 4.1 Database Tables

**`reviews` table:**
| Column | Type | Notes |
|--------|------|-------|
| id | INT PK AUTO_INCREMENT | |
| restaurant_id | INT FK → restaurants.id | required |
| user_id | INT FK → users.id | required |
| rating | TINYINT | 1–5, required |
| comment | TEXT | |
| created_at | DATETIME | server-generated, not user input |
| updated_at | DATETIME | |

**Constraint:** One review per user per restaurant (enforce at DB level with UNIQUE constraint on `(restaurant_id, user_id)`).

---

## 4.2 API Endpoints

| Method | Path | Auth | Description |
|--------|------|------|-------------|
| POST | `/restaurants/{id}/reviews` | User JWT | Create a review |
| GET | `/restaurants/{id}/reviews` | None | List all reviews for a restaurant |
| PUT | `/reviews/{id}` | User JWT (owner only) | Edit own review |
| DELETE | `/reviews/{id}` | User JWT (owner only) | Delete own review |

**Authorization rule:** On PUT/DELETE, check `review.user_id == current_user.id`. Return 403 if not.

**Required response shape for `GET /restaurants/{id}/reviews`:**
```json
[
  {
    "id": 5,
    "rating": 4,
    "comment": "Great food and atmosphere!",
    "user_name": "Jane D.",
    "created_at": "2025-11-03T14:22:00Z",
    "updated_at": "2025-11-03T14:22:00Z"
  }
]
```
> ⚠️ `user_name` must be joined from the `users` table — do not expose `user_id` alone. The frontend relies on this to display the reviewer's name and post date.

---

## 4.3 Rating Aggregation

On `GET /restaurants/{id}`, compute and return:
```json
{
  "average_rating": 4.2,
  "review_count": 38,
  ...
}
```
Use a SQL aggregate query (`AVG`, `COUNT`) — do not store a cached field for the prototype.

---

## 4.4 Frontend

**On Restaurant Details page:**
- Show list of reviews: reviewer name, star rating, comment, date
- Show "Edit" and "Delete" buttons only on the logged-in user's own reviews
- Show average rating as stars + numeric score

**Write/Edit Review:**
- Star selector (1–5)
- Comment textarea
- Submit button

---

## Phase 4 Acceptance Checklist

- [ ] Review appears on restaurant page immediately after creation
- [ ] Users can only edit/delete their own reviews (403 otherwise)
- [ ] Average rating and count update correctly after add/edit/delete
- [ ] Server generates `created_at` — not accepted from the client
- [ ] Duplicate review from same user returns a clean error

---

---

# PHASE 5 — Favorites + User History

**Goal:** Users can favorite restaurants and view their activity history.

---

## 5.1 Database Tables

**`favorites` table:**
| Column | Type | Notes |
|--------|------|-------|
| id | INT PK | |
| user_id | INT FK → users.id | |
| restaurant_id | INT FK → restaurants.id | |
| created_at | DATETIME | |

Add UNIQUE constraint on `(user_id, restaurant_id)` to prevent duplicates.

History is derived — no extra table needed:
- My Reviews = `reviews WHERE user_id = me`
- My Added Restaurants = `restaurants WHERE created_by_user_id = me`

---

## 5.2 API Endpoints

| Method | Path | Auth | Description |
|--------|------|------|-------------|
| POST | `/favorites/{restaurant_id}` | User JWT | Favorite a restaurant |
| DELETE | `/favorites/{restaurant_id}` | User JWT | Unfavorite |
| GET | `/users/me/favorites` | User JWT | List favorited restaurants |
| GET | `/users/me/history` | User JWT | Returns `{my_reviews, my_restaurants_added}` |

---

## 5.3 Frontend

- ❤️ Favorite toggle button on restaurant cards and detail pages
- **Dashboard page (`/dashboard`)** with tabs:
  - **Favorites** tab — grid of favorited restaurants
  - **History** tab — list of reviews written + restaurants added

---

## Phase 5 Acceptance Checklist

- [ ] Favorite persists after page refresh and appears in Favorites tab
- [ ] Unfavoriting removes it correctly
- [ ] No duplicate favorites (DB constraint + clean error)
- [ ] History tab shows correct reviews and added restaurants

---

---

# PHASE 6 — Owner Features

**Goal:** Owners can manage their own restaurant listings, claim unlisted ones, and view a read-only review dashboard.

---

## 6.1 API Endpoints

**Owner profile:**
| Method | Path | Auth |
|--------|------|------|
| GET | `/owners/me` | Owner JWT |
| PUT | `/owners/me` | Owner JWT |

**Restaurant management:**
| Method | Path | Auth | Description |
|--------|------|------|-------------|
| POST | `/owner/restaurants` | Owner JWT | Create new listing as owner |
| PUT | `/owner/restaurants/{id}` | Owner JWT | Edit (only if they own it) |
| POST | `/owner/restaurants/{id}/claim` | Owner JWT | Claim an existing listing |

**Claim rules:**
- If `claimed_by_owner_id` is null → allow claim
- If already claimed by another owner → return 409

**Reviews (read-only for owners):**
| Method | Path | Auth |
|--------|------|------|
| GET | `/owner/restaurants/{id}/reviews` | Owner JWT |

**Dashboard:**
| Method | Path | Auth |
|--------|------|------|
| GET | `/owner/dashboard` | Owner JWT |

Dashboard response shape:
```json
{
  "owned_restaurants": [...],
  "recent_reviews": [...],
  "rating_distribution": { "1": 2, "2": 5, "3": 10, "4": 18, "5": 22 },
  "total_reviews": 57
}
```

---

## 6.2 Frontend Pages

- **Owner Profile** (`/owner/profile`) — edit name, email, location
- **My Restaurants** (`/owner/restaurants`) — list of claimed/created restaurants
- **Edit Restaurant** (`/owner/restaurants/:id/edit`) — full edit form
- **Reviews Dashboard** (`/owner/restaurants/:id/reviews`) — read-only review list
- **Analytics Dashboard** (`/owner/dashboard`) — stats overview

---

## Phase 6 Acceptance Checklist

- [ ] Owner can claim an unclaimed restaurant
- [ ] Claiming an already-claimed restaurant returns a clear error
- [ ] Owner can edit only their own restaurants (403 otherwise)
- [ ] Owner can view reviews but cannot edit or delete them
- [ ] Dashboard returns correct stats and recent reviews

---

---

# PHASE 7 — AI Assistant Chatbot

**Goal:** A conversational chatbot that recommends restaurants using the user's preferences + DB data + live web context (Tavily).

---

## 7.1 Architecture

```
User message
    ↓
POST /ai-assistant/chat
    ↓
[Load user preferences from DB]
    ↓
[Search restaurants in DB matching query + preferences]
    ↓
[Use Tavily to get live context: hours changes, events, trending]
    ↓
[LangChain prompt with context → Claude/GPT]
    ↓
Response with ranked recommendations + reasoning
```

---

## 7.2 API Endpoint

**`POST /ai-assistant/chat`** — **Auth: User JWT required**

> **Why required:** The chatbot loads saved user preferences (cuisine, dietary, ambiance, price range) at the start of every request to personalize recommendations. Without a valid User JWT, there is no way to securely identify which user's preferences to load. Do not accept `user_id` as a request body field — that would be insecure.
>
> If you want a public demo mode in the future, create a separate `/ai-assistant/chat/guest` endpoint that uses generic default preferences instead.

Request body:
```json
{
  "message": "Find me a romantic Italian restaurant near downtown under $$",
  "conversation_history": [
    { "role": "user", "content": "..." },
    { "role": "assistant", "content": "..." }
  ]
}
```

Response:
```json
{
  "reply": "Based on your preferences for Italian and a casual ambiance, here are my top picks...",
  "suggested_restaurants": [
    { "id": 12, "name": "Trattoria Roma", "reason": "4.7 stars, matches your $$ preference" }
  ]
}
```

---

## 7.3 Implementation Notes

- **LLM provider must be configurable via env vars — never hardcode the model or API key.** Read `LLM_PROVIDER`, `OPENAI_API_KEY`, and `OPENAI_MODEL` (or Anthropic equivalents) from settings. This lets you swap models without touching code.
- Load `user_preferences` from DB at the start of each chat call (user JWT is required, so preferences are always available).
- Query `restaurants` table with filters matching the message intent.
- Use **Tavily** to supplement: search for `"{restaurant name} hours"` or `"best Italian restaurants in {city} 2024"`.
- Use LangChain to build the prompt chain:
  - System prompt: "You are a restaurant recommendation assistant. Use the provided restaurant data and user preferences to give helpful, personalized recommendations."
  - Inject: user preferences, matched restaurants, Tavily results, conversation history.
- Multi-turn: Pass full `conversation_history` each call — the model has no memory between calls.

---

## 7.4 Frontend

- Chat widget (floating button or sidebar) accessible on Explore and Home pages.
- Shows conversation thread (user + assistant bubbles).
- Typing indicator while waiting for response.
- Clicking a recommended restaurant card navigates to its detail page.

---

## Phase 7 Acceptance Checklist

- [ ] `/ai-assistant/chat` requires User JWT — returns 401 without token
- [ ] LLM provider, API key, and model are loaded from env vars (not hardcoded)
- [ ] Chat responds with relevant restaurant suggestions
- [ ] User preferences are reflected in recommendations
- [ ] Multi-turn conversation works (context maintained)
- [ ] Tavily enriches responses with live context
- [ ] Chat UI is accessible and easy to use

---

---

# PHASE 8 — Documentation, Testing & Final Polish (MANDATORY)

**Goal:** Make the project submission-ready: complete documentation, stable UX, responsive UI, accessibility basics, and basic tests.

---

## 8.1 API Documentation (Choose ONE)

**Option A (Recommended): Swagger**
- All endpoints visible and testable at `/docs`
- Request/response schemas fully defined via Pydantic
- Auth header usage documented in the Swagger UI
- Example payloads included in schema descriptions

**Option B: Postman**
- Export Postman collection to `docs/postman_collection.json`
- Each request has a description + sample response body
- Auth token instructions included in the collection readme

---

## 8.2 Backend Quality Improvements

**Consistent error format** — every error response must look like:
```json
{ "detail": "Human readable message here" }
```

**Correct HTTP status codes:**
| Code | When to use |
|------|-------------|
| 400 | Bad/malformed input |
| 401 | Not authenticated (no/invalid token) |
| 403 | Authenticated but not authorized |
| 404 | Resource not found |
| 409 | Conflict (duplicate email, already claimed, etc.) |
| 422 | Pydantic validation failure |
| 500 | Unexpected server error |

**Pagination** — add `page` and `limit` query params to:
- `GET /restaurants`
- `GET /restaurants/{id}/reviews`

**DB Indexes to add via Alembic migration:**
- UNIQUE index on `users.email` and `owners.email`
- Index on `restaurants.name`, `restaurants.city`, `restaurants.cuisine_type`
- UNIQUE index on `reviews(restaurant_id, user_id)`
- UNIQUE index on `favorites(user_id, restaurant_id)`

---

## 8.3 Frontend Polish

Every page must have:
- **Loading state** — spinner or skeleton while data fetches
- **Empty state** — friendly message when no results (e.g. "No restaurants found. Try a different search.")
- **Error state** — error banner when API call fails

**Responsive design** — verify on all three breakpoints:
- Mobile (≤ 480px)
- Tablet (768px)
- Desktop (1024px+)

**Accessibility basics:**
- Semantic HTML (`<nav>`, `<main>`, `<section>`, `<article>`, `<button>` not `<div onClick>`)
- `alt` text on all images
- All forms and buttons keyboard-navigable (Tab + Enter)
- Sufficient color contrast (aim for WCAG AA)

---

## 8.4 Testing

**Backend minimum tests** (use `pytest`):

```
backend/tests/
├── test_auth.py          # signup/login for user + owner
├── test_reviews.py       # create, edit own, 403 on editing others
└── test_restaurants.py   # create, search filters
```

Key test cases to cover:
- User signup → duplicate email returns 409
- User login → wrong password returns 401
- `PUT /reviews/{id}` by a different user → returns 403
- `GET /restaurants?city=Chicago` → only returns Chicago restaurants

**Frontend smoke test** (manual checklist):

Walk through this full flow without errors before submitting:

1. Sign up as a new User
2. Log in
3. Update profile (name, city, profile picture)
4. Set preferences (cuisine, dietary, ambiance)
5. Browse Explore page — search by city
6. Open a restaurant detail page
7. Write a review (1–5 stars + comment)
8. Edit the review
9. Favorite the restaurant
10. Go to Dashboard → confirm it appears in Favorites tab
11. Go to History tab → confirm review and added restaurant appear
12. Sign up as an Owner
13. Create a restaurant listing (with amenities + photos)
14. Claim an existing restaurant
15. View owner dashboard
16. Open AI chatbot → ask for a recommendation → verify response

---

## 8.5 README Completion

The `README.md` in the repo root must include:

```markdown
## Backend Setup
cd backend
python -m venv venv
source venv/bin/activate  # Windows: venv\Scripts\activate
pip install -r requirements.txt
cp .env.example .env      # then fill in your values
alembic upgrade head
uvicorn app.main:app --reload

## Frontend Setup
cd frontend
npm install
npm run dev

## API Docs
Open http://localhost:8000/docs

## Environment Variables
See .env.example for all required variables and descriptions.
```

---

## Phase 8 Acceptance Checklist

- [ ] Swagger or Postman documentation is complete and all endpoints are testable
- [ ] All pages are responsive on mobile, tablet, and desktop
- [ ] No major console errors in the browser on any page
- [ ] Backend returns clean `{ "detail": "..." }` errors — no raw tracebacks
- [ ] Pagination works for `/restaurants` and `/restaurants/{id}/reviews`
- [ ] DB indexes are applied via Alembic migration
- [ ] Backend tests pass (`pytest`)
- [ ] Manual frontend smoke test completed without errors
- [ ] README contains complete setup + run instructions

---

---

## GENERAL ENGINEERING STANDARDS

### Error Handling Pattern (Backend)
- Always return structured errors: `{ "detail": "message" }`
- Use correct HTTP codes: 400 (bad input), 401 (unauthenticated), 403 (unauthorized), 404 (not found), 409 (conflict), 422 (validation), 500 (server error)
- Never expose stack traces to the frontend in production

### Service Layer Pattern
```python
# ✅ Correct — route just calls service
@router.post("/restaurants")
def create_restaurant(data: RestaurantCreate, db: Session = Depends(get_db), user = Depends(get_current_user)):
    return restaurant_service.create(db, data, user.id)

# ❌ Wrong — DB logic inside route handler
@router.post("/restaurants")
def create_restaurant(data: RestaurantCreate, db: Session = Depends(get_db)):
    restaurant = Restaurant(**data.dict())
    db.add(restaurant)
    db.commit()
    ...
```

### Commit Message Format
```
feat(scope): short description
fix(scope): short description
chore(scope): short description
docs(scope): short description
```
Examples: `feat(auth): add owner login`, `fix(reviews): return 403 on unauthorized delete`

### Environment Variables
- Never hardcode secrets in code
- Always use `pydantic-settings` to load from `.env`
- Every new secret needs a matching entry in `.env.example`

---

## QUICK REFERENCE — All API Endpoints

| Phase | Method | Path | Auth |
|-------|--------|------|------|
| 1 | POST | `/auth/user/signup` | None |
| 1 | POST | `/auth/user/login` | None |
| 1 | POST | `/auth/owner/signup` | None |
| 1 | POST | `/auth/owner/login` | None |
| 2 | GET | `/users/me` | User |
| 2 | PUT | `/users/me` | User |
| 2 | POST | `/users/me/profile-picture` | User |
| 2 | GET | `/users/me/preferences` | User |
| 2 | PUT | `/users/me/preferences` | User |
| 3 | POST | `/restaurants` | User |
| 3 | GET | `/restaurants` | None |
| 3 | GET | `/restaurants/{id}` | None |
| 3 | POST | `/restaurants/{id}/photos` | User OR Owner |
| 4 | POST | `/restaurants/{id}/reviews` | User |
| 4 | GET | `/restaurants/{id}/reviews` | None |
| 4 | PUT | `/reviews/{id}` | User (own only) |
| 4 | DELETE | `/reviews/{id}` | User (own only) |
| 5 | POST | `/favorites/{restaurant_id}` | User |
| 5 | DELETE | `/favorites/{restaurant_id}` | User |
| 5 | GET | `/users/me/favorites` | User |
| 5 | GET | `/users/me/history` | User |
| 6 | GET | `/owners/me` | Owner |
| 6 | PUT | `/owners/me` | Owner |
| 6 | POST | `/owner/restaurants` | Owner |
| 6 | PUT | `/owner/restaurants/{id}` | Owner |
| 6 | POST | `/owner/restaurants/{id}/claim` | Owner |
| 6 | GET | `/owner/restaurants/{id}/reviews` | Owner |
| 6 | GET | `/owner/dashboard` | Owner |
| 7 | POST | `/ai-assistant/chat` | User (required) |

---

*Last updated: February 2026 — v3 (6 spec alignment tweaks applied)*
