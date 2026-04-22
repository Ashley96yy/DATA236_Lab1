# DATA236 Lab 2 - Yelp Distributed Application

This repository contains the Lab 2 version of our Yelp-style application. The project extends the Lab 1 prototype into a distributed full-stack system with:

- MongoDB for document storage
- containerized backend microservices
- Kafka-based asynchronous review processing
- Kubernetes manifests for deployment
- Amazon EKS / ECR deployment support
- Redux-based frontend state management
- JMeter load-testing plans and result artifacts
- a hybrid AI assistant with internal recommendations and external fallback search

## Final Lab 2 Architecture

The final deployed system is organized into the following services:

- `user-service`
  - user authentication
  - user profile, favorites, preferences
  - AI assistant workflow
- `owner-service`
  - owner authentication
  - restaurant claim and owner management flows
  - owner dashboard analytics and sentiment summaries
- `restaurant-service`
  - restaurant list/detail data
  - restaurant creation and photo-related operations
- `review-api-service`
  - receives review create/update/delete requests
  - publishes review events to Kafka
- `review-worker-service`
  - consumes Kafka review events
  - persists the final review changes to MongoDB
- `api-gateway`
  - single HTTP entry point for frontend-to-backend communication
- `frontend`
  - React/Vite application with Redux-managed state

Supporting infrastructure:

- `mongodb`
- `zookeeper`
- `kafka`
- `mongo-init` bootstrap / seed job

## Repository Layout

```text
backend/
  services/                  backend microservices
  shared/                    shared config, db, schemas, auth helpers
  scripts/                   bootstrap and seed utilities
frontend/
  src/store/                 Redux store and slices
deploy/
  docker/                    local gateway config
  k8s/                       Kubernetes manifests
jmeter/
  plans/                     .jmx load-test plans
  results/                   raw .jtl outputs and summaries
  scripts/                   JMeter summarization utilities
```

## Main Features

### User flows

- user signup / login / logout
- restaurant browsing, filters, sorting, and detail pages
- favorites and history
- create, edit, and delete reviews
- profile and preference management
- AI assistant recommendations

### Owner flows

- owner signup / login / logout
- claim restaurant
- create and edit restaurant
- owner dashboard analytics
- owner-side sentiment labels for claimed restaurants

### Distributed system features

- review events processed asynchronously through Kafka
- MongoDB-backed session persistence
- Redux-managed authentication, restaurant, review, favorites, and preference state
- AWS deployment through EKS and ECR

## Prerequisites

For local Lab 2 execution:

- Docker Desktop or Docker Engine with Compose support
- optional: `kubectl` for Kubernetes deployment
- optional: `aws` CLI for EKS / ECR deployment
- optional: Apache JMeter for performance testing

## Local Lab 2 Run With Docker Compose

This is the primary local run path for Lab 2.

From the repository root:

```bash
docker compose up -d --build
```

This starts:

- MongoDB
- Zookeeper
- Kafka
- `mongo-init`
- all backend microservices
- API gateway
- frontend

### Local URLs

- Frontend: `http://127.0.0.1:3000`
- Gateway health: `http://127.0.0.1:8000/health`
- API base: `http://127.0.0.1:8000/api/v1`
- Swagger docs are available through the gateway-backed services as applicable

### Demo Accounts

- User: `ashley@example.com` / `Passw0rd!`
- Owner: `owner@example.com` / `Passw0rd!`

### Optional AI Environment Variables

The AI assistant can use internal app data and, when configured, external fallback search.

Set these before running `docker compose up` if needed:

```env
JWT_SECRET_KEY=change-me
GOOGLE_API_KEY=
GEMINI_MODEL=gemini-2.5-flash
TAVILY_API_KEY=
TAVILY_ENABLED=true
```

Notes:

- internal recommendation logic works from application data
- Gemini-backed response generation requires `GOOGLE_API_KEY`
- external fallback search requires `TAVILY_API_KEY`

## Kubernetes / AWS Deployment

Kubernetes manifests are provided under:

```text
deploy/k8s/
```

These manifests include:

