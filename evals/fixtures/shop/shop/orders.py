from dataclasses import asdict

from .pricing import Line, calculate_totals


class OrderStore:
    def __init__(self) -> None:
        self.orders: list[dict] = []

    def add(self, row: dict) -> int:
        self.orders.append(row)
        return len(self.orders)


def place_order(store: OrderStore, lines: list[Line], member: str, use_coupon: bool = False) -> dict:
    amounts = asdict(calculate_totals(lines, member, use_coupon))
    order_id = store.add(amounts)
    return {"id": order_id, **amounts}
