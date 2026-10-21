"""A small, working first draft: routes, auth, schemas and SQL in one file."""

from contextlib import asynccontextmanager, closing
import hashlib
import os
import secrets
import sqlite3
import time
from typing import Annotated

from fastapi import Depends, FastAPI, HTTPException, Query, Request, Response
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from pydantic import BaseModel, ConfigDict, Field, StringConstraints
from pwdlib import PasswordHash

password_hash = PasswordHash.recommended()
dummy_hash = password_hash.hash("dummy-password-for-missing-users")
bearer = HTTPBearer(auto_error=False)
SESSION_SECONDS = 3600
SCHEMA = """
CREATE TABLE IF NOT EXISTS users (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    username TEXT NOT NULL UNIQUE,
    password_hash TEXT NOT NULL
);
CREATE TABLE IF NOT EXISTS sessions (
    token_hash TEXT PRIMARY KEY,
    user_id INTEGER NOT NULL REFERENCES users(id),
    expires_at INTEGER NOT NULL
);
CREATE TABLE IF NOT EXISTS posts (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    title TEXT NOT NULL,
    content TEXT NOT NULL,
    author_id INTEGER NOT NULL REFERENCES users(id)
);
"""


class Credentials(BaseModel):
    model_config = ConfigDict(extra="forbid")
    username: Annotated[str, StringConstraints(pattern=r"^[a-zA-Z0-9_]{3,32}$")]
    password: str = Field(min_length=8, max_length=128, repr=False)


class UserPublic(BaseModel):
    id: int
    username: str


class TokenPublic(BaseModel):
    access_token: str
    token_type: str = "bearer"
    expires_in: int = SESSION_SECONDS


class PostInput(BaseModel):
    model_config = ConfigDict(extra="forbid")
    title: Annotated[str, StringConstraints(strip_whitespace=True, min_length=1, max_length=120)]
    content: Annotated[str, StringConstraints(strip_whitespace=True, min_length=1, max_length=5000)]


class PostPublic(BaseModel):
    id: int
    title: str
    content: str
    author_id: int


def get_db(request: Request):
    db = sqlite3.connect(request.app.state.database_path, check_same_thread=False)
    db.row_factory = sqlite3.Row
    db.execute("PRAGMA foreign_keys = ON")
    try:
        yield db
    finally:
        db.close()


def get_current_user(
    credentials: HTTPAuthorizationCredentials | None = Depends(bearer),
    db: sqlite3.Connection = Depends(get_db),
) -> UserPublic:
    if credentials is not None:
        digest = hashlib.sha256(credentials.credentials.encode()).hexdigest()
        row = db.execute(
            "SELECT users.id, users.username FROM sessions JOIN users ON users.id = sessions.user_id "
            "WHERE sessions.token_hash = ? AND sessions.expires_at > ?",
            (digest, int(time.time())),
        ).fetchone()
        if row is not None:
            return UserPublic(**dict(row))
    raise HTTPException(401, "Authentication required", headers={"WWW-Authenticate": "Bearer"})


def create_app(database_path: str = "board-before.sqlite3") -> FastAPI:
    @asynccontextmanager
    async def lifespan(app):
        with closing(sqlite3.connect(app.state.database_path)) as db:
            db.executescript(SCHEMA)
        yield

    app = FastAPI(title="Board API", lifespan=lifespan)
    app.state.database_path = database_path

    @app.post("/auth/register", response_model=UserPublic, status_code=201)
    def register(data: Credentials, db: sqlite3.Connection = Depends(get_db)):
        try:
            cursor = db.execute("INSERT INTO users (username, password_hash) VALUES (?, ?)",
                                (data.username, password_hash.hash(data.password)))
            db.commit()
        except sqlite3.IntegrityError:
            db.rollback()
            raise HTTPException(409, "Username already exists") from None
        return {"id": cursor.lastrowid, "username": data.username}

    @app.post("/auth/login", response_model=TokenPublic)
    def login(data: Credentials, db: sqlite3.Connection = Depends(get_db)):
        user = db.execute("SELECT * FROM users WHERE username = ?", (data.username,)).fetchone()
        valid = password_hash.verify(data.password, user["password_hash"] if user else dummy_hash)
        if user is None or not valid:
            raise HTTPException(401, "Invalid credentials", headers={"WWW-Authenticate": "Bearer"})
        token = secrets.token_urlsafe(32)
        db.execute("INSERT INTO sessions (token_hash, user_id, expires_at) VALUES (?, ?, ?)",
                   (hashlib.sha256(token.encode()).hexdigest(), user["id"], int(time.time()) + SESSION_SECONDS))
        db.commit()
        return TokenPublic(access_token=token)

    @app.get("/posts", response_model=list[PostPublic])
    def list_posts(limit: int = Query(20, ge=1, le=100), offset: int = Query(0, ge=0),
                   db: sqlite3.Connection = Depends(get_db)):
        rows = db.execute("SELECT * FROM posts ORDER BY id LIMIT ? OFFSET ?", (limit, offset)).fetchall()
        return [dict(row) for row in rows]

    @app.get("/posts/{post_id}", response_model=PostPublic)
    def read_post(post_id: int, db: sqlite3.Connection = Depends(get_db)):
        post = db.execute("SELECT * FROM posts WHERE id = ?", (post_id,)).fetchone()
        if post is None:
            raise HTTPException(404, "Post not found")
        return dict(post)

    @app.post("/posts", response_model=PostPublic, status_code=201)
    def create_post(data: PostInput, user: UserPublic = Depends(get_current_user),
                    db: sqlite3.Connection = Depends(get_db)):
        cursor = db.execute("INSERT INTO posts (title, content, author_id) VALUES (?, ?, ?)",
                            (data.title, data.content, user.id))
        db.commit()
        return {"id": cursor.lastrowid, **data.model_dump(), "author_id": user.id}

    @app.put("/posts/{post_id}", response_model=PostPublic)
    def update_post(post_id: int, data: PostInput, user: UserPublic = Depends(get_current_user),
                    db: sqlite3.Connection = Depends(get_db)):
        post = db.execute("SELECT * FROM posts WHERE id = ?", (post_id,)).fetchone()
        if post is None:
            raise HTTPException(404, "Post not found")
        if post["author_id"] != user.id:
            raise HTTPException(403, "Only the author can change this post")
        db.execute("UPDATE posts SET title = ?, content = ? WHERE id = ?", (data.title, data.content, post_id))
        db.commit()
        return {"id": post_id, **data.model_dump(), "author_id": user.id}

    @app.delete("/posts/{post_id}", status_code=204)
    def delete_post(post_id: int, user: UserPublic = Depends(get_current_user),
                    db: sqlite3.Connection = Depends(get_db)):
        post = db.execute("SELECT * FROM posts WHERE id = ?", (post_id,)).fetchone()
        if post is None:
            raise HTTPException(404, "Post not found")
        if post["author_id"] != user.id:
            raise HTTPException(403, "Only the author can change this post")
        db.execute("DELETE FROM posts WHERE id = ?", (post_id,))
        db.commit()
        return Response(status_code=204)

    return app


app = create_app(os.environ.get("BOARD_DB_PATH", "board-before.sqlite3"))
