# DATA236 Lab 1 - Yelp Prototype

This repository includes project planning docs, MySQL scripts, and a minimal FastAPI backend scaffold for Week 1.

## Database Setup

### Prerequisites
- MySQL 8.0+
- A MySQL user with permissions to create databases and tables

### Files
- `db/001_init_schema.sql`: create database and tables
- `db/002_seed_sample_data.sql`: insert sample users/restaurants/reviews/favorites/history
- `db/003_quick_check_queries.sql`: quick verification queries

### Run Steps
1. Initialize schema:
```bash
mysql -u <username> -p < db/001_init_schema.sql
```
2. Seed sample data:
```bash
mysql -u <username> -p < db/002_seed_sample_data.sql
```
3. Run quick checks:
```bash
mysql -u <username> -p < db/003_quick_check_queries.sql
```

### Seed Login Accounts
- `alice@example.com` / `Passw0rd!`
- `bob@example.com` / `Passw0rd!`

### Notes
- Database name: `yelp_lab1`
- The seed script is designed to be mostly idempotent for core entities.

## Backend Bootstrap (Week 1 Step 1)

This repository now includes a minimal FastAPI backend scaffold in `backend/`.

### What is included
- `GET /api/v1/health` (checks API + DB connectivity)
- `POST /api/v1/auth/signup` (bcrypt password hashing)
- `POST /api/v1/auth/login` (JWT issue)
- `GET /api/v1/auth/me` (Bearer token protected route)
- `GET /api/v1/users/me` (protected profile read)
- `PUT /api/v1/users/me` (protected profile update)
- `GET /api/v1/users/me/preferences` (protected preferences read)
- `PUT /api/v1/users/me/preferences` (protected preferences update)
- MySQL environment config via `.env`
- SQLAlchemy `users` model
- Scripts for users table bootstrap and DB smoke test

### Run Steps
1. Create a Python virtual environment and install dependencies:
```bash
cd backend
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
```
If you recently changed dependencies, run:
```bash
pip install --upgrade -r requirements.txt
```
If you see a MySQL auth error mentioning `caching_sha2_password`, run:
```bash
pip install cryptography
```

2. Configure environment:
```bash
cp .env.example .env
```
Then edit `.env` with your MySQL credentials.
Also set `JWT_SECRET_KEY` to a long random value for local development.

3. Initialize users table (if needed):
```bash
python scripts/init_users_table.py
```

4. Run DB smoke test (insert + read + delete one temp user):
```bash
python scripts/db_smoke.py
```

5. Start backend:
```bash
uvicorn app.main:app --reload
```

6. Verify health endpoint:
```bash
curl http://127.0.0.1:8000/api/v1/health
```

7. Quick auth check (optional):
```bash
curl -X POST http://127.0.0.1:8000/api/v1/auth/signup \
  -H "Content-Type: application/json" \
  -d '{"name":"Test User","email":"test_user@example.com","password":"Passw0rd!"}'
```

## Frontend Bootstrap (Week 1)

Week 1 frontend lives in `frontend/` (React + Vite + React Router + Axios).

### Implemented Pages
- `/login`
- `/signup`
- `/profile` (protected)
- `/preferences` (protected)

### Implemented Frontend Features
- API client with Bearer token interceptor
- Auth session persistence (localStorage)
- Route guard for protected pages
- Public route guard for login/signup
- Loading/error/success states for Week 1 forms
- Dine Finder auth layout (logo + left form + right hero illustration)

### Run Steps
1. Install dependencies:
```bash
cd frontend
npm install
```
2. Configure API base URL:
```bash
cp .env.example .env
```
`VITE_API_BASE_URL` should point to backend v1 base path, for example:
`http://127.0.0.1:8000/api/v1`

3. Start frontend:
```bash
npm run dev
```

4. Open app:
`http://127.0.0.1:5173`

### Optional UI Customization
- Replace login/signup right-side illustration:
  `frontend/public/login.png`
- Project logo component:
  `frontend/public/app_logo.png` + `frontend/src/components/ProjectLogo.jsx`
