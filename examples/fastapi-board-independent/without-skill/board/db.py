"""SQLite 연결과 스키마."""

import sqlite3
from pathlib import Path

# SQLite INTEGER의 최댓값. 이보다 큰 값을 바인딩하면 OverflowError가 난다.
SQLITE_MAX_INT = 2**63 - 1

SCHEMA = """
CREATE TABLE IF NOT EXISTS users (
    id            INTEGER PRIMARY KEY AUTOINCREMENT,
    username      TEXT    NOT NULL UNIQUE,
    password_hash TEXT    NOT NULL
);

CREATE TABLE IF NOT EXISTS sessions (
    token_fingerprint TEXT    PRIMARY KEY,
    user_id           INTEGER NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    expires_at        INTEGER NOT NULL
);
CREATE INDEX IF NOT EXISTS idx_sessions_expires_at ON sessions(expires_at);

CREATE TABLE IF NOT EXISTS posts (
    id        INTEGER PRIMARY KEY AUTOINCREMENT,
    title     TEXT    NOT NULL,
    content   TEXT    NOT NULL,
    author_id INTEGER NOT NULL REFERENCES users(id) ON DELETE CASCADE
);
"""


def connect(db_path: Path) -> sqlite3.Connection:
    # 요청마다 새 연결을 열고, FastAPI 스레드풀에서 다른 스레드가 닫을 수 있게 한다.
    conn = sqlite3.connect(db_path, timeout=10, check_same_thread=False)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA foreign_keys = ON")
    return conn


def init_db(db_path: Path) -> None:
    db_path.parent.mkdir(parents=True, exist_ok=True)
    conn = connect(db_path)
    try:
        conn.execute("PRAGMA journal_mode = WAL")
        conn.executescript(SCHEMA)
        conn.commit()
    finally:
        conn.close()
