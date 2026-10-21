"""Account registration and login HTTP routes."""

import secrets
import sqlite3
import time

from fastapi import APIRouter, Depends, HTTPException

from ..auth import SESSION_SECONDS, dummy_hash, password_hash, token_digest
from ..db import get_db
from ..schemas import Credentials, TokenPublic, UserPublic

router = APIRouter(tags=["auth"])


@router.post("/auth/register", response_model=UserPublic, status_code=201)
def register(data: Credentials, db: sqlite3.Connection = Depends(get_db)):
    try:
        cursor = db.execute("INSERT INTO users (username, password_hash) VALUES (?, ?)",
                            (data.username, password_hash.hash(data.password)))
        db.commit()
    except sqlite3.IntegrityError:
        db.rollback()
        raise HTTPException(409, "Username already exists") from None
    return {"id": cursor.lastrowid, "username": data.username}


@router.post("/auth/login", response_model=TokenPublic)
def login(data: Credentials, db: sqlite3.Connection = Depends(get_db)):
    user = db.execute("SELECT * FROM users WHERE username = ?", (data.username,)).fetchone()
    valid = password_hash.verify(data.password, user["password_hash"] if user else dummy_hash)
    if user is None or not valid:
        raise HTTPException(401, "Invalid credentials", headers={"WWW-Authenticate": "Bearer"})
    token = secrets.token_urlsafe(32)
    db.execute("INSERT INTO sessions (token_hash, user_id, expires_at) VALUES (?, ?, ?)",
               (token_digest(token), user["id"], int(time.time()) + SESSION_SECONDS))
    db.commit()
    return TokenPublic(access_token=token, expires_in=SESSION_SECONDS)
