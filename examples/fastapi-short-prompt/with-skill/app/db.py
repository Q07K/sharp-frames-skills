import sqlite3
from collections.abc import Iterator

from fastapi import Request

SCHEMA = """
CREATE TABLE IF NOT EXISTS users (
    id            INTEGER PRIMARY KEY AUTOINCREMENT,
    username      TEXT    NOT NULL UNIQUE COLLATE NOCASE,
    password_hash TEXT    NOT NULL,
    created_at    TEXT    NOT NULL
);

CREATE TABLE IF NOT EXISTS sessions (
    token_hash TEXT    PRIMARY KEY,
    user_id    INTEGER NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    expires_at TEXT    NOT NULL
);

CREATE TABLE IF NOT EXISTS posts (
    id         INTEGER PRIMARY KEY AUTOINCREMENT,
    author_id  INTEGER NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    title      TEXT    NOT NULL,
    content    TEXT    NOT NULL,
    created_at TEXT    NOT NULL,
    updated_at TEXT    NOT NULL
);

CREATE INDEX IF NOT EXISTS ix_posts_author_id ON posts(author_id);
"""


def connect(database_path: str) -> sqlite3.Connection:
    # FastAPI may run a sync dependency and its endpoint on different worker
    # threads; each connection is still used by only one request at a time.
    connection = sqlite3.connect(database_path, check_same_thread=False)
    connection.row_factory = sqlite3.Row
    connection.execute("PRAGMA foreign_keys = ON")
    return connection


def init_schema(database_path: str) -> None:
    connection = connect(database_path)
    try:
        connection.executescript(SCHEMA)
    finally:
        connection.close()


def get_db(request: Request) -> Iterator[sqlite3.Connection]:
    """Per-request connection. Write paths commit via `with connection:`."""
    connection = connect(request.app.state.database_path)
    try:
        yield connection
    finally:
        connection.close()
