from pydantic import BaseModel, Field


class LineInput(BaseModel):
    sku: str = Field(min_length=1)
    quantity: int = Field(strict=True, gt=0, le=100)


class BasketInput(BaseModel):
    lines: list[LineInput] = Field(min_length=1, max_length=50)
    coupon_code: str | None = None
