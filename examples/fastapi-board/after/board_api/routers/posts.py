"""Public reads and authenticated post writes."""

import sqlite3

from fastapi import APIRouter, Depends, Query, Response

from ..auth import get_current_user
from ..db import get_db
from ..post_access import get_owned_post, get_post
from ..schemas import PostInput, PostPublic, UserPublic

router = APIRouter(tags=["posts"])


@router.get("/posts", response_model=list[PostPublic])
def list_posts(limit: int = Query(20, ge=1, le=100), offset: int = Query(0, ge=0),
               db: sqlite3.Connection = Depends(get_db)):
    rows = db.execute("SELECT * FROM posts ORDER BY id LIMIT ? OFFSET ?", (limit, offset)).fetchall()
    return [dict(row) for row in rows]


@router.get("/posts/{post_id}", response_model=PostPublic)
def read_post(post_id: int, db: sqlite3.Connection = Depends(get_db)):
    return get_post(db, post_id)


@router.post("/posts", response_model=PostPublic, status_code=201)
def create_post(data: PostInput, user: UserPublic = Depends(get_current_user),
                db: sqlite3.Connection = Depends(get_db)):
    cursor = db.execute("INSERT INTO posts (title, content, author_id) VALUES (?, ?, ?)",
                        (data.title, data.content, user.id))
    db.commit()
    return {"id": cursor.lastrowid, **data.model_dump(), "author_id": user.id}


@router.put("/posts/{post_id}", response_model=PostPublic)
def update_post(post_id: int, data: PostInput, user: UserPublic = Depends(get_current_user),
                db: sqlite3.Connection = Depends(get_db)):
    get_owned_post(db, post_id, user.id)
    db.execute("UPDATE posts SET title = ?, content = ? WHERE id = ?", (data.title, data.content, post_id))
    db.commit()
    return {"id": post_id, **data.model_dump(), "author_id": user.id}


@router.delete("/posts/{post_id}", status_code=204)
def delete_post(post_id: int, user: UserPublic = Depends(get_current_user),
                db: sqlite3.Connection = Depends(get_db)):
    get_owned_post(db, post_id, user.id)
    db.execute("DELETE FROM posts WHERE id = ?", (post_id,))
    db.commit()
    return Response(status_code=204)
