"""요청·응답 모델."""

from typing import Annotated, Literal

from pydantic import BaseModel, ConfigDict, Field, StringConstraints

Username = Annotated[str, Field(pattern=r"^[A-Za-z0-9_]{3,32}$")]
Password = Annotated[str, Field(min_length=8, max_length=128)]
Title = Annotated[str, StringConstraints(strip_whitespace=True, min_length=1, max_length=120)]
Content = Annotated[str, StringConstraints(strip_whitespace=True, min_length=1, max_length=5000)]


class Credentials(BaseModel):
    username: Username
    password: Password


class UserOut(BaseModel):
    id: int
    username: str


class TokenOut(BaseModel):
    access_token: str
    token_type: Literal["bearer"] = "bearer"
    expires_in: int


class PostIn(BaseModel):
    model_config = ConfigDict(extra="forbid")

    title: Title
    content: Content


class PostOut(BaseModel):
    id: int
    title: str
    content: str
    author_id: int
