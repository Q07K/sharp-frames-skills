"""게시글 CRUD."""

import sqlite3
from typing import Annotated

from fastapi import APIRouter, HTTPException, Query, Response, status

from .db import SQLITE_MAX_INT
from .deps import Conn, CurrentUserId
from .schemas import PostIn, PostOut

router = APIRouter(prefix="/posts", tags=["posts"])


def _to_post(row: sqlite3.Row) -> PostOut:
    return PostOut(id=row["id"], title=row["title"], content=row["content"], author_id=row["author_id"])


def _get_post_row(conn: sqlite3.Connection, post_id: int) -> sqlite3.Row:
    # SQLite 정수 범위를 벗어난 ID는 존재할 수 없으므로 조회 없이 404로 처리한다.
    row = None
    if 1 <= post_id <= SQLITE_MAX_INT:
        row = conn.execute(
            "SELECT id, title, content, author_id FROM posts WHERE id = ?", (post_id,)
        ).fetchone()
    if row is None:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Post not found")
    return row


def _get_own_post_row(conn: sqlite3.Connection, post_id: int, user_id: int) -> sqlite3.Row:
    row = _get_post_row(conn, post_id)
    if row["author_id"] != user_id:
        raise HTTPException(status.HTTP_403_FORBIDDEN, "Only the author can modify this post")
    return row


@router.post("", status_code=status.HTTP_201_CREATED, response_model=PostOut)
def create_post(body: PostIn, conn: Conn, user_id: CurrentUserId) -> PostOut:
    with conn:
        cur = conn.execute(
            "INSERT INTO posts (title, content, author_id) VALUES (?, ?, ?)",
            (body.title, body.content, user_id),
        )
    return PostOut(id=cur.lastrowid, title=body.title, content=body.content, author_id=user_id)


@router.get("", response_model=list[PostOut])
def list_posts(
    conn: Conn,
    limit: Annotated[int, Query(ge=1, le=100)] = 20,
    offset: Annotated[int, Query(ge=0, le=SQLITE_MAX_INT)] = 0,
) -> list[PostOut]:
    rows = conn.execute(
        "SELECT id, title, content, author_id FROM posts ORDER BY id ASC LIMIT ? OFFSET ?",
        (limit, offset),
    ).fetchall()
    return [_to_post(row) for row in rows]


@router.get("/{post_id}", response_model=PostOut)
def get_post(post_id: int, conn: Conn) -> PostOut:
    return _to_post(_get_post_row(conn, post_id))


@router.put("/{post_id}", response_model=PostOut)
def update_post(post_id: int, body: PostIn, conn: Conn, user_id: CurrentUserId) -> PostOut:
    with conn:
        # 작성자 확인과 수정을 하나의 쓰기 트랜잭션에서 수행한다.
        conn.execute("BEGIN IMMEDIATE")
        row = _get_own_post_row(conn, post_id, user_id)
        conn.execute(
            "UPDATE posts SET title = ?, content = ? WHERE id = ?",
            (body.title, body.content, row["id"]),
        )
    return PostOut(id=row["id"], title=body.title, content=body.content, author_id=user_id)


@router.delete("/{post_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_post(post_id: int, conn: Conn, user_id: CurrentUserId) -> Response:
    with conn:
        conn.execute("BEGIN IMMEDIATE")
        row = _get_own_post_row(conn, post_id, user_id)
        conn.execute("DELETE FROM posts WHERE id = ?", (row["id"],))
    return Response(status_code=status.HTTP_204_NO_CONTENT)
