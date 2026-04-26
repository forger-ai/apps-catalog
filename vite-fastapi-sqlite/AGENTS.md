# Stack: vite-fastapi-sqlite

Apps in this stack run a **FastAPI** backend (Python, SQLite via SQLModel) and a
**Vite + React + MUI** frontend. They are packaged as ZIPs and run locally via
Docker Compose or the Forger desktop app.

## Directory layout inside an app

```
{app}/
  backend/
    app/
      __init__.py
      main.py         FastAPI app factory
      database.py     ← copied from commons/backend/
      health.py       ← copied from commons/backend/
      cors.py         ← copied from commons/backend/
      models.py       SQLModel table definitions
      schemas.py      Pydantic request/response schemas
      routes/         One file per domain (e.g. movements.py)
      services/       Business logic called by routes
    scripts/          Dev/admin CLI scripts
    data/             SQLite files (gitignored)
    pyproject.toml
  frontend/
    src/
      api/
        client.ts     ← copied from commons/frontend/
        {domain}.ts   Domain-specific API calls
      components/     React components
      views/          Page-level components
      main.tsx
      App.tsx
    package.json
    vite.config.ts
  manifest.json
  docker-compose.yml
```

## Commons

Three files are injected by `build_setup` and should not be edited inside the app:

| File | Location in app | What it does |
|------|----------------|--------------|
| `database.py` | `backend/app/database.py` | SQLModel engine, `init_db`, `get_session` |
| `health.py` | `backend/app/health.py` | `GET /health` router |
| `cors.py` | `backend/app/cors.py` | `allowed_origins()` from env |
| `client.ts` | `frontend/src/api/client.ts` | Typed HTTP client |

## Backend conventions

- Use `get_session()` as a FastAPI dependency (`Depends(get_session)`)
- Include `health.router` in every app's `main.py`
- Read CORS origins via `cors.allowed_origins()`, never hardcode them
- Database URL comes from `DATABASE_URL` env var; Forger sets this at runtime

## Frontend conventions

- All HTTP calls go through `client.ts` — never use `fetch` directly
- One file per domain in `src/api/` (e.g. `movements.ts`, `categories.ts`)
- MUI theme lives in `src/theme/theme.ts`

## Running locally

```bash
# Backend
cd backend && uv run uvicorn app.main:app --reload --port 8000

# Frontend
cd frontend && npm install && npm run dev
```

## Adding a route

1. Create `backend/app/routes/{domain}.py` with an `APIRouter`
2. Import and register in `main.py`
3. Add corresponding `frontend/src/api/{domain}.ts` using `client.ts` helpers
