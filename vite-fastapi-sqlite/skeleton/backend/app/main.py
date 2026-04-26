from __future__ import annotations

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

import app.database_ext  # noqa: F401 - registers models before init_db

from app.cors import allowed_origins
from app.database import init_db
from app.routes import health


def create_app() -> FastAPI:
    app = FastAPI(
        title="Skeleton API",
        version="0.1.0",
        docs_url="/api/docs",
        redoc_url="/api/redoc",
        openapi_url="/api/openapi.json",
    )

    app.add_middleware(
        CORSMiddleware,
        allow_origins=allowed_origins(),
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    @app.on_event("startup")
    def _startup() -> None:
        init_db()  # models already registered via database_ext

    app.include_router(health.router)

    return app


app = create_app()
