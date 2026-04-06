# Yelp Prototype Lab 2 — Full Implementation Plan
### Stack: React + FastAPI + MongoDB + Kafka + Docker + Kubernetes + AWS + Redux + JMeter
### For: Junior Developer Reference (Phase-by-Phase)

---

## ⚠️ GOLDEN RULES — READ BEFORE YOU START

1. **Do not rewrite Lab 1 from scratch.** Reuse the existing application and upgrade it step by step.
2. Every phase must end with: code complete + local validation complete + screenshots or evidence collected.
3. **Keep service boundaries clear.** Do not mix user, owner, restaurant, and review logic in one giant service once the split begins.
4. **No secrets in the repo.** Never commit `.env`, cloud credentials, MongoDB credentials, Kafka credentials, or kubeconfig files.
5. Use meaningful commit messages:
   - `feat(mongo): migrate restaurant storage to mongodb`
   - `feat(kafka): publish review.created events`
   - `feat(redux): add auth and restaurant slices`
6. **Finish the review Kafka flow first.** Do not try to make every write operation asynchronous on day one.
7. **Docker Compose must work before Kubernetes.** Do not move to AWS until the stack runs locally in containers.

---

## PROJECT OVERVIEW

This lab extends the Lab 1 Yelp-style platform into a distributed systems project with:
- **Containerized services** using Docker
- **Service orchestration** using Kubernetes
- **Asynchronous messaging** using Kafka
- **MongoDB** as the primary data store
- **Redux** for frontend state management
- **JMeter** for performance testing

The upgraded platform still supports:
- **User (Reviewer)** — authentication, search, favorites, reviews, history, AI assistant
- **Restaurant Owner** — authentication, claim/create/manage restaurants, review monitoring, dashboard
- **AI Assistant** — recommendation flow built on restaurant data and user preferences

---

## TARGET REPO STRUCTURE

```
root/
├── backend/
│   ├── services/
│   │   ├── user-service/
│   │   ├── owner-service/
│   │   ├── restaurant-service/
│   │   ├── review-api-service/
│   │   └── review-worker-service/
│   ├── shared/                  # shared schemas, config, auth helpers, Mongo/Kafka helpers
│   └── requirements/
├── frontend/                    # React + Redux frontend
├── deploy/
│   ├── docker/
│   ├── compose/
│   └── k8s/
├── jmeter/
├── docs/
└── README.md
```

**Recommended branch strategy:**
- `main` — stable branch only
- `dev` — integration branch
- `feature/<lab2-part>` — feature branches

---

---

# PHASE 0 — Lab 2 Planning and Service Boundaries

**Goal:** Lock the architecture before changing code.

---

## 0.1 Define Services

Split the Lab 1 backend into the following services:

1. **user-service**
   - user signup/login
   - profile
   - preferences
   - favorites
   - history

2. **owner-service**
   - owner signup/login
   - owner profile
   - owner dashboard
   - claim restaurant

3. **restaurant-service**
   - restaurant search
   - restaurant details
   - create restaurant
   - restaurant photo metadata

4. **review-api-service**
   - accept review create/update/delete requests
   - publish Kafka events
   - return request status to frontend

5. **review-worker-service**
   - consume review Kafka topics
   - validate/process review events
   - write results to MongoDB

> Optional later: add `restaurant-worker-service` if you also want `restaurant.created`, `restaurant.updated`, and `restaurant.claimed` to be event-driven.

---

## 0.2 Define Core Topics

Start with these Kafka topics:

- `review.created`
- `review.updated`
- `review.deleted`
- `restaurant.created`

Recommended future-ready topics:
- `restaurant.updated`
- `restaurant.claimed`
- `user.created`
- `user.updated`
- `review.status`

---

## 0.3 Decide What Stays Synchronous vs Asynchronous

**Synchronous (frontend-facing):**
- login/signup
- profile fetch/update
- search and restaurant detail reads
- favorites reads

**Asynchronous first:**
- review create/update/delete

**Asynchronous later if time allows:**
- restaurant create/update/claim

---

## Phase 0 Acceptance Checklist

- [ ] Service boundaries are documented
- [ ] Kafka topics are defined
- [ ] Review flow is confirmed as the first async workflow
- [ ] MongoDB migration scope is agreed
- [ ] Redux slices are agreed before frontend refactor starts

---

---

# PHASE 1 — MongoDB Migration

