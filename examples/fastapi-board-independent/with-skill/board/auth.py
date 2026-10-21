import hashlib
import secrets
import sqlite3
from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, Request, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from pwdlib import PasswordHash
from pwdlib.hashers.argon2 import Argon2Hasher
from pydantic import BaseModel, Field

from board.db import get_connection

router = APIRouter(prefix="/auth", tags=["auth"])

password_hasher = PasswordHash((Argon2Hasher(),))
# Verified for unknown usernames so both login failures cost one Argon2 check.
DUMMY_PASSWORD_HASH = password_hasher.hash(secrets.token_urlsafe(16))


class Credentials(BaseModel):
    # Pattern is ASCII-only on purpose: \w would also accept non-English letters.
    username: Annotated[str, Field(pattern=r"^[A-Za-z0-9_]{3,32}$")]
    password: Annotated[str, Field(min_length=8, max_length=128)]


class User(BaseModel):
    id: int
    username: str


class TokenOut(BaseModel):
    access_token: str
    token_type: str = "bearer"
    expires_in: int


def token_fingerprint(token: str) -> str:
    # Tokens carry 256 random bits, so an unsalted fast hash is sufficient here.
    return hashlib.sha256(token.encode()).hexdigest()


@router.post("/register", status_code=status.HTTP_201_CREATED, response_model=User)
def register(
    credentials: Credentials,
    connection: Annotated[sqlite3.Connection, Depends(get_connection)],
) -> User:
    password_hash = password_hasher.hash(credentials.password)
    try:
        with connection:
            cursor = connection.execute(
                "INSERT INTO users (username, password_hash) VALUES (?, ?)",
                (credentials.username, password_hash),
            )
    except sqlite3.IntegrityError:
        # The UNIQUE constraint is the authority, so concurrent registrations race safely.
        raise HTTPException(status.HTTP_409_CONFLICT, "Username already exists") from None
    user_id = cursor.lastrowid
    assert user_id is not None
    return User(id=user_id, username=credentials.username)


@router.post("/login", response_model=TokenOut)
def login(
    credentials: Credentials,
    request: Request,
    connection: Annotated[sqlite3.Connection, Depends(get_connection)],
) -> TokenOut:
    user = connection.execute(
        "SELECT id, password_hash FROM users WHERE username = ?",
        (credentials.username,),
    ).fetchone()
    stored_hash = user["password_hash"] if user else DUMMY_PASSWORD_HASH
    password_ok = password_hasher.verify(credentials.password, stored_hash)
    if user is None or not password_ok:
        raise HTTPException(status.HTTP_401_UNAUTHORIZED, "Invalid username or password")

    ttl_seconds: int = request.app.state.settings.session_ttl_seconds
    now: float = request.app.state.clock()
    token = secrets.token_urlsafe(32)
    with connection:
        connection.execute("DELETE FROM sessions WHERE expires_at <= ?", (now,))
        connection.execute(
            "INSERT INTO sessions (token_fingerprint, user_id, expires_at) VALUES (?, ?, ?)",
            (token_fingerprint(token), user["id"], now + ttl_seconds),
        )
    return TokenOut(access_token=token, expires_in=ttl_seconds)


bearer_scheme = HTTPBearer(auto_error=False)


def unauthorized(detail: str) -> HTTPException:
    return HTTPException(
        status.HTTP_401_UNAUTHORIZED, detail, headers={"WWW-Authenticate": "Bearer"}
    )


def require_user(
    request: Request,
    credentials: Annotated[HTTPAuthorizationCredentials | None, Depends(bearer_scheme)],
    connection: Annotated[sqlite3.Connection, Depends(get_connection)],
) -> User:
    """Resolve the caller from a live session token, or raise 401 with a Bearer challenge."""
    if credentials is None or not credentials.credentials:
        raise unauthorized("Not authenticated")
    now: float = request.app.state.clock()
    row = connection.execute(
        """
        SELECT users.id, users.username
        FROM sessions JOIN users ON users.id = sessions.user_id
        WHERE sessions.token_fingerprint = ? AND sessions.expires_at > ?
        """,
        (token_fingerprint(credentials.credentials), now),
    ).fetchone()
    if row is None:
        raise unauthorized("Invalid or expired token")
    return User(id=row["id"], username=row["username"])
