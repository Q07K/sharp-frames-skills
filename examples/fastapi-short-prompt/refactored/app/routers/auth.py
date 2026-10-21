import sqlite3
from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, Response, status

from app.db import DbConnection
from app.schemas import LoginRequest, SignupRequest, TokenResponse, UserOut
from app.security import (
    CurrentUser,
    create_session,
    delete_session,
    get_token,
    hash_password,
    unauthorized,
    utcnow,
    verify_password,
)

router = APIRouter(prefix="/auth", tags=["auth"])


@router.post("/signup", response_model=UserOut, status_code=status.HTTP_201_CREATED)
def signup(body: SignupRequest, db: DbConnection):
    try:
        cur = db.execute(
            "INSERT INTO users (username, password_hash, created_at) VALUES (?, ?, ?)",
            (body.username, hash_password(body.password), utcnow().isoformat()),
        )
    except sqlite3.IntegrityError:
        raise HTTPException(status.HTTP_409_CONFLICT, "Username already exists")
    row = db.execute(
        "SELECT id, username, created_at FROM users WHERE id = ?", (cur.lastrowid,)
    ).fetchone()
    return dict(row)


@router.post("/login", response_model=TokenResponse)
def login(body: LoginRequest, db: DbConnection):
    user = db.execute(
        "SELECT id, password_hash FROM users WHERE username = ?", (body.username,)
    ).fetchone()
    if not verify_password(body.password, user["password_hash"] if user else None):
        raise unauthorized("Incorrect username or password")
    token, expires_at = create_session(db, user["id"])
    return TokenResponse(access_token=token, expires_at=expires_at)


@router.post("/logout", status_code=status.HTTP_204_NO_CONTENT)
def logout(_: CurrentUser, token: Annotated[str, Depends(get_token)], db: DbConnection):
    delete_session(db, token)
    return Response(status_code=status.HTTP_204_NO_CONTENT)


@router.get("/me", response_model=UserOut)
def me(user: CurrentUser):
    return {"id": user["id"], "username": user["username"], "created_at": user["created_at"]}