**Goal:** Replace MySQL with MongoDB as the system of record.

---

## 1.1 MongoDB Collections

Create the following collections:

- `users`
- `owners`
- `user_preferences`
- `sessions`
- `restaurants`
- `reviews`
- `favorites`
- `restaurant_photos`
- `activity_logs`

---

## 1.2 Suggested Document Design

**`users`**
```json
{
  "_id": "ObjectId",
  "name": "Ashley",
  "email": "ashley@example.com",
  "password_hash": "...bcrypt...",
  "phone": "+1 4085550000",
  "about_me": "Food lover",
  "city": "San Jose",
  "state": "CA",
  "country": "US",
  "languages": ["English"],
  "gender": "female",
  "avatar_url": "/uploads/avatar.png",
  "created_at": "ISODate",
  "updated_at": "ISODate"
}
```

**`sessions`**
```json
{
  "_id": "ObjectId",
  "subject_id": "user_or_owner_id",
  "role": "user",
  "token": "jwt-or-session-token",
  "expires_at": "ISODate",
  "created_at": "ISODate"
}
```

**`restaurants`**
```json
{
  "_id": "ObjectId",
  "name": "Hunan Impression",
  "cuisine": "Chinese",
  "description": "Sichuan restaurant",
  "street": "5152 Moorpark Ave Ste 30",
  "city": "San Jose",
  "state": "CA",
  "zip_code": "95129",
  "country": "US",
  "phone": "+1 4085550000",
  "email": "contact@example.com",
  "pricing_tier": "$$",
  "amenities": ["WiFi", "Parking"],
  "hours": {
    "Mon": "11am - 8pm",
    "Tue": "Closed"
  },
  "created_by_user_id": "user_id",
  "claimed_by_owner_id": "owner_id_or_null",
  "created_at": "ISODate",
  "updated_at": "ISODate"
}
```

**`reviews`**
```json
{
  "_id": "ObjectId",
  "restaurant_id": "restaurant_id",
  "user_id": "user_id",
  "rating": 5,
  "comment": "Great food",
  "status": "processed",
  "created_at": "ISODate",
  "updated_at": "ISODate"
}
```

---

## 1.3 Security Rules

- Passwords must remain hashed using `bcrypt`
- Sessions must be stored in MongoDB
- Sessions must have expiry
- Do not store plaintext passwords or raw secrets

---

## 1.4 Migration Strategy

Recommended migration path:

1. Add MongoDB config and client utilities
2. Build repository/data-access helpers for each service
3. Port one domain at a time:
   - users
   - owners
   - restaurants
   - reviews
   - favorites/preferences
4. Verify reads and writes before removing MySQL dependencies

---

## Phase 1 Acceptance Checklist

- [ ] MongoDB connection works locally
- [ ] All core entities are stored in MongoDB
- [ ] Passwords remain bcrypt-hashed
- [ ] Sessions are stored in MongoDB with expiry
- [ ] No service still depends on MySQL for critical Lab 2 flows

---

---

# PHASE 2 — Service Split and Shared Infrastructure

**Goal:** Separate the backend into service-level applications.

---

## 2.1 Shared Backend Package

Create a shared package for:
- config/settings
- JWT helpers
- bcrypt helpers
- MongoDB connection helpers
- common schemas
- common error response helpers
- Kafka producer/consumer helpers

---

## 2.2 Service Responsibilities

**user-service**
- `/auth/signup`
- `/auth/login`
- `/users/me`
- `/users/me/preferences`
- `/users/me/favorites`
- `/users/me/history`

**owner-service**
- `/auth/owner/signup`
- `/auth/owner/login`
- `/owners/me`
- `/owner/dashboard`
- `/owner/restaurants/{id}/claim`

**restaurant-service**
- `/restaurants`
- `/restaurants/{id}`
- `/restaurants/{id}/photos`

**review-api-service**
- `/restaurants/{id}/reviews` POST
- `/reviews/{id}` PUT
- `/reviews/{id}` DELETE

**review-worker-service**
- Kafka consumers only
- no public browser-facing routes required except optional health route

---

## 2.3 Inter-Service Communication

Keep synchronous service-to-service calls minimal.

Recommended pattern:
- frontend talks only to API-facing services
- API-facing services talk to MongoDB directly for synchronous reads
- asynchronous writes go through Kafka

---

