"""Post lookup and the shared author-only modification policy."""

import sqlite3

from fastapi import HTTPException


def get_post(db: sqlite3.Connection, post_id: int) -> dict:
    post = db.execute("SELECT * FROM posts WHERE id = ?", (post_id,)).fetchone()
    if post is None:
        raise HTTPException(404, "Post not found")
    return dict(post)


def get_owned_post(db: sqlite3.Connection, post_id: int, user_id: int) -> dict:
    post = get_post(db, post_id)
    if post["author_id"] != user_id:
        raise HTTPException(403, "Only the author can change this post")
    return post
