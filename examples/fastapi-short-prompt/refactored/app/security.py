import hashlib
import os
import secrets
import sqlite3
from datetime import datetime, timedelta, timezone
from typing import Annotated

from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from pwdlib import PasswordHash

from app.db import DbConnection

TOKEN_TTL = timedelta(minutes=int(os.environ.get("TOKEN_TTL_MINUTES", "60")))

password_hash = PasswordHash.recommended()
# 존재하지 않는 사용자로 로그인할 때도 해시 검증 시간을 소모해 사용자 존재 여부 유추를 막는다.
_DUMMY_HASH = password_hash.hash("dummy-password-for-timing")

bearer_scheme = HTTPBearer(auto_error=False)


def utcnow() -> datetime:
    return datetime.now(timezone.utc)


def hash_password(password: str) -> str:
    return password_hash.hash(password)


def verify_password(password: str, hashed: str | None) -> bool:
    if hashed is None:
        password_hash.verify(password, _DUMMY_HASH)
        return False
    return password_hash.verify(password, hashed)


def _hash_token(token: str) -> str:
    # DB가 유출돼도 토큰 원문을 바로 쓸 수 없도록 해시만 저장한다.
    return hashlib.sha256(token.encode()).hexdigest()


def create_session(db: sqlite3.Connection, user_id: int) -> tuple[str, datetime]:
    token = secrets.token_urlsafe(32)
    now = utcnow()
    expires_at = now + TOKEN_TTL
    db.execute("DELETE FROM sessions WHERE expires_at <= ?", (now.isoformat(),))
    db.execute(
        "INSERT INTO sessions (token_hash, user_id, expires_at) VALUES (?, ?, ?)",
        (_hash_token(token), user_id, expires_at.isoformat()),
    )
    return token, expires_at


def delete_session(db: sqlite3.Connection, token: str) -> None:
    db.execute("DELETE FROM sessions WHERE token_hash = ?", (_hash_token(token),))


def unauthorized(detail: str) -> HTTPException:
    return HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail=detail,
        headers={"WWW-Authenticate": "Bearer"},
    )


def get_token(
    credentials: Annotated[HTTPAuthorizationCredentials | None, Depends(bearer_scheme)],
) -> str:
    if credentials is None or credentials.scheme.lower() != "bearer":
        raise unauthorized("Not authenticated")
    return credentials.credentials


def get_current_user(
    token: Annotated[str, Depends(get_token)],
    db: DbConnection,
) -> sqlite3.Row:
    row = db.execute(
        """
        SELECT u.id, u.username, u.created_at, s.expires_at
        FROM sessions s JOIN users u ON u.id = s.user_id
        WHERE s.token_hash = ?
        """,
        (_hash_token(token),),
    ).fetchone()
    if row is None or datetime.fromisoformat(row["expires_at"]) <= utcnow():
        raise unauthorized("Invalid or expired token")
    return row


CurrentUser = Annotated[sqlite3.Row, Depends(get_current_user)]
