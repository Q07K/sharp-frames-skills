from dataclasses import dataclass
from fastapi import HTTPException


@dataclass(frozen=True)
class Actor:
    id: int
    tenant_id: int
    role: str
    tier: str


def authenticate(connection, authorization: str | None) -> Actor:
    if not authorization or not authorization.startswith("Bearer "):
        raise HTTPException(401, "Authentication required")
    row = connection.execute("SELECT * FROM users WHERE token = ?", (authorization[7:],)).fetchone()
    if row is None:
        raise HTTPException(401, "Invalid token")
    return Actor(row['id'], row['tenant_id'], row['role'], row['tier'])
