# AI Trip Optimizer

A full-stack travel planning app: sign up, save your travel preferences, get
personalized destination recommendations, and plan trips that fit your budget.

- **Frontend** — React + Vite + Tailwind CSS v4 (react-router)
- **Backend** — FastAPI
- **Database** — PostgreSQL
- **Auth** — JWT with bcrypt password hashing
- **AI layer** — modular multi-agent pipeline (destination, hotel, weather,
  transport, cost, itinerary) with optional RAG + external API enrichments

## Repo layout

```
ai-trip-optimizer/
├── frontend/            # React + Vite app
│   ├── app/             # login, signup, dashboard, create-trip, trips + layout/main/App
│   ├── components/      # auth / common / trip / itinerary
│   ├── hooks/ services/ lib/ types/
│   └── public/          # favicon + destination imagery
├── backend/             # FastAPI app
│   └── app/             # api, models, schemas, services, database, agents, rag, api_clients, workflows
├── database/            # migrations (Alembic) + seed.py
├── docs/                # HLD, LLD, database-design, API-documentation
└── docker-compose.yml
```

## Quick start (Docker)

```bash
docker compose up --build
```

- Frontend: http://localhost:3000
- API docs: http://localhost:8000/docs

## Local development

### 1. Database (PostgreSQL)

```bash
# create role + db
sudo -u postgres psql -c "CREATE ROLE tripopt LOGIN PASSWORD 'tripopt';"
sudo -u postgres createdb -O tripopt tripopt
```

> Zero-setup alternative: set `DATABASE_URL=sqlite:///./dev.db` in
> `backend/.env` — everything works with no Postgres installed.

### 2. Backend

```bash
cd backend
python3 -m venv .venv
.venv/bin/pip install -r requirements.txt
cp .env.example .env           # edit DATABASE_URL if needed
.venv/bin/uvicorn app.main:app --reload --port 8000
```

Tables are created on startup (dev). For migrations:

```bash
.venv/bin/alembic upgrade head
python ../database/seed.py     # seed the destination catalogue
```

### 3. Frontend

```bash
cd frontend
npm install
npm run dev                    # http://localhost:5173
```

The Vite dev server proxies `/api/*` and `/images/*` to the backend on
`http://localhost:8000`, so no extra config is needed.

### Smoke test

With the backend running:

```bash
cd backend
.venv/bin/python tests/smoke_test.py   # 16/16 checks
```

## Environment variables

Backend (`backend/.env`):

| Var | Purpose |
| --- | --- |
| `DATABASE_URL` | SQLAlchemy URL (Postgres) |
| `SECRET_KEY` | token signing secret |
| `ACCESS_TOKEN_EXPIRE_MINUTES` | JWT expiry |
| `CORS_ORIGINS` | allowed origins (comma-separated) |
| `OPENWEATHERMAP_API_KEY` | optional — live weather |
| `GOOGLE_PLACES_API_KEY` | optional — places |
| `AMADEUS_API_KEY` / `AMADEUS_API_SECRET` | optional — hotels |
| `OPENAI_API_KEY` | optional — embeddings for RAG |

Frontend (`frontend/.env`):

| Var | Purpose |
| --- | --- |
| `VITE_API_URL` | optional — override API base (default `/api`) |
