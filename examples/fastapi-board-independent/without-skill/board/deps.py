"""라우터가 공유하는 의존성: DB 연결, 설정, 현재 사용자."""

import sqlite3
import time
from collections.abc import Iterator
from typing import Annotated

from fastapi import Depends, HTTPException, Request, status

from .config import Settings
from .db import connect
from .security import token_fingerprint


def get_settings(request: Request) -> Settings:
    return request.app.state.settings


def get_conn(request: Request) -> Iterator[sqlite3.Connection]:
    conn = connect(request.app.state.settings.db_path)
    try:
        yield conn
    finally:
        conn.close()


Conn = Annotated[sqlite3.Connection, Depends(get_conn)]


def _unauthorized(detail: str) -> HTTPException:
    return HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail=detail,
        headers={"WWW-Authenticate": "Bearer"},
    )


def get_current_user_id(request: Request, conn: Conn) -> int:
    header = request.headers.get("Authorization")
    if not header:
        raise _unauthorized("Not authenticated")
    scheme, _, token = header.partition(" ")
    token = token.strip()
    if scheme.lower() != "bearer" or not token:
        raise _unauthorized("Invalid authentication credentials")

    row = conn.execute(
        "SELECT user_id, expires_at FROM sessions WHERE token_fingerprint = ?",
        (token_fingerprint(token),),
    ).fetchone()
    if row is None or row["expires_at"] <= int(time.time()):
        raise _unauthorized("Invalid or expired token")
    return row["user_id"]


CurrentUserId = Annotated[int, Depends(get_current_user_id)]
