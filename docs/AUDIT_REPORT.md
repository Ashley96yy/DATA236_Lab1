# Codebase Audit Report
**Project:** Dine Finder — Yelp-Style Platform
**Plan Reference:** IMPLEMENTATION_PLAN.md v3
**Audit Date:** 2026-02-22
**Auditor:** Claude Code (analysis-only, no modifications made)

---

## Summary Table

| Phase | Title                          | Status            |
|-------|--------------------------------|-------------------|
| 0     | Project Setup                  | Partial           |
| 1     | Authentication (User + Owner)  | Complete          |
| 2     | User Profile + Preferences     | Partial           |
| 3     | Restaurant Listings            | Not Implemented   |
| 4     | Reviews                        | Not Implemented   |
| 5     | Favorites + User History       | Not Implemented   |
| 6     | Owner Features                 | Not Implemented   |
| 7     | AI Assistant Chatbot           | Not Implemented   |
| 8     | Documentation, Testing & Polish| Partial           |

---

## Phase 0 — Project Setup
**Status: Partial**

### Evidence (Implemented)
- `backend/app/main.py` — FastAPI app, CORS, `/health` root endpoint ✅
- `backend/app/core/config.py` — Pydantic Settings reads `.env` ✅
- `backend/app/core/security.py` — bcrypt + JWT helpers ✅
- `backend/app/core/errors.py` — Standardised exception handlers ✅
- `backend/app/db/session.py` — SQLAlchemy engine + SessionLocal + `get_db` dependency ✅
- `backend/app/db/base.py` — Declarative Base ✅
- `backend/app/models/` — user.py, owner.py, user_preference.py ✅
- `backend/app/schemas/` — auth.py, user.py ✅
- `backend/app/api/v1/endpoints/` — auth.py, users.py, owners.py, health.py ✅
- `backend/alembic/` — Alembic initialised, `env.py` connected to settings ✅
- `backend/requirements.txt` ✅ | `backend/.env.example` ✅
- `frontend/` — Vite + React, axios, react-router-dom ✅
- `frontend/src/App.jsx` — Full route skeleton (/, /login, /signup, /owner/login, /owner/signup, /profile, /preferences, /restaurant/:id, /add-restaurant) ✅
- `frontend/src/components/TopNav.jsx` — Navbar with conditional auth links ✅
- `GET /api/v1/health` — DB-verified health check ✅

### Deviations from Plan
1. **No `app/services/` directory.** Business logic lives as `_private` helper functions inside `app/api/v1/endpoints/*.py`. Golden Rule 5 violated: *"No DB logic inside route handlers — all goes in services/"*.
2. **No Alembic migration files.** `backend/alembic/versions/` contains only `.gitkeep`. Schema is created via raw SQL scripts in `db/001_init_schema.sql`. No `alembic upgrade head` path exists.
3. **No Tailwind CSS.** Plan specifies Tailwind; implementation uses a custom CSS file (`frontend/src/styles.css`).
4. **Different JWT library.** Plan specifies `python-jose[cryptography]`; code uses `PyJWT>=2.8`. Also uses `bcrypt>=4.0` directly instead of `passlib[bcrypt]`.
5. **Missing Phase 7 dependencies.** `langchain` and `tavily-python` are absent from `requirements.txt`.
6. **API URL prefix deviation.** All endpoints are served under `/api/v1/` (e.g., `/api/v1/auth/user/signup`). Plan quick-reference table shows paths without this prefix.

---

## Phase 1 — Authentication (User + Owner)
**Status: Complete**

### Evidence
**Database models (SQLAlchemy + SQL init script):**
- `users` table: id, name, email, password_hash, created_at, updated_at ✅
- `owners` table: id, name, email, password_hash, restaurant_location, created_at, updated_at ✅
- UNIQUE on `users.email`, `owners.email` ✅

**Security utilities (`backend/app/core/security.py`):**
- `get_password_hash()` / `verify_password()` via bcrypt ✅
- `create_access_token(subject, expires_minutes, token_type)` — includes `typ` claim to distinguish user vs owner tokens ✅
- `decode_access_token()` ✅

**API endpoints (`backend/app/api/v1/endpoints/auth.py`, `backend/app/api/deps.py`):**
- `POST /api/v1/auth/user/signup` ✅ | `POST /api/v1/auth/signup` (alias) ✅
- `POST /api/v1/auth/user/login` ✅ | `POST /api/v1/auth/login` (alias) ✅
- `POST /api/v1/auth/owner/signup` ✅
- `POST /api/v1/auth/owner/login` ✅
- `GET /api/v1/users/me` ✅ | `GET /api/v1/auth/me` (alias) ✅
- `GET /api/v1/owners/me` ✅
- `get_current_user()` dep ✅ | `get_current_owner()` dep ✅
- Login response: `{ "access_token": "...", "token_type": "bearer", "user": {...} }` ✅
- 409 on duplicate email ✅ | 401 on bad password ✅ | 401 on missing token ✅

