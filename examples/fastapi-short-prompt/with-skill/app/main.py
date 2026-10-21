import os
from datetime import timedelta

from fastapi import FastAPI

from app import auth, posts
from app.db import init_schema

DEFAULT_TOKEN_TTL = timedelta(hours=24)


def create_app(database_path: str, token_ttl: timedelta = DEFAULT_TOKEN_TTL) -> FastAPI:
    init_schema(database_path)
    app = FastAPI(title="Board API")
    app.state.database_path = database_path
    app.state.token_ttl = token_ttl
    app.include_router(auth.router)
    app.include_router(posts.router)
    return app


def create_app_from_env() -> FastAPI:
    """Entry point for `uvicorn app.main:create_app_from_env --factory`."""
    return create_app(os.environ.get("DATABASE_PATH", "app.db"))
