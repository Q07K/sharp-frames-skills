"""Application configuration and router composition."""

from contextlib import asynccontextmanager
import os

from fastapi import FastAPI

from .db import initialize_database
from .routers import auth, posts


def create_app(database_path: str = "board-after.sqlite3") -> FastAPI:
    @asynccontextmanager
    async def lifespan(app):
        initialize_database(app.state.database_path)
        yield

    app = FastAPI(title="Board API", lifespan=lifespan)
    app.state.database_path = database_path
    app.include_router(auth.router)
    app.include_router(posts.router)
    return app


app = create_app(os.environ.get("BOARD_DB_PATH", "board-after.sqlite3"))
