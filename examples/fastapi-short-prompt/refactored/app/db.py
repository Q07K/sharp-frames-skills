import os
import sqlite3
from collections.abc import Iterator
from contextlib import closing
from typing import Annotated

from fastapi import Depends

SCHEMA = """
CREATE TABLE IF NOT EXISTS users (
    id            INTEGER PRIMARY KEY AUTOINCREMENT,
    username      TEXT NOT NULL UNIQUE COLLATE NOCASE,
    password_hash TEXT NOT NULL,
    created_at    TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS sessions (
    token_hash TEXT PRIMARY KEY,
    user_id    INTEGER NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    expires_at TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS posts (
    id         INTEGER PRIMARY KEY AUTOINCREMENT,
    title      TEXT NOT NULL,
    content    TEXT NOT NULL,
    author_id  INTEGER NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    created_at TEXT NOT NULL,
    updated_at TEXT NOT NULL
);

CREATE INDEX IF NOT EXISTS idx_sessions_user ON sessions(user_id);
CREATE INDEX IF NOT EXISTS idx_posts_author ON posts(author_id);
"""


def database_path() -> str:
    return os.environ.get("DATABASE_PATH", "app.db")


def connect() -> sqlite3.Connection:
    conn = sqlite3.connect(database_path(), check_same_thread=False)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA foreign_keys = ON")
    return conn


def init_db() -> None:
    # sqlite3.Connection의 with 블록은 트랜잭션만 끝내고 닫지는 않는다.
    with closing(connect()) as conn:
        conn.executescript(SCHEMA)


def get_db() -> Iterator[sqlite3.Connection]:
    """요청 단위 커넥션. 예외 없이 끝나면 commit, 아니면 rollback."""
    conn = connect()
    try:
        yield conn
        conn.commit()
    except Exception:
        conn.rollback()
        raise
    finally:
        conn.close()


# scope="function": 응답을 보내기 전에 commit해야 commit 실패가 성공 응답으로 나가지 않는다.
# 같은 요청 안에서 인증과 핸들러가 한 커넥션을 공유하도록 모든 곳에서 이 별칭을 쓴다.
DbConnection = Annotated[sqlite3.Connection, Depends(get_db, scope="function")]
