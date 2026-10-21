import sqlite3
from datetime import UTC, datetime
from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, Request, Response, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer

from app.db import get_db
from app.schemas import Credentials, TokenRead, UserRead
from app.security import hash_password, hash_session_token, new_session_token, verify_password

router = APIRouter(prefix="/auth", tags=["auth"])

Db = Annotated[sqlite3.Connection, Depends(get_db)]

_bearer = HTTPBearer(auto_error=False)


def utc_now() -> datetime:
    return datetime.now(UTC)


def _unauthorized(detail: str) -> HTTPException:
    return HTTPException(
        status.HTTP_401_UNAUTHORIZED, detail=detail, headers={"WWW-Authenticate": "Bearer"}
    )


def _session_token(
    credentials: Annotated[HTTPAuthorizationCredentials | None, Depends(_bearer)],
) -> str:
    if credentials is None:
        raise _unauthorized("Not authenticated")
    return credentials.credentials


def get_current_user(db: Db, token: Annotated[str, Depends(_session_token)]) -> UserRead:
    row = db.execute(
        """
        SELECT users.id, users.username, users.created_at, sessions.expires_at
        FROM sessions JOIN users ON users.id = sessions.user_id
        WHERE sessions.token_hash = ?
        """,
        (hash_session_token(token),),
    ).fetchone()
    if row is None or datetime.fromisoformat(row["expires_at"]) <= utc_now():
        raise _unauthorized("Invalid or expired token")
    return UserRead(id=row["id"], username=row["username"], created_at=row["created_at"])


CurrentUser = Annotated[UserRead, Depends(get_current_user)]


@router.post("/signup", status_code=status.HTTP_201_CREATED)
def signup(credentials: Credentials, db: Db) -> UserRead:
    created_at = utc_now()
    try:
        with db:
            cursor = db.execute(
                "INSERT INTO users (username, password_hash, created_at) VALUES (?, ?, ?)",
                (credentials.username, hash_password(credentials.password), created_at.isoformat()),
            )
    except sqlite3.IntegrityError:
        # The UNIQUE NOCASE constraint is the authority, so concurrent signups
        # for the same name cannot both succeed.
        raise HTTPException(status.HTTP_409_CONFLICT, detail="Username already taken") from None
    assert cursor.lastrowid is not None
    return UserRead(id=cursor.lastrowid, username=credentials.username, created_at=created_at)


@router.post("/login")
def login(credentials: Credentials, db: Db, request: Request) -> TokenRead:
    user = db.execute(
        "SELECT id, password_hash FROM users WHERE username = ?", (credentials.username,)
    ).fetchone()
    stored_hash = user["password_hash"] if user is not None else None
    if not verify_password(credentials.password, stored_hash):
        raise _unauthorized("Invalid username or password")

    token = new_session_token()
    expires_at = utc_now() + request.app.state.token_ttl
    with db:
        db.execute(
            "INSERT INTO sessions (token_hash, user_id, expires_at) VALUES (?, ?, ?)",
            (hash_session_token(token), user["id"], expires_at.isoformat()),
        )
    return TokenRead(access_token=token, expires_at=expires_at)


@router.post("/logout", status_code=status.HTTP_204_NO_CONTENT)
def logout(_user: CurrentUser, db: Db, token: Annotated[str, Depends(_session_token)]) -> Response:
    with db:
        db.execute("DELETE FROM sessions WHERE token_hash = ?", (hash_session_token(token),))
    return Response(status_code=status.HTTP_204_NO_CONTENT)


@router.get("/me")
def me(user: CurrentUser) -> UserRead:
    return user
