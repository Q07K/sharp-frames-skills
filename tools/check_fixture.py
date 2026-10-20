"""External behavior checks for a copied evaluation candidate; no model required."""

import argparse
from contextlib import ExitStack
from dataclasses import asdict
import importlib
import io
import json
from pathlib import Path
import sys
import unittest
from unittest.mock import patch


def evaluate(case: int, path: Path) -> dict:
    sys.path.insert(0, str(path))
    orders = importlib.import_module("shop.orders")
    pricing = importlib.import_module("shop.pricing")
    wholesale = importlib.import_module("shop.wholesale")
    checks = []

    def record(name, operation):
        try:
            operation()
            checks.append({"name": name, "passed": True})
        except Exception as error:
            checks.append({"name": name, "passed": False, "error": str(error)})

    def equal(actual, expected):
        if actual != expected:
            raise AssertionError(f"Expected {expected!r}, got {actual!r}")

    retail_examples = [
        (60_000, "vip", True, {"subtotal_won": 60_000, "discount_won": 11_000, "shipping_won": 3_000, "total_won": 52_000}),
        (50_000, "regular", False, {"subtotal_won": 50_000, "discount_won": 0, "shipping_won": 0, "total_won": 50_000}),
        (4_000, "regular", True, {"subtotal_won": 4_000, "discount_won": 4_000, "shipping_won": 3_000, "total_won": 3_000}),
        (55_555, "vip", False, {"subtotal_won": 55_555, "discount_won": 5_556, "shipping_won": 3_000, "total_won": 52_999}),
        (55_556, "vip", False, {"subtotal_won": 55_556, "discount_won": 5_556, "shipping_won": 0, "total_won": 50_000}),
    ]

    def retail_preserved():
        for price, member, coupon, expected in retail_examples:
            lines = [pricing.Line(price, 1)]
            equal(asdict(pricing.calculate_totals(lines, member, coupon)), expected)
            store = orders.OrderStore()
            equal(orders.place_order(store, lines, member, coupon), {"id": 1, **expected})
            equal(store.orders, [expected])

    record("retail_and_order_behavior", retail_preserved)

    if case == 1:
        def preview_behavior():
            for price, member, coupon, expected in retail_examples:
                equal(orders.preview_order([pricing.Line(price, 1)], member, coupon), expected)
            equal(wholesale.shipping_fee_won(99_999), 5_000)
            equal(wholesale.shipping_fee_won(100_000), 0)

        def no_persistence():
            with patch.object(orders.OrderStore, "add", side_effect=AssertionError("preview attempted persistence")):
                with patch.object(orders, "place_order", side_effect=AssertionError("preview created order")):
                    orders.preview_order([pricing.Line(60_000, 1)], "vip", True)

        def uses_authoritative_policy():
            original = pricing.calculate_totals
            sentinel = pricing.Totals(123, 4, 5, 124)
            targets = []
            for module in list(sys.modules.values()):
                if module is not None and getattr(module, "__name__", "").startswith("shop"):
                    targets.extend((module, name) for name, value in list(vars(module).items()) if value is original)
            with ExitStack() as stack:
                for module, name in targets:
                    stack.enter_context(patch.object(module, name, return_value=sentinel))
                equal(orders.preview_order([pricing.Line(9_000, 1)], "regular"), asdict(sentinel))

        record("preview_boundary_amounts", preview_behavior)
        record("preview_does_not_create_orders", no_persistence)
        record("existing_pricing_policy_is_used", uses_authoritative_policy)
    else:
        def wholesale_boundaries():
            for amount, expected in [(0, 6_000), (100_000, 6_000), (119_999, 6_000), (120_000, 0), (120_001, 0)]:
                equal(wholesale.shipping_fee_won(amount), expected)

        def wholesale_validation():
            for value in (-1, True, 1.5, "100000", None):
                try:
                    wholesale.shipping_fee_won(value)
                except ValueError:
                    continue
                raise AssertionError(f"Expected ValueError for {value!r}")

        record("wholesale_new_boundaries", wholesale_boundaries)
        record("wholesale_invalid_input_preserved", wholesale_validation)

    suite = unittest.TestLoader().discover(str(path / "tests"))
    output = io.StringIO()
    run = unittest.TextTestRunner(stream=output).run(suite)
    checks.append({"name": "candidate_tests", "passed": run.wasSuccessful(), "tests_run": run.testsRun, "output": output.getvalue()})
    return {"case": case, "passed": all(c["passed"] for c in checks), "checks": checks}


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--case", type=int, choices=[1, 2], required=True)
    parser.add_argument("--path", type=Path, required=True)
    args = parser.parse_args()
    result = evaluate(args.case, args.path.resolve())
    print(json.dumps(result, ensure_ascii=False, indent=2))
    return 0 if result["passed"] else 1


if __name__ == "__main__":
    sys.exit(main())
