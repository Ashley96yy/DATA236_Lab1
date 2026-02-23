# Architecture Decision Proposals
**Project:** Dine Finder — Yelp-Style Platform
**Date:** 2026-02-23
**Status:** PENDING APPROVAL — Do not start Phase 3 until decisions A–D are approved.
**Related audit:** `docs/AUDIT_REPORT.md`

---

## Decision A — Database Standard

**Question:** Should Dockerized MySQL be the enforced project standard?

### Recommendation: YES — Docker as default, local MySQL as documented fallback

**Reasoning:**
- The audit found no Docker Compose file in the project. Every developer is currently setting up MySQL independently, which creates version drift (MySQL 5.7 vs 8.x) and connection-string inconsistencies.
- Docker gives all team members an identical MySQL 8 environment with zero installation — a single `docker compose up` replaces a multi-page setup guide.
- Phase 3 onwards adds foreign keys, JSON columns, and composite indexes that behave differently across MySQL versions. Consistency is critical.

**Decision:**
| Question | Answer |
|----------|--------|
| Enforce Docker as the default? | **Yes** |
| Allow local MySQL as fallback? | **Yes, with a documented caveat** (must be MySQL 8.0+, utf8mb4 charset) |
| Block CI/CD on non-Docker setups? | No — local fallback is acceptable for contributors |

**Impact:**
- Add `docker-compose.yml` to project root (one-time, ~20 lines).
- Update `README.md` with Docker-first setup instructions.
- Keep `MYSQL_HOST`, `MYSQL_PORT`, `MYSQL_USER`, `MYSQL_PASSWORD`, `MYSQL_DB` in `.env.example` so local MySQL users only need to change those vars.
- No code changes required. No model or schema changes.

**Proposed `.env.example` additions:**
```
# --- Database ---
# Docker (recommended): run `docker compose up -d` then use values below as-is
# Local MySQL: change host/user/password to match your local setup (must be MySQL 8.0+)
MYSQL_HOST=127.0.0.1
MYSQL_PORT=3306
MYSQL_USER=root
MYSQL_PASSWORD=root
MYSQL_DB=yelp_lab1
```

---

## Decision B — Migration Strategy

**Question:** Should we standardize on Alembic migrations or keep the raw SQL script approach?

### Recommendation: Option 1 — Migrate to Alembic (align with plan)

**Current state:** Schema lives in `db/001_init_schema.sql`. Alembic is configured (`alembic/env.py` is wired to settings) but `alembic/versions/` is empty. New developers cannot run `alembic upgrade head` — they must manually run SQL files.

**Tradeoff table:**

| | Alembic Migrations | SQL Scripts (current) |
|---|---|---|
| Versioned history | ✅ Every schema change is tracked | ❌ Ad-hoc files, no version chain |
| Rollback | ✅ `alembic downgrade -1` | ❌ Manual reverse SQL |
| CI/CD compatibility | ✅ Single command | ❌ Must execute files in order |
| Schema drift detection | ✅ `alembic check` compares models vs DB | ❌ Silent drift |
| Junior-dev friendliness | ⚠️ Small learning curve | ✅ Plain SQL is readable |
| Current investment | Alembic already configured | SQL scripts already written |

**Decision: Move to Alembic.**

**Migration path (one-time, low risk):**
1. Keep `db/001_init_schema.sql` as a reference file (do not delete it).
2. Create an initial Alembic migration by running `alembic revision --autogenerate -m "initial_schema"` against a running DB that already has the tables. This captures the current state.
3. Mark the initial migration as "already applied" on existing dev DBs with `alembic stamp head`.
4. All future schema changes (Phase 3+) go through `alembic revision` → `alembic upgrade head`. No raw SQL for schema changes.
5. Seed data (`db/002_seed_sample_data.sql`) stays as a SQL file — Alembic handles schema only, not seed data.

**Impact:** One setup session (~1 hour). Zero application code changes. All future phases gain automatic schema versioning.

---

## Decision C — Service Layer (Golden Rule #5)

**Question:** Should we introduce `app/services/` before Phase 3 starts, or allow current inline-endpoint logic to continue temporarily?

### Recommendation: Introduce `app/services/` before Phase 3 — not after

**Current state:** All DB access and business logic lives as `_private` helper functions inside `app/api/v1/endpoints/*.py`. This violates IMPLEMENTATION_PLAN.md Golden Rule 5: *"No DB logic inside route handlers — all DB access and business rules go in services/"*.

**Why fix it now, not later:**
- Phase 3 introduces the most complex business logic in the project: restaurant search with multiple filter combinations, photo upload with ownership checks (User OR Owner), and `amenities` JSON queries. Writing all of this inline will create handlers that are 100+ lines long and untestable.
- Phase 4 adds review ownership checks. Phase 5 adds favorites toggle logic. Phase 6 adds restaurant claim conflict logic. Each phase compounds the debt.
- Refactoring after Phase 3–5 are built inline would require touching every endpoint file simultaneously — far more disruptive than establishing the pattern now when only `auth.py` and `users.py` exist.

**Decision: YES — introduce `app/services/` before Phase 3 feature work begins.**

