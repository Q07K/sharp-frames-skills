"""Password hashing, session token identity and trusted current user."""

import hashlib
import sqlite3
import time

from fastapi import Depends, HTTPException
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from pwdlib import PasswordHash

from .db import get_db
from .schemas import UserPublic

password_hash = PasswordHash.recommended()
dummy_hash = password_hash.hash("dummy-password-for-missing-users")
bearer = HTTPBearer(auto_error=False)
SESSION_SECONDS = 3600


def token_digest(token: str) -> str:
    return hashlib.sha256(token.encode()).hexdigest()


def get_current_user(
    credentials: HTTPAuthorizationCredentials | None = Depends(bearer),
    db: sqlite3.Connection = Depends(get_db),
) -> UserPublic:
    if credentials is not None:
        digest = token_digest(credentials.credentials)
        row = db.execute(
            "SELECT users.id, users.username FROM sessions JOIN users ON users.id = sessions.user_id "
            "WHERE sessions.token_hash = ? AND sessions.expires_at > ?",
            (digest, int(time.time())),
        ).fetchone()
        if row is not None:
            return UserPublic(**dict(row))
    raise HTTPException(401, "Authentication required", headers={"WWW-Authenticate": "Bearer"})
