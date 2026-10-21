"""FastAPI 애플리케이션 팩토리."""

from fastapi import FastAPI

from . import auth, posts
from .config import Settings, load_settings
from .db import init_db


def create_app(settings: Settings | None = None) -> FastAPI:
    settings = settings or load_settings()
    init_db(settings.db_path)

    app = FastAPI(title="Board API")
    app.state.settings = settings
    app.include_router(auth.router)
    app.include_router(posts.router)
    return app
