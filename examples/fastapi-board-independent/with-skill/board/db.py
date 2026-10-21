import sqlite3
from collections.abc import Iterator
from pathlib import Path

from fastapi import Request

# SQLite INTEGER is a signed 64-bit value; larger Python ints raise OverflowError
# when bound as parameters.
SQLITE_INTEGER_MIN = -(2**63)
SQLITE_INTEGER_MAX = 2**63 - 1

SCHEMA = """
CREATE TABLE IF NOT EXISTS users (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    username TEXT NOT NULL UNIQUE,
    password_hash TEXT NOT NULL
);
CREATE TABLE IF NOT EXISTS sessions (
    token_fingerprint TEXT PRIMARY KEY,
    user_id INTEGER NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    expires_at REAL NOT NULL
);
CREATE INDEX IF NOT EXISTS sessions_expires_at ON sessions(expires_at);
CREATE TABLE IF NOT EXISTS posts (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    title TEXT NOT NULL,
    content TEXT NOT NULL,
    author_id INTEGER NOT NULL REFERENCES users(id)
);
"""


def connect(db_path: Path) -> sqlite3.Connection:
    # FastAPI may run a sync dependency's setup/teardown and the endpoint on
    # different worker threads; each connection is still used by one request only.
    connection = sqlite3.connect(db_path, check_same_thread=False)
    connection.row_factory = sqlite3.Row
    connection.execute("PRAGMA foreign_keys = ON")
    return connection


def init_schema(db_path: Path) -> None:
    connection = connect(db_path)
    try:
        connection.executescript(SCHEMA)
    finally:
        connection.close()


def get_connection(request: Request) -> Iterator[sqlite3.Connection]:
    """Request-scoped connection. Writers commit with `with connection:`."""
    connection = connect(request.app.state.settings.db_path)
    try:
        yield connection
    finally:
        connection.close()