**Frontend pages:**
- `/login` (`LoginPage.jsx`) ✅ | `/signup` (`SignupPage.jsx`) ✅
- `/owner/login` (`OwnerLoginPage.jsx`) ✅ | `/owner/signup` (`OwnerSignupPage.jsx`) ✅
- JWT stored in `localStorage` ✅ | Axios interceptor injects `Authorization: Bearer` ✅
- `AuthContext.jsx` — `login()`, `logout()`, `refreshCurrentUser()`, `isAuthReady` ✅
- Post-login redirect ✅ | Logout button in Navbar ✅
- Cross-links between auth pages ✅

### Deviations
- **JWT library:** PyJWT used instead of python-jose (functional parity, different import surface).
- **No separate `services/auth.py`:** Auth logic is inline in `endpoints/auth.py` as private helpers.

---

## Phase 2 — User Profile + Preferences
**Status: Partial**

### Evidence (Implemented)
**Database:**
- `user_preferences` table exists (SQL + SQLAlchemy model `backend/app/models/user_preference.py`) ✅
- Profile fields (phone, about_me, city, state, country, languages, gender, avatar_url) present ✅
- File upload: `POST /api/v1/users/me/avatar` + alias `/profile-picture`, max 5 MB, jpg/png/webp ✅

**API endpoints (`backend/app/api/v1/endpoints/users.py`):**
- `GET /api/v1/users/me` — merged user + profile data ✅
- `PUT /api/v1/users/me` — updates profile fields ✅
- `POST /api/v1/users/me/avatar` (+ `/profile-picture` alias) ✅
- `GET /api/v1/users/me/preferences` ✅
- `PUT /api/v1/users/me/preferences` ✅

**Validation:**
- `state` — 2-letter uppercase enforced (schema + frontend) ✅
- `country` — validated against `ALLOWED_COUNTRY_CODES` set (backend + frontend dropdown) ✅
- Avatar: extension + MIME-type whitelist ✅

**Frontend pages:**
- `/profile` (`ProfilePage.jsx`) — pre-filled form, avatar upload with preview, save ✅
- `/preferences` (`PreferencesPage.jsx`) — multi-select cuisines, dietary, ambiance; price/sort dropdowns; location/radius ✅

### Deviations
1. **No separate `user_profiles` table.** Plan specifies a `user_profiles` table (FK → users.id, unique). All profile fields are merged directly into the `users` table. This flattens the schema. The API return shape still matches the plan.
2. **Column naming differs in `user_preferences`:**
   - Plan: `cuisine_preferences` → Actual: `cuisines`
   - Plan: `dietary_restrictions` → Actual: `dietary_needs`
   - Plan: `ambiance_preferences` → Actual: `ambiance`
   - Plan: `search_radius_km FLOAT` → Actual: `search_radius_km INT`
3. **`country` column stored as 2-char code (VARCHAR(2)), not full country name (VARCHAR(100)).** The plan says `VARCHAR(100)`.
4. **`profile_picture_url` stored as `avatar_url` on users row**, not in a separate profile table.
5. **Languages stored as comma-separated VARCHAR** in the DB (not JSON array as specified in plan). Frontend converts list ↔ comma string.
6. **No email-uniqueness check on `PUT /users/me`.** Plan requires rejecting duplicate email updates; this is unverified in the current implementation.

---

## Phase 3 — Restaurant Listings (Create + Search + Details)
**Status: Not Implemented**

### Evidence
**Database (SQL only — no Python ORM model):**
- `restaurants` table created by `db/001_init_schema.sql` with ~11 fields (id, name, cuisine_type, description, city, state, zip, country, phone, pricing_tier, created_by_user_id).
- Indexes on name, city, cuisine_type ✅
- FK to users (SET NULL) ✅

**Missing from DB schema (vs plan):**
- `street`, `latitude`, `longitude`, `email`, `hours_json`, `amenities` (JSON), `claimed_by_owner_id`, `updated_at` columns — absent or unconfirmed.
- `restaurant_photos` table — **absent**.

**Backend:**
- No SQLAlchemy model for `Restaurant` or `RestaurantPhoto`.
- No Pydantic schemas for restaurant operations.
- **Zero endpoints implemented:** `POST /restaurants`, `GET /restaurants`, `GET /restaurants/{id}`, `POST /restaurants/{id}/photos` — all absent.

**Frontend:**
- `/` (Explore page) — placeholder only ("Explore Restaurants" heading, no search or cards).
- `/restaurant/:id` — `PlaceholderPage` component, no real content.
- `/add-restaurant` — `PlaceholderPage` component, no form.