**Scope of refactor (Phase 2→3 transition task, not a separate phase):**
```
backend/app/services/
├── auth_service.py       # move _signup_user, _login_user helpers from endpoints/auth.py
└── user_service.py       # move _to_profile_response, _to_preferences_response, etc. from endpoints/users.py
```
Routes become thin: they validate input via Pydantic, call one service function, and return the result. All DB queries and business rules move to services.

**Rule going forward:** No new endpoint file may contain a raw `db.query()` or `db.add()` call. All DB access goes through a service function.

**Impact:** 2–4 hours of refactor. No API contract changes. No DB changes. Enables pytest (services can be unit-tested without an HTTP client).

---

## Decision D — Plan Alignment Approach

**Question:** Should we update the code to match the plan, or update the plan to match the current code?

### Recommendation: Hybrid — accept pragmatic deviations, align critical DB schema before Phase 3

**Not all deviations carry equal weight.** The audit found 14 deviations. They fall into three categories:

**Category 1 — Accept as-is (update the plan):**
These are implementation-detail choices with no downstream impact on API contracts or data integrity.

| Deviation | Rationale for accepting |
|-----------|------------------------|
| PyJWT instead of python-jose | Both implement HS256 JWT; same security posture |
| bcrypt directly instead of passlib | Same algorithm; passlib is a wrapper |
| Custom CSS instead of Tailwind | Styling choice with no API/schema impact |
| `/api/v1/` URL prefix | More conventional REST versioning; update Quick Reference table in plan |
| `country` stored as 2-char ISO code (VARCHAR(2)) | Stricter and cleaner than full name; update plan column type |

**Category 2 — Align code to plan before Phase 3 (DB schema corrections):**
These deviations will cause silent bugs or blocked features in Phase 3+ if left uncorrected.

| Deviation | Why it must be fixed | Action |
|-----------|---------------------|--------|
| `cuisine_preferences` → `cuisines`, `dietary_restrictions` → `dietary_needs`, `ambiance_preferences` → `ambiance` | Phase 7 AI prompt logic and Phase 8 tests will use plan column names; mismatches will cause confusion | Rename columns via Alembic migration |
| `search_radius_km FLOAT` → `INT` | FLOAT is correct for geographic distances (e.g., 2.5 km) | Change type via Alembic migration |
| Missing `user_profiles` table | **Accept deviation** — merged-into-users approach is pragmatic for a prototype; plan sections 2.1 and 2.2 will be updated to reflect this | Update plan only |
| `languages` stored as VARCHAR (comma-sep) instead of JSON | JSON is more correct and consistent with other array fields; risk of parsing bugs on edge cases | Change to JSON column via Alembic migration |
| `user_history` table added (plan says derive from queries) | Extra table is harmless and may be useful; accept it but document it | Update plan section 5.1 |

**Category 3 — Must be added before Phase 3 (missing schema items):**

| Missing item | Why critical |
|--------------|-------------|
| `restaurants.amenities` (JSON) | Phase 3 search (`keywords` filter) and Phase 7 AI search both depend on this field |
| `restaurants.hours_json` (JSON) | Required by Phase 3 restaurant detail response |
| `restaurants.latitude`, `restaurants.longitude` | Required for Phase 7 geo-aware recommendations |
| `restaurants.email`, `restaurants.street`, `restaurants.claimed_by_owner_id`, `restaurants.updated_at` | Required by Phase 3 and Phase 6 endpoints |
| `restaurant_photos` table | Required by Phase 3 photo upload endpoint |

**Decision summary:**
- Update IMPLEMENTATION_PLAN.md to reflect accepted deviations (library choices, CSS, URL prefix, merged users table, user_history table, country as ISO code).
- Fix critical column naming + type deviations via Alembic migration (column renames, languages → JSON).
- Extend `restaurants` table and add `restaurant_photos` table as part of Phase 3 kick-off migration.

---

## Phase Readiness Checklist

### If Decisions A–D are approved → Phase 3 may start

**Pre-Phase 3 gate (must complete before first Phase 3 endpoint):**
- [ ] **A** — `docker-compose.yml` added to project root; README updated
- [ ] **B** — Initial Alembic migration created and stamped; all future schema changes via Alembic
- [ ] **C** — `app/services/auth_service.py` and `app/services/user_service.py` created; endpoint files refactored to call services
- [ ] **D** — Column renames and type fixes applied via Alembic migration; `restaurants` table extended; `restaurant_photos` table added; IMPLEMENTATION_PLAN.md updated for accepted deviations

**Once all 4 gate items are checked → Phase 3 feature development begins.**

### If decisions are not approved → Blockers

| Decision | Blocker if rejected |
|----------|-------------------|
| A (Docker) | No standard dev environment — setup instructions remain ambiguous |
| B (Alembic) | Phase 3 schema additions have no migration path; DB drift risk increases |
| C (Services) | Phase 3 endpoints will be untestable and exceed 100 lines per handler |
| D (Plan alignment) | `amenities` and `restaurant_photos` table won't exist → Phase 3 endpoints cannot be built |
