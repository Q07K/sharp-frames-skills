import unittest

from shop.orders import OrderStore, place_order
from shop.pricing import Line, calculate_totals
from shop.wholesale import shipping_fee_won


class ExistingBehavior(unittest.TestCase):
    def test_vip_coupon_boundary(self):
        self.assertEqual(calculate_totals([Line(60_000, 1)], "vip", True).total_won, 52_000)

    def test_coupon_never_creates_negative_price(self):
        self.assertEqual(calculate_totals([Line(4_000, 1)], "regular", True).total_won, 3_000)

    def test_order_persists_once(self):
        store = OrderStore()
        result = place_order(store, [Line(50_000, 1)], "regular")
        self.assertEqual(result["id"], 1)
        self.assertEqual(len(store.orders), 1)

    def test_empty_basket(self):
        with self.assertRaises(ValueError):
            calculate_totals([], "regular")

    def test_wholesale_boundary(self):
        self.assertEqual(shipping_fee_won(99_999), 5_000)
        self.assertEqual(shipping_fee_won(100_000), 0)


if __name__ == "__main__":
    unittest.main()