### Deviations
- Entire phase is not implemented beyond a partial SQL table definition.
- `amenities` JSON field (critical for Phase 7 AI search) is absent.
- `restaurant_photos` table is absent.
- No service layer, no routes, no frontend pages.

---

## Phase 4 — Reviews (Add / Edit / Delete + Rating Aggregation)
**Status: Not Implemented**

### Evidence
**Database (SQL only):**
- `reviews` table in `db/001_init_schema.sql`: id, user_id, restaurant_id, rating (CHECK 1–5), comment, created_at, updated_at ✅
- UNIQUE constraint (user_id, restaurant_id) ✅
- Indexes on restaurant_id, user_id ✅
- 3 seed reviews inserted by `db/002_seed_sample_data.sql` ✅

**Backend:**
- No SQLAlchemy `Review` model.
- No Pydantic review schemas.
- **Zero endpoints:** `POST /restaurants/{id}/reviews`, `GET /restaurants/{id}/reviews`, `PUT /reviews/{id}`, `DELETE /reviews/{id}` — all absent.
- No rating aggregation logic.

**Frontend:**
- No review form, no review list, no star selector, no edit/delete buttons — all absent.

### Deviations
- Entire phase not implemented beyond SQL table creation.

---

## Phase 5 — Favorites + User History
**Status: Not Implemented**

### Evidence
**Database (SQL only):**
- `favorites` table: id, user_id, restaurant_id, created_at, UNIQUE(user_id, restaurant_id) ✅
- `user_history` table: id, user_id, action (ENUM), restaurant_id, details, created_at ✅
- 2 seed favorites and 3 seed history entries present ✅

**Backend:**
- No SQLAlchemy models for Favorite or UserHistory.
- **Zero endpoints:** `POST /favorites/{id}`, `DELETE /favorites/{id}`, `GET /users/me/favorites`, `GET /users/me/history` — all absent.

**Frontend:**
- No favorites toggle, no dashboard page, no favorites tab, no history tab.

### Deviations
1. **`user_history` table exists in SQL but plan says no table is needed** (history should be derived from reviews/restaurants queries). This is an unprompted addition.
2. Entire backend and frontend for Phase 5 not implemented.

---

## Phase 6 — Owner Features
**Status: Not Implemented**

### Evidence
**Partially implemented:**
- `GET /api/v1/owners/me` — returns owner profile ✅
- `Owner` SQLAlchemy model exists ✅
- `get_current_owner()` dependency exists ✅

**Not implemented:**
- `PUT /owners/me` — absent.
- `POST /owner/restaurants` — absent.
- `PUT /owner/restaurants/{id}` — absent.
- `POST /owner/restaurants/{id}/claim` — absent (claim logic, 409 conflict check).
- `GET /owner/restaurants/{id}/reviews` — absent.
- `GET /owner/dashboard` — absent.
- `restaurants.claimed_by_owner_id` FK column — absent from current SQL schema.

**Frontend:**
- None of the owner management pages exist: `/owner/profile`, `/owner/restaurants`, `/owner/restaurants/:id/edit`, `/owner/dashboard`.

### Deviations
- Only `GET /owners/me` from Phase 6 is implemented.
- Claim workflow entirely absent.

---

## Phase 7 — AI Assistant Chatbot
**Status: Not Implemented**

### Evidence
- No `ai-assistant` route file.
- No LangChain imports anywhere in the codebase.
- No Tavily usage.
- `langchain` and `tavily-python` absent from `backend/requirements.txt`.
- `TAVILY_API_KEY`, `LLM_PROVIDER`, `OPENAI_API_KEY`, `OPENAI_MODEL` present in `backend/.env.example` ✅ (placeholder values only).
- No frontend chatbot component, no chat widget, no conversation thread UI.

### Deviations
- Entire phase not started. Dependencies not installed.

---

## Phase 8 — Documentation, Testing & Final Polish
**Status: Partial**

### Evidence (Implemented)
- Swagger UI available at `http://localhost:8000/docs` (FastAPI auto-generate) ✅
- `docs/api-contract-v1.md` — manual API specification exists ✅
- `docs/implementation-checklist-week1.md` — week 1 tracker ✅
- `backend/app/core/errors.py` — standardised `{"detail": "..."}` error format ✅
- HTTP status codes 400, 401, 403, 404, 409, 422 used correctly in auth/profile code ✅
- Frontend loading states (spinners, disabled buttons during save) ✅
- Frontend error states (error banners, field-level messages) ✅
- Mobile responsive CSS (breakpoint at 760px) ✅
- DB indexes on users.email, owners.email, restaurants(name, city, cuisine_type), reviews(user_id, restaurant_id), favorites(user_id, restaurant_id) — present in SQL init script ✅
- `README.md` exists with setup steps ✅