- MongoDB
- Kafka + Zookeeper
- `mongo-init` job
- all backend microservices
- API gateway
- frontend

### Basic Apply Command

```bash
kubectl apply -k deploy/k8s
```

### AWS / EKS Notes

For AWS deployment:

1. build service images locally
2. push them to Amazon ECR
3. update the Kubernetes image references if using versioned tags
4. apply the manifests into the EKS cluster

Important files:

- `deploy/k8s/configmap.yaml`
- `deploy/k8s/secret-template.yaml`
- `deploy/k8s/owner-service.yaml`
- `deploy/k8s/api-gateway.yaml`
- `deploy/k8s/frontend.yaml`

Do not commit real secrets to the repository. Use placeholders in Kubernetes secret files and inject real values only in your actual deployment environment.

## JMeter Assets

The `jmeter/` directory contains:

- load-test plans
- test-user CSV data
- raw `.jtl` outputs
- summary CSV results
- helper scripts

Included plans:

- `jmeter/plans/login_load_test.jmx`
- `jmeter/plans/search_load_test.jmx`
- `jmeter/plans/create_review_load_test.jmx`

Example CLI command:

```bash
jmeter -n -t jmeter/plans/login_load_test.jmx \
  -Jthreads=100 \
  -Jramp_up=20 \
  -Jloops=1 \
  -Jresults_file=jmeter/results/login_100.jtl
```

To summarize a JTL result:

```bash
python jmeter/scripts/summarize_jtl.py jmeter/results/login_100.jtl
```

## Frontend State Management

Redux state is implemented under:

```text
frontend/src/store/
```

Key slices include:

- `authSlice`
- `ownerAuthSlice`
- `restaurantSlice`
- `reviewSlice`
- `favoritesSlice`
- `preferencesSlice`

These slices coordinate authentication, restaurant data, review state, favorites, and personalization state across the application.

## Main Routes

### Public

- `/`
- `/restaurant/:id`
- `/login`
- `/signup`
- `/owner/login`
- `/owner/signup`

### User

- `/dashboard`
- `/profile`
- `/preferences`
- `/add-restaurant`

### Owner

- `/owner/dashboard`
- `/owner/profile`
- `/owner/restaurants`
- `/owner/restaurants/new`
- `/owner/restaurants/:id/edit`
- `/owner/restaurants/:id/reviews`

## API Summary

### Authentication

- `POST /api/v1/auth/signup`
- `POST /api/v1/auth/login`
- `POST /api/v1/auth/owner/signup`
- `POST /api/v1/auth/owner/login`

### User

- `GET /api/v1/users/me`
- `PUT /api/v1/users/me`
- `GET /api/v1/users/me/favorites`
- `GET /api/v1/users/me/history`
- `GET /api/v1/users/me/preferences`
- `PUT /api/v1/users/me/preferences`

### Restaurants and Reviews

- `GET /api/v1/restaurants`
- `GET /api/v1/restaurants/{id}`
- `POST /api/v1/restaurants`
- `POST /api/v1/restaurants/{id}/photos`
- `POST /api/v1/restaurants/{id}/reviews`
- `GET /api/v1/restaurants/{id}/reviews`
- `PUT /api/v1/reviews/{id}`
- `DELETE /api/v1/reviews/{id}`

### Owner

- `GET /api/v1/owners/me`
- `PUT /api/v1/owners/me`
- `GET /api/v1/owner/dashboard`
- `POST /api/v1/owner/restaurants`
- `PUT /api/v1/owner/restaurants/{id}`
- `POST /api/v1/owner/restaurants/{id}/claim`
- `GET /api/v1/owner/restaurants/{id}/reviews`

### AI Assistant

- `POST /api/v1/ai-assistant/chat`

## Submission Notes

- include Dockerfiles and Kubernetes manifests
- include Kafka integration code
- include Redux frontend implementation
- include JMeter plans and results
- keep `README.md` aligned with the final Lab 2 architecture

Do not commit:

- `.venv/`
- `__pycache__/`
- real API keys or cloud secrets
- temporary local save files

