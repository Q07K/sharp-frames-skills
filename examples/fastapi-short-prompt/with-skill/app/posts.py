import sqlite3
from typing import Annotated

from fastapi import APIRouter, HTTPException, Query, Response, status

from app.auth import CurrentUser, Db, utc_now
from app.schemas import AuthorRead, PostCreate, PostPage, PostRead, PostUpdate

router = APIRouter(prefix="/posts", tags=["posts"])

_SELECT_POST = """
    SELECT posts.id, posts.title, posts.content, posts.created_at, posts.updated_at,
           users.id AS author_id, users.username AS author_username
    FROM posts JOIN users ON users.id = posts.author_id
"""


def _to_post(row: sqlite3.Row) -> PostRead:
    return PostRead(
        id=row["id"],
        title=row["title"],
        content=row["content"],
        author=AuthorRead(id=row["author_id"], username=row["author_username"]),
        created_at=row["created_at"],
        updated_at=row["updated_at"],
    )


def _get_post_or_404(db: sqlite3.Connection, post_id: int) -> PostRead:
    row = db.execute(f"{_SELECT_POST} WHERE posts.id = ?", (post_id,)).fetchone()
    if row is None:
        raise HTTPException(status.HTTP_404_NOT_FOUND, detail="Post not found")
    return _to_post(row)


def _require_author(post: PostRead, user: CurrentUser) -> None:
    if post.author.id != user.id:
        raise HTTPException(status.HTTP_403_FORBIDDEN, detail="Only the author can modify this post")


@router.get("")
def list_posts(
    db: Db,
    limit: Annotated[int, Query(ge=1, le=100)] = 20,
    offset: Annotated[int, Query(ge=0)] = 0,
) -> PostPage:
    rows = db.execute(
        f"{_SELECT_POST} ORDER BY posts.id DESC LIMIT ? OFFSET ?", (limit, offset)
    ).fetchall()
    total = db.execute("SELECT COUNT(*) FROM posts").fetchone()[0]
    return PostPage(items=[_to_post(row) for row in rows], total=total, limit=limit, offset=offset)


@router.post("", status_code=status.HTTP_201_CREATED)
def create_post(payload: PostCreate, user: CurrentUser, db: Db) -> PostRead:
    now = utc_now().isoformat()
    with db:
        cursor = db.execute(
            "INSERT INTO posts (author_id, title, content, created_at, updated_at)"
            " VALUES (?, ?, ?, ?, ?)",
            (user.id, payload.title, payload.content, now, now),
        )
    assert cursor.lastrowid is not None
    return _get_post_or_404(db, cursor.lastrowid)


@router.get("/{post_id}")
def get_post(post_id: int, db: Db) -> PostRead:
    return _get_post_or_404(db, post_id)


@router.patch("/{post_id}")
def update_post(post_id: int, payload: PostUpdate, user: CurrentUser, db: Db) -> PostRead:
    post = _get_post_or_404(db, post_id)
    _require_author(post, user)
    changes = payload.model_dump(exclude_unset=True)
    with db:
        # author_id in the WHERE clause keeps the write scoped to the author even
        # if the row changed after the check; a concurrent delete yields 404.
        cursor = db.execute(
            "UPDATE posts SET title = ?, content = ?, updated_at = ?"
            " WHERE id = ? AND author_id = ?",
            (
                changes.get("title", post.title),
                changes.get("content", post.content),
                utc_now().isoformat(),
                post_id,
                user.id,
            ),
        )
    if cursor.rowcount == 0:
        raise HTTPException(status.HTTP_404_NOT_FOUND, detail="Post not found")
    return _get_post_or_404(db, post_id)


@router.delete("/{post_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_post(post_id: int, user: CurrentUser, db: Db) -> Response:
    post = _get_post_or_404(db, post_id)
    _require_author(post, user)
    with db:
        db.execute("DELETE FROM posts WHERE id = ? AND author_id = ?", (post_id, user.id))
    return Response(status_code=status.HTTP_204_NO_CONTENT)