### Not Implemented / Deviations
1. **No pytest test suite.** `backend/tests/` directory does not exist. Only `backend/scripts/db_smoke.py` exists (not pytest). Plan requires `test_auth.py`, `test_reviews.py`, `test_restaurants.py`.
2. **No pagination.** `GET /restaurants` and `GET /restaurants/{id}/reviews` endpoints do not exist yet; pagination will need to be added when they are built.
3. **No Alembic migration for indexes.** Indexes exist only in the raw SQL init script, not in Alembic migration files.
4. **Empty states not verified** for unimplemented pages (restaurant search, details, dashboard).
5. **Accessibility not verified** (semantic HTML, alt text, keyboard navigation).
6. **No `pydantic[email]` in requirements** — email validation relies on Pydantic's built-in string validator.
7. **No Postman collection** (`docs/postman_collection.json` absent).

---

## Architectural Deviations Summary

| # | Area | Plan Specification | Actual Implementation |
|---|------|-------------------|-----------------------|
| 1 | **Service layer** | Dedicated `app/services/` directory; no DB logic in routes | Business logic as `_private` helpers inside `endpoints/*.py`; no `services/` dir |
| 2 | **DB migrations** | Alembic migrations (`alembic upgrade head`) | Raw SQL scripts (`db/001_init_schema.sql`); Alembic `versions/` is empty |
| 3 | **user_profiles table** | Separate `user_profiles` table (FK → users.id) | Profile fields merged into `users` table directly |
| 4 | **JWT library** | `python-jose[cryptography]` | `PyJWT>=2.8` |
| 5 | **Password hashing** | `passlib[bcrypt]` | `bcrypt>=4.0` (direct) |
| 6 | **CSS framework** | Tailwind CSS | Custom CSS (`frontend/src/styles.css`) |
| 7 | **user_preferences column names** | `cuisine_preferences`, `dietary_restrictions`, `ambiance_preferences` | `cuisines`, `dietary_needs`, `ambiance` |
| 8 | **search_radius_km type** | FLOAT | INT |
| 9 | **country storage** | VARCHAR(100) full name | VARCHAR(2) ISO code |
| 10 | **languages storage** | JSON array | Comma-separated VARCHAR string |
| 11 | **user_history table** | No table; history derived from reviews + restaurants queries | Explicit `user_history` table with ENUM action column |
| 12 | **API path prefix** | `/auth/...`, `/users/...` (no version prefix) | `/api/v1/auth/...`, `/api/v1/users/...` |
| 13 | **AI dependencies** | `langchain`, `tavily-python` in requirements.txt | Not installed |
| 14 | **restaurants table** | Full schema with amenities, hours_json, lat/lon, claimed_by_owner_id, restaurant_photos | Partial SQL-only schema; missing amenities, hours_json, lat/lon, claimed_by_owner_id; no restaurant_photos table |

---

## Final Assessment

### Highest Fully Completed Phase
**Phase 1 — Authentication (User + Owner)**
All backend endpoints, security utilities, DB models, and frontend pages for authentication are implemented and functional. Minor deviations (JWT library choice, no services/ directory) do not affect end-to-end functionality.

### Next Required Phase
**Phase 2 remediation + Phase 3 start**

Phase 2 is functionally working but has structural deviations (no separate `user_profiles` table, column name mismatches, languages stored as VARCHAR). Before proceeding to Phase 3, the team should make a formal decision: either align the DB schema with the plan, or accept the merged-users-table approach and update the plan accordingly.

Phase 3 (Restaurant Listings) is the next unstarted phase. It requires:
1. Completing the `restaurants` table SQL schema (add `street`, `amenities`, `hours_json`, `latitude`, `longitude`, `email`, `claimed_by_owner_id`, `updated_at`) and adding `restaurant_photos` table
2. SQLAlchemy `Restaurant` + `RestaurantPhoto` ORM models
3. Pydantic schemas for restaurant CRUD
4. Four new API endpoints (`POST /restaurants`, `GET /restaurants`, `GET /restaurants/{id}`, `POST /restaurants/{id}/photos`)
5. Complete frontend: Explore page with search/filter cards, Restaurant Details page, Add Restaurant form

### Critical Architectural Blocker
The absence of a `services/` layer is the most significant architectural debt. All future phases (3–7) add substantial business logic; building them as route-inline private helpers will make the codebase increasingly difficult to test, maintain, and hand off. This should be resolved — either by introducing `services/` before Phase 3, or by formally accepting the inline-helper pattern and updating the Golden Rules accordingly — before feature work resumes.
