import sqlite3
from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, Query, Response, status

from app.db import get_db
from app.schemas import PostCreate, PostList, PostOut, PostUpdate
from app.security import CurrentUser, utcnow

router = APIRouter(prefix="/posts", tags=["posts"])

Db = Annotated[sqlite3.Connection, Depends(get_db)]

SELECT_POST = """
SELECT p.id, p.title, p.content, p.author_id, u.username AS author_username,
       p.created_at, p.updated_at
FROM posts p JOIN users u ON u.id = p.author_id
"""


def _get_post_or_404(db: sqlite3.Connection, post_id: int) -> sqlite3.Row:
    row = db.execute(SELECT_POST + " WHERE p.id = ?", (post_id,)).fetchone()
    if row is None:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Post not found")
    return row


def _ensure_author(post: sqlite3.Row, user: sqlite3.Row) -> None:
    if post["author_id"] != user["id"]:
        raise HTTPException(status.HTTP_403_FORBIDDEN, "Only the author can modify this post")


@router.get("", response_model=PostList)
def list_posts(
    db: Db,
    limit: Annotated[int, Query(ge=1, le=100)] = 20,
    offset: Annotated[int, Query(ge=0)] = 0,
    author_id: int | None = None,
):
    where, params = "", []
    if author_id is not None:
        where, params = " WHERE p.author_id = ?", [author_id]
    total = db.execute("SELECT COUNT(*) FROM posts p" + where, params).fetchone()[0]
    rows = db.execute(
        SELECT_POST + where + " ORDER BY p.id DESC LIMIT ? OFFSET ?",
        [*params, limit, offset],
    ).fetchall()
    return {"items": [dict(r) for r in rows], "total": total, "limit": limit, "offset": offset}


@router.post("", response_model=PostOut, status_code=status.HTTP_201_CREATED)
def create_post(body: PostCreate, user: CurrentUser, db: Db):
    now = utcnow().isoformat()
    cur = db.execute(
        "INSERT INTO posts (title, content, author_id, created_at, updated_at) VALUES (?, ?, ?, ?, ?)",
        (body.title, body.content, user["id"], now, now),
    )
    return dict(_get_post_or_404(db, cur.lastrowid))


@router.get("/{post_id}", response_model=PostOut)
def get_post(post_id: int, db: Db):
    return dict(_get_post_or_404(db, post_id))


@router.patch("/{post_id}", response_model=PostOut)
def update_post(post_id: int, body: PostUpdate, user: CurrentUser, db: Db):
    post = _get_post_or_404(db, post_id)
    _ensure_author(post, user)
    db.execute(
        "UPDATE posts SET title = ?, content = ?, updated_at = ? WHERE id = ?",
        (
            body.title if body.title is not None else post["title"],
            body.content if body.content is not None else post["content"],
            utcnow().isoformat(),
            post_id,
        ),
    )
    return dict(_get_post_or_404(db, post_id))


@router.delete("/{post_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_post(post_id: int, user: CurrentUser, db: Db):
    post = _get_post_or_404(db, post_id)
    _ensure_author(post, user)
    db.execute("DELETE FROM posts WHERE id = ?", (post_id,))
    return Response(status_code=status.HTTP_204_NO_CONTENT)
