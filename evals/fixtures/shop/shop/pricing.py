from dataclasses import dataclass


@dataclass(frozen=True)
class Line:
    unit_price_won: int
    quantity: int


@dataclass(frozen=True)
class Totals:
    subtotal_won: int
    discount_won: int
    shipping_won: int
    total_won: int


def calculate_totals(lines: list[Line], member: str, use_coupon: bool = False) -> Totals:
    if member not in {"regular", "vip"}:
        raise ValueError("unknown member")
    if not lines:
        raise ValueError("empty basket")
    for line in lines:
        if type(line.unit_price_won) is not int or line.unit_price_won < 0:
            raise ValueError("invalid price")
        if type(line.quantity) is not int or line.quantity < 1:
            raise ValueError("invalid quantity")
    subtotal = sum(line.unit_price_won * line.quantity for line in lines)
    after_member = subtotal * 90 // 100 if member == "vip" else subtotal
    after_coupon = max(0, after_member - (5_000 if use_coupon else 0))
    shipping = 0 if after_coupon >= 50_000 else 3_000
    return Totals(subtotal, subtotal - after_coupon, shipping, after_coupon + shipping)