## Phase 2 Acceptance Checklist

- [ ] Each backend service has its own app entry point
- [ ] Shared config/auth/Mongo helpers are reused correctly
- [ ] Health endpoints exist for services
- [ ] Frontend-facing routes are separated from worker logic

---

---

# PHASE 3 — Dockerization

**Goal:** Containerize the entire stack.

---

## 3.1 Dockerfiles

Create one Dockerfile per service:

- `backend/services/user-service/Dockerfile`
- `backend/services/owner-service/Dockerfile`
- `backend/services/restaurant-service/Dockerfile`
- `backend/services/review-api-service/Dockerfile`
- `backend/services/review-worker-service/Dockerfile`
- `frontend/Dockerfile`

Optional but recommended:
- development Dockerfiles vs production Dockerfiles

---

## 3.2 docker-compose.yml

Local compose stack should include:

- frontend
- user-service
- owner-service
- restaurant-service
- review-api-service
- review-worker-service
- mongodb
- zookeeper
- kafka

---

## 3.3 Local Container Validation

Validate:
- containers build without errors
- services can reach MongoDB
- services can reach Kafka
- frontend can call backend services
- review flow still works end-to-end

---

## Phase 3 Acceptance Checklist

- [ ] Each required service has a Dockerfile
- [ ] `docker-compose up --build` runs the full stack locally
- [ ] MongoDB and Kafka are reachable from the containers
- [ ] Frontend can complete a basic login + search + review flow

---

---

# PHASE 4 — Kafka Integration

**Goal:** Move review processing to an asynchronous producer/consumer workflow.

---

## 4.1 Producer Flow

When a user submits, updates, or deletes a review:

1. `review-api-service` receives the request
2. validates auth and request payload
3. publishes event to Kafka:
   - `review.created`
   - `review.updated`
   - `review.deleted`
4. returns acknowledgment to frontend

Recommended event structure:
```json
{
  "event_id": "uuid",
  "event_type": "review.created",
  "restaurant_id": "restaurant_id",
  "user_id": "user_id",
  "rating": 5,
  "comment": "Great food",
  "timestamp": "ISODate"
}
```

---

## 4.2 Consumer Flow

`review-worker-service` should:

1. subscribe to review topics
2. validate event payload
3. write the review change to MongoDB
4. update a review status record or activity log
5. optionally publish a completion/status event

---

## 4.3 Required Diagram

Include a report architecture diagram showing:

- frontend services as producers or frontend-facing APIs
- Kafka topics in the middle
- worker services as consumers

At minimum, include:
- `review-api-service`
- Kafka topics
- `review-worker-service`
- MongoDB

---

## Phase 4 Acceptance Checklist

- [ ] Kafka is running locally in the stack
- [ ] Review create publishes to `review.created`
- [ ] Review update publishes to `review.updated`
- [ ] Review delete publishes to `review.deleted`
- [ ] Worker consumes events and persists results in MongoDB
- [ ] Architecture diagram is ready for the report

---

---

# PHASE 5 — Kubernetes and AWS Deployment

**Goal:** Run the Dockerized services in Kubernetes and collect AWS evidence.

---

## 5.1 Kubernetes Manifests

Create manifests for:
- deployments
- services
- config maps
- secrets (without committing real credentials)

Minimum targets:
- frontend
- user-service
- owner-service
- restaurant-service
- review-api-service
- review-worker-service
- mongodb
- kafka

---

## 5.2 Kubernetes Validation

Confirm:
- services can reach each other by service name
- frontend can reach API services
- API services can reach MongoDB and Kafka
- services can scale cleanly

---

## 5.3 AWS Evidence

Collect screenshots of:
- running pods/deployments
- services exposed correctly
- application reachable
- Kafka and MongoDB running in the environment

---

## Phase 5 Acceptance Checklist

- [ ] Kubernetes manifests exist for all required services
- [ ] Services communicate correctly in the cluster
- [ ] AWS screenshots are collected
- [ ] Deployment instructions are documented in README

---

---

# PHASE 6 — Redux Integration

**Goal:** Replace fragmented frontend state with Redux-managed application state.

---

## 6.1 Required Redux Slices

Create these slices:

1. **authSlice**
   - JWT token
   - logged-in user
   - auth status

2. **ownerAuthSlice** (optional but recommended if owner state is separate)
   - owner token
   - owner profile
   - owner auth status

