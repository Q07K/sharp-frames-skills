"""Public request and response contracts, shared by the routers."""

from typing import Annotated

from pydantic import BaseModel, ConfigDict, Field, StringConstraints


class Credentials(BaseModel):
    model_config = ConfigDict(extra="forbid")
    username: Annotated[str, StringConstraints(pattern=r"^[a-zA-Z0-9_]{3,32}$")]
    password: str = Field(min_length=8, max_length=128, repr=False)


class UserPublic(BaseModel):
    id: int
    username: str


class TokenPublic(BaseModel):
    access_token: str
    token_type: str = "bearer"
    expires_in: int


class PostInput(BaseModel):
    model_config = ConfigDict(extra="forbid")
    title: Annotated[str, StringConstraints(strip_whitespace=True, min_length=1, max_length=120)]
    content: Annotated[str, StringConstraints(strip_whitespace=True, min_length=1, max_length=5000)]


class PostPublic(BaseModel):
    id: int
    title: str
    content: str
    author_id: int
