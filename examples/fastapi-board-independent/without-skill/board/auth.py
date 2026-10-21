"""회원가입·로그인."""

import sqlite3
import time
from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, status

from .config import Settings
from .deps import Conn, get_settings
from .schemas import Credentials, TokenOut, UserOut
from .security import hash_password, new_token, token_fingerprint, verify_password

router = APIRouter(prefix="/auth", tags=["auth"])


@router.post("/register", status_code=status.HTTP_201_CREATED, response_model=UserOut)
def register(body: Credentials, conn: Conn) -> UserOut:
    password_hash = hash_password(body.password)
    try:
        with conn:
            cur = conn.execute(
                "INSERT INTO users (username, password_hash) VALUES (?, ?)",
                (body.username, password_hash),
            )
    except sqlite3.IntegrityError:
        raise HTTPException(status.HTTP_409_CONFLICT, "Username already exists")
    return UserOut(id=cur.lastrowid, username=body.username)


@router.post("/login", response_model=TokenOut)
def login(
    body: Credentials,
    conn: Conn,
    settings: Annotated[Settings, Depends(get_settings)],
) -> TokenOut:
    row = conn.execute(
        "SELECT id, password_hash FROM users WHERE username = ?", (body.username,)
    ).fetchone()
    if not verify_password(body.password, row["password_hash"] if row else None):
        raise HTTPException(status.HTTP_401_UNAUTHORIZED, "Invalid username or password")

    token = new_token()
    now = int(time.time())
    with conn:
        conn.execute("DELETE FROM sessions WHERE expires_at <= ?", (now,))
        conn.execute(
            "INSERT INTO sessions (token_fingerprint, user_id, expires_at) VALUES (?, ?, ?)",
            (token_fingerprint(token), row["id"], now + settings.session_ttl_seconds),
        )
    return TokenOut(access_token=token, expires_in=settings.session_ttl_seconds)
