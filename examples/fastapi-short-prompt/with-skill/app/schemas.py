from datetime import datetime
from typing import Annotated, Literal, Self

from pydantic import BaseModel, Field, StringConstraints, model_validator

Username = Annotated[str, StringConstraints(min_length=3, max_length=30, pattern=r"^[A-Za-z0-9_]+$")]
# Upper bound keeps Argon2 hashing cost bounded for hostile input.
Password = Annotated[str, Field(min_length=8, max_length=128)]
PostTitle = Annotated[str, StringConstraints(strip_whitespace=True, min_length=1, max_length=200)]
PostContent = Annotated[str, StringConstraints(min_length=1, max_length=10_000)]


class Credentials(BaseModel):
    username: Username
    password: Password


class UserRead(BaseModel):
    id: int
    username: str
    created_at: datetime


class TokenRead(BaseModel):
    access_token: str
    token_type: Literal["bearer"] = "bearer"
    expires_at: datetime


class PostCreate(BaseModel):
    title: PostTitle
    content: PostContent


class PostUpdate(BaseModel):
    """Partial update: omitted fields are kept; explicit null is rejected."""

    title: PostTitle | None = None
    content: PostContent | None = None

    @model_validator(mode="after")
    def _require_non_null_change(self) -> Self:
        if not self.model_fields_set:
            raise ValueError("At least one of title or content is required")
        for field_name in self.model_fields_set:
            if getattr(self, field_name) is None:
                raise ValueError(f"{field_name} cannot be null")
        return self


class AuthorRead(BaseModel):
    id: int
    username: str


class PostRead(BaseModel):
    id: int
    title: str
    content: str
    author: AuthorRead
    created_at: datetime
    updated_at: datetime


class PostPage(BaseModel):
    items: list[PostRead]
    total: int
    limit: int
    offset: int
