import sqlite3
from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, Query, Response, status
from pydantic import BaseModel, ConfigDict, StringConstraints

from board.auth import User, require_user
from board.db import SQLITE_INTEGER_MAX, SQLITE_INTEGER_MIN, get_connection

router = APIRouter(prefix="/posts", tags=["posts"])

Connection = Annotated[sqlite3.Connection, Depends(get_connection)]
CurrentUser = Annotated[User, Depends(require_user)]

Title = Annotated[str, StringConstraints(strip_whitespace=True, min_length=1, max_length=120)]
Content = Annotated[
    str, StringConstraints(strip_whitespace=True, min_length=1, max_length=5000)
]


class PostIn(BaseModel):
    # author_id and other unknown fields are rejected; the author comes from the token.
    model_config = ConfigDict(extra="forbid")

    title: Title
    content: Content


class Post(BaseModel):
    id: int
    title: str
    content: str
    author_id: int


def find_post(connection: sqlite3.Connection, post_id: int) -> Post | None:
    # IDs outside SQLite's range cannot exist; binding them would raise OverflowError.
    if not SQLITE_INTEGER_MIN <= post_id <= SQLITE_INTEGER_MAX:
        return None
    row = connection.execute(
        "SELECT id, title, content, author_id FROM posts WHERE id = ?", (post_id,)
    ).fetchone()
    return Post(**row) if row else None


def find_own_post(connection: sqlite3.Connection, post_id: int, user: User) -> Post:
    """Return the post if `user` wrote it; 404 if it does not exist, 403 otherwise."""
    post = find_post(connection, post_id)
    if post is None:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Post not found")
    if post.author_id != user.id:
        raise HTTPException(status.HTTP_403_FORBIDDEN, "Only the author can modify this post")
    return post


def raise_if_deleted_concurrently(cursor: sqlite3.Cursor) -> None:
    # The ownership check and the write are separate statements; another request
    # may delete the post in between. author_id never changes, so 404 is the only race.
    if cursor.rowcount == 0:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Post not found")


@router.post("", status_code=status.HTTP_201_CREATED, response_model=Post)
def create_post(post_in: PostIn, user: CurrentUser, connection: Connection) -> Post:
    with connection:
        cursor = connection.execute(
            "INSERT INTO posts (title, content, author_id) VALUES (?, ?, ?)",
            (post_in.title, post_in.content, user.id),
        )
    post_id = cursor.lastrowid
    assert post_id is not None
    return Post(id=post_id, title=post_in.title, content=post_in.content, author_id=user.id)


@router.get("", response_model=list[Post])
def list_posts(
    connection: Connection,
    limit: Annotated[int, Query(ge=1, le=100)] = 20,
    offset: Annotated[int, Query(ge=0, le=SQLITE_INTEGER_MAX)] = 0,
) -> list[Post]:
    rows = connection.execute(
        "SELECT id, title, content, author_id FROM posts ORDER BY id LIMIT ? OFFSET ?",
        (limit, offset),
    ).fetchall()
    return [Post(**row) for row in rows]


@router.get("/{post_id}", response_model=Post)
def get_post(post_id: int, connection: Connection) -> Post:
    post = find_post(connection, post_id)
    if post is None:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Post not found")
    return post


@router.put("/{post_id}", response_model=Post)
def update_post(
    post_id: int, post_in: PostIn, user: CurrentUser, connection: Connection
) -> Post:
    with connection:
        post = find_own_post(connection, post_id, user)
        cursor = connection.execute(
            "UPDATE posts SET title = ?, content = ? WHERE id = ?",
            (post_in.title, post_in.content, post.id),
        )
    raise_if_deleted_concurrently(cursor)
    return post.model_copy(update={"title": post_in.title, "content": post_in.content})


@router.delete("/{post_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_post(post_id: int, user: CurrentUser, connection: Connection) -> Response:
    with connection:
        post = find_own_post(connection, post_id, user)
        cursor = connection.execute("DELETE FROM posts WHERE id = ?", (post.id,))
    raise_if_deleted_concurrently(cursor)
    return Response(status_code=status.HTTP_204_NO_CONTENT)