3. **restaurantSlice**
   - restaurant list
   - selected restaurant
   - loading/error

4. **reviewSlice**
   - review list
   - submission/update/delete status
   - async processing status if applicable

5. **favoritesSlice**
   - favorite restaurants
   - add/remove loading state

---

## 6.2 Required Redux Features

- actions
- reducers
- selectors
- async thunks or equivalent async dispatch pattern
- Redux DevTools support

---

## 6.3 Frontend Refactor Targets

Replace or reduce direct state handling in:
- auth context
- favorites context
- restaurant list/detail fetch logic
- review submission/update/delete logic

---

## Phase 6 Acceptance Checklist

- [ ] Redux store is integrated into the React app
- [ ] Auth, Restaurant, Review, and Favorites are managed by Redux
- [ ] At least two state changes are captured in Redux DevTools screenshots
- [ ] Components read from selectors rather than duplicating state locally

---

---

# PHASE 7 — JMeter Performance Testing

**Goal:** Measure performance under load and produce required artifacts.

---

## 7.1 APIs to Test

Required:
- user authentication login endpoint
- restaurant search endpoint
- review submission endpoint

The review submission test should hit the Kafka-backed flow.

---

## 7.2 Required Concurrency Levels

Run tests at:
- 100 users
- 200 users
- 300 users
- 400 users
- 500 users

For each level, record:
- average response time
- throughput (requests/sec)
- error rate

---

## 7.3 Required Deliverables

- `.jmx` file
- result screenshots
- graph of average response time vs concurrency
- short written analysis of bottlenecks and performance change

---

## Phase 7 Acceptance Checklist

- [ ] JMeter test plan is created and saved
- [ ] Tests run at all five required concurrency levels
- [ ] Metrics are recorded for each level
- [ ] Graph is created
- [ ] Analysis is written for the report

---

---

# PHASE 8 — README, Report, and Submission Packaging

**Goal:** Package the final Lab 2 submission cleanly.

---

## 8.1 README Updates

README must include:
- architecture overview
- service list
- Docker Compose setup
- Kubernetes deployment steps
- MongoDB setup
- Kafka setup
- Redux notes
- JMeter execution notes

---

## 8.2 Report Sections

The Lab 2 report should cover:
- how Docker, Kubernetes, Kafka, and AWS were integrated
- how Redux improves state management
- screenshots of AWS services and Kafka flow
- MongoDB schema design and session handling
- JMeter graph and performance analysis

---

## 8.3 Repo Cleanup

Before submission:
- remove temporary drafts not needed for grading
- ensure no `.env`, `venv/`, `__pycache__/`, or cloud credentials are committed
- verify `requirements.txt` and frontend dependency files are present
- confirm private repo access for `Devdatta1999` and `Saurabh2504`

---

## Phase 8 Acceptance Checklist

- [ ] README reflects Lab 2 architecture and setup
- [ ] Report includes all required screenshots and explanations
- [ ] JMeter artifacts are committed
- [ ] No secrets or local junk files are committed
- [ ] Repository is private and access is correct

---

## RECOMMENDED IMPLEMENTATION ORDER

If time is limited, follow this order exactly:

1. Phase 0 — Architecture plan
2. Phase 1 — MongoDB migration
3. Phase 2 — Service split
4. Phase 3 — Docker + Compose
5. Phase 4 — Kafka review flow
6. Phase 6 — Redux
7. Phase 5 — Kubernetes + AWS
8. Phase 7 — JMeter
9. Phase 8 — README + report + cleanup

> **Why this order?**  
> MongoDB and service boundaries affect almost every other part of the system.  
> Docker Compose must work before Kubernetes.  
> Kafka should be proven locally before cloud deployment.  
> JMeter should only be run after the stack is stable.

---

## FINAL LAB 2 DONE CRITERIA

You are done only when:

- [ ] MongoDB fully replaces MySQL in the Lab 2 implementation
- [ ] Review processing flows through Kafka
- [ ] Required services are containerized
- [ ] Docker Compose runs the stack locally
- [ ] Kubernetes manifests exist and services communicate
- [ ] AWS deployment screenshots are captured
- [ ] Redux manages auth, restaurant, review, and favorites state
- [ ] Redux DevTools screenshots are included
- [ ] JMeter test plan, graph, and analysis are complete
- [ ] README and report are updated for Lab 2

---
