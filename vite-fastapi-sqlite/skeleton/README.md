# skeleton

Plantilla mínima para apps con **FastAPI + uv** (backend) y **Vite + React + MUI** (frontend).

## Stack

| Capa      | Tecnología          |
|-----------|---------------------|
| Backend   | FastAPI, Python 3.12 |
| Packaging | uv                  |
| Frontend  | Vite, React, TypeScript |
| UI        | Material UI (MUI v6) |

## Estructura

```
skeleton/
├── backend/
│   ├── pyproject.toml       # dependencias y config (uv/fastapi)
│   ├── .python-version      # versión de Python para uv
│   └── src/
│       └── app/
│           ├── main.py      # entry point FastAPI
│           └── routers/
│               └── health.py
├── frontend/
│   ├── index.html
│   ├── vite.config.ts
│   ├── package.json
│   └── src/
│       ├── main.tsx
│       ├── App.tsx
│       └── theme.ts         # MUI theme base
└── .env.example
```

## Inicio rápido

### Backend

```bash
cd backend
uv sync
uv run fastapi dev src/app/main.py
```

### Frontend

```bash
cd frontend
npm install
npm run dev
```

La API corre en `http://localhost:8000` y el frontend en `http://localhost:5173`.
El frontend proxea `/api` → backend automáticamente (ver `vite.config.ts`).
