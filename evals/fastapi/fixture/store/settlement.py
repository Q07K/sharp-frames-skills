from dataclasses import asdict, dataclass
from fastapi import HTTPException


@dataclass(frozen=True)
class Breakdown:
    subtotal_won: int
    discount_won: int
    shipping_won: int
    total_won: int


def price_basket(connection, actor, basket) -> Breakdown:
    subtotal = 0
    for line in basket.lines:
        product = connection.execute('SELECT * FROM products WHERE sku = ?', (line.sku,)).fetchone()
        if product is None:
            raise HTTPException(404, 'Product not found')
        subtotal += product['price_won'] * line.quantity
    discounted = subtotal * 9 // 10 if actor.tier == 'vip' else subtotal
    if basket.coupon_code is not None:
        if basket.coupon_code != 'SAVE500':
            raise HTTPException(422, 'Invalid coupon')
        discounted = max(0, discounted - 500)
    shipping = 0 if discounted >= 10000 else 700
    return Breakdown(subtotal, subtotal - discounted, shipping, discounted + shipping)
