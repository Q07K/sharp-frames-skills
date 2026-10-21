from datetime import datetime

from pydantic import BaseModel, Field, model_validator

Username = Field(min_length=3, max_length=30, pattern=r"^[A-Za-z0-9_]+$")


class SignupRequest(BaseModel):
    username: str = Username
    password: str = Field(min_length=8, max_length=128)


class LoginRequest(BaseModel):
    username: str = Field(min_length=1, max_length=30)
    password: str = Field(min_length=1, max_length=128)


class TokenResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"
    expires_at: datetime


class UserOut(BaseModel):
    id: int
    username: str
    created_at: datetime


class PostCreate(BaseModel):
    title: str = Field(min_length=1, max_length=200)
    content: str = Field(min_length=1, max_length=20_000)


class PostUpdate(BaseModel):
    title: str | None = Field(default=None, min_length=1, max_length=200)
    content: str | None = Field(default=None, min_length=1, max_length=20_000)

    @model_validator(mode="after")
    def at_least_one_field(self) -> "PostUpdate":
        if self.title is None and self.content is None:
            raise ValueError("title 또는 content 중 하나 이상 필요합니다.")
        return self


class PostOut(BaseModel):
    id: int
    title: str
    content: str
    author_id: int
    author_username: str
    created_at: datetime
    updated_at: datetime


class PostList(BaseModel):
    items: list[PostOut]
    total: int
    limit: int
    offset: int
