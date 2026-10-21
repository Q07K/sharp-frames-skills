import time
from collections.abc import AsyncIterator, Callable
from contextlib import asynccontextmanager

from fastapi import FastAPI

from board import auth, posts
from board.config import Settings, load_settings
from board.db import init_schema


def create_app(
    settings: Settings | None = None, clock: Callable[[], float] = time.time
) -> FastAPI:
    """Build the application. `clock` returns Unix seconds and decides session expiry."""
    resolved_settings = settings if settings is not None else load_settings()

    @asynccontextmanager
    async def lifespan(app: FastAPI) -> AsyncIterator[None]:
        init_schema(resolved_settings.db_path)
        yield

    app = FastAPI(title="Board API", lifespan=lifespan)
    app.state.settings = resolved_settings
    app.state.clock = clock
    app.include_router(auth.router)
    app.include_router(posts.router)
    return app
