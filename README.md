# DATA236 Lab 1 - Yelp Prototype

Yelp-style restaurant discovery and review platform built with `React`, `FastAPI`, `MySQL`, and an AI assistant that supports vector retrieval.

## Stack

- Frontend: `React`, `Vite`, `React Router`, `Axios`
- Backend: `FastAPI`, `SQLAlchemy`, `PyMySQL`, `JWT`, `bcrypt`
- Database: `MySQL`
- AI: `LangChain`, `Chroma`, `OpenAI` or local fallback embeddings, `Tavily`

## Implemented Features

### User / Reviewer
- User signup, login, logout
- Profile editing and avatar upload
- Dining preference management
- Explore/search page with filters and sorting
- Restaurant details page
- Add restaurant listing
- Review create, edit, delete
- Favorites
- User history
- AI assistant chat widget

### Owner
- Owner signup, login, logout
- Owner profile management
- Create restaurant listing as owner
- Claim existing restaurant
- Edit claimed restaurant
- View reviews for claimed restaurants
- Owner dashboard with analytics

### AI Assistant
- `POST /api/v1/ai-assistant/chat`
- Loads user preferences
- Interprets natural language queries
- Uses vector retrieval plus MySQL reranking
- Supports follow-up questions
- Optionally enriches answers with Tavily live context

## Project Structure

```text
backend/    FastAPI app, services, schemas, scripts, tests
frontend/   React app
db/         MySQL schema and seed SQL
docs/       planning and reference docs
```

## Prerequisites

- Python `3.12+`
- Node.js `18+`
- MySQL `8.0+`

## Database Setup

Run from the repository root:

```bash
mysql -u <username> -p < db/001_init_schema.sql
mysql -u <username> -p < db/003_phase3_schema.sql
mysql -u <username> -p < db/004_phase4_reviews.sql
mysql -u <username> -p < db/002_seed_sample_data.sql
```

Optional quick verification:

```bash
mysql -u <username> -p < db/003_quick_check_queries.sql
```

Database name:

```text
yelp_lab1
```

## Seed Accounts

### User accounts
- `alice@example.com` / `Passw0rd!`
- `bob@example.com` / `Passw0rd!`

### Owner accounts
- No seeded owner account is required.
- Create an owner from the UI at `/owner/signup`.

## Backend Setup

```bash
cd backend
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
cp .env.example .env
```

Edit `backend/.env` and set at least:

```env
MYSQL_HOST=127.0.0.1
MYSQL_PORT=3306
MYSQL_USER=...
MYSQL_PASSWORD=...
MYSQL_DB=yelp_lab1
JWT_SECRET_KEY=...
```

### AI Configuration

You can run the AI assistant in two modes.

#### Option 1: Local / no OpenAI cost

```env
EMBEDDING_PROVIDER=local
OPENAI_API_KEY=
AI_LLM_INTENT_EXTRACTION_ENABLED=false
AI_RETRIEVAL_TOP_K=8
```

This uses:
- local fallback embeddings
- Chroma vector retrieval
- MySQL reranking
- fallback response generation without OpenAI

#### Option 2: OpenAI-backed

```env
LLM_PROVIDER=openai
OPENAI_API_KEY=...
OPENAI_MODEL=gpt-4o-mini
OPENAI_EMBEDDING_MODEL=text-embedding-3-small
EMBEDDING_PROVIDER=openai
AI_LLM_INTENT_EXTRACTION_ENABLED=false
AI_RETRIEVAL_TOP_K=8
```

Optional Tavily enrichment:

```env
TAVILY_API_KEY=...
```

### Build the Restaurant Vector Index

Run this after the database is ready and whenever restaurant data changes significantly:

```bash
PYTHONPATH=. .venv/bin/python scripts/rebuild_restaurant_index.py
```

### Start the Backend

```bash
PYTHONPATH=. .venv/bin/uvicorn app.main:app --reload --host 127.0.0.1 --port 8000
```

Backend URLs:

- API root health: `http://127.0.0.1:8000/health`
- Versioned health: `http://127.0.0.1:8000/api/v1/health`
- Swagger docs: `http://127.0.0.1:8000/docs`

## Frontend Setup

```bash
cd frontend
npm install
cp .env.example .env
```

Set:

```env
VITE_API_BASE_URL=http://127.0.0.1:8000/api/v1
```

Start the frontend:

```bash
npm run dev -- --host 127.0.0.1 --port 5173
```

Frontend URL:

- `http://127.0.0.1:5173`

## Recommended Local Run Sequence

From the repository root:

1. Start MySQL
2. Initialize and seed the database
3. Start the backend
4. Build the vector index
5. Start the frontend
6. Open `http://127.0.0.1:5173`

Example:

```bash
cd backend
PYTHONPATH=. .venv/bin/uvicorn app.main:app --reload --host 127.0.0.1 --port 8000
```

In another terminal:

```bash
cd backend
PYTHONPATH=. .venv/bin/python scripts/rebuild_restaurant_index.py
```

In another terminal:

```bash
cd frontend
npm run dev -- --host 127.0.0.1 --port 5173
```

## Main Routes

### Public
- `/`
- `/restaurant/:id`
- `/login`
- `/signup`
- `/owner/login`
- `/owner/signup`

### User
- `/profile`
- `/preferences`
- `/dashboard`
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
- `POST /api/v1/users/me/avatar`
- `GET /api/v1/users/me/preferences`
- `PUT /api/v1/users/me/preferences`
- `GET /api/v1/users/me/favorites`
- `GET /api/v1/users/me/history`

### Restaurants and Reviews
- `POST /api/v1/restaurants`
- `GET /api/v1/restaurants`
- `GET /api/v1/restaurants/{id}`
- `POST /api/v1/restaurants/{id}/photos`
- `POST /api/v1/restaurants/{id}/reviews`
- `GET /api/v1/restaurants/{id}/reviews`
- `PUT /api/v1/reviews/{id}`
- `DELETE /api/v1/reviews/{id}`

### Owner Management
- `GET /api/v1/owners/me`
- `PUT /api/v1/owners/me`
- `POST /api/v1/owner/restaurants`
- `PUT /api/v1/owner/restaurants/{id}`
- `POST /api/v1/owner/restaurants/{id}/claim`
- `GET /api/v1/owner/restaurants/{id}/reviews`
- `GET /api/v1/owner/dashboard`

### AI Assistant
- `POST /api/v1/ai-assistant/chat`

## Notes
- Do not commit `backend/.env` or any real API keys.
- `backend/vector_store/` is generated at runtime and ignored by git.
- If OpenAI quota is unavailable, use local embedding mode.
- FastAPI Swagger UI is the primary API documentation for this project.
