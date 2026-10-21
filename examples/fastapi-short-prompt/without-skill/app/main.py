from contextlib import asynccontextmanager

from fastapi import FastAPI

from app.db import init_db
from app.routers import auth, posts


@asynccontextmanager
async def lifespan(_: FastAPI):
    init_db()
    yield


app = FastAPI(title="Board API", version="1.0.0", lifespan=lifespan)
app.include_router(auth.router)
app.include_router(posts.router)


@app.get("/health", tags=["meta"])
def health():
    return {"status": "ok"}
