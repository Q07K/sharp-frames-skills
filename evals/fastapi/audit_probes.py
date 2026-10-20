"""Post-hoc probes prompted by independent grader audit; original grades unchanged."""
import argparse
import json
from pathlib import Path
import sys
import tempfile
import unittest

parser = argparse.ArgumentParser()
parser.add_argument('--case', type=int, choices=(1, 2, 3), required=True)
parser.add_argument('--candidate', type=Path, required=True)
parser.add_argument('--output', type=Path, required=True)
args = parser.parse_args()
sys.path.insert(0, str(args.candidate.resolve()))
from fastapi.testclient import TestClient
from store.api import create_app
from store.db import initialize, session


class AuditProbes(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.path = str(Path(self.temp.name) / 'audit.sqlite')
        initialize(self.path)
        self.client = TestClient(create_app(self.path), raise_server_exceptions=False)
        self.headers = {'Authorization': 'Bearer alice', 'Idempotency-Key': 'audit-key'}

    def tearDown(self):
        self.client.close()
        self.temp.cleanup()

    def snapshot(self):
        with session(self.path) as connection:
            return {t: [tuple(r) for r in connection.execute(f'SELECT * FROM {t} ORDER BY rowid')] for t in ('users', 'products', 'orders', 'order_lines', 'stock_movements', 'cancel_requests')}

    def probe_quote_zero_floor_and_shipping_after_discount(self):
        with session(self.path) as connection:
            with connection:
                connection.execute("INSERT INTO products VALUES ('SMALL',100,5)")
        before = self.snapshot()
        for sku, count, coupon, expected in [('SMALL', 1, 'SAVE500', {'subtotal_won': 100, 'discount_won': 100, 'shipping_won': 700, 'total_won': 700}), ('B', 4, None, {'subtotal_won': 10012, 'discount_won': 1002, 'shipping_won': 700, 'total_won': 9710})]:
            response = self.client.post('/quotes', headers=self.headers, json={'lines': [{'sku': sku, 'quantity': count}], 'coupon_code': coupon})
            self.assertEqual(response.status_code, 200, response.text)
            self.assertEqual(response.json(), expected)
        self.assertEqual(self.snapshot(), before)

    def probe_cancel_late_write_failure_rolls_back(self):
        with session(self.path) as connection:
            connection.executescript("CREATE TRIGGER fail_request BEFORE INSERT ON cancel_requests BEGIN SELECT RAISE(ABORT, 'injected late failure'); END;")
        before = self.snapshot()
        response = self.client.post('/orders/10/cancel', headers=self.headers)
        self.assertGreaterEqual(response.status_code, 400)
        self.assertEqual(self.snapshot(), before)
        with session(self.path) as connection:
            connection.execute('DROP TRIGGER fail_request')
        self.assertEqual(self.client.post('/orders/10/cancel', headers=self.headers).status_code, 200)

    def probe_cancel_persisted_key_result(self):
        response = self.client.post('/orders/10/cancel', headers=self.headers)
        self.assertEqual(response.status_code, 200, response.text)
        with session(self.path) as connection:
            row = connection.execute('SELECT user_id,request_key,order_id,response_json FROM cancel_requests').fetchone()
        self.assertIsNotNone(row)
        self.assertEqual(tuple(row[:3]), (1, 'audit-key', 10))
        self.assertEqual(json.loads(row[3]), {'id': 10, 'status': 'canceled'})

    def probe_list_canceled_items_and_unequal_counts(self):
        with session(self.path) as connection:
            with connection:
                connection.execute("UPDATE orders SET status='canceled' WHERE id=10")
                connection.execute("INSERT INTO orders VALUES (30,101,1,'paid',3333)")
        response = self.client.get('/orders?status=canceled', headers=self.headers)
        self.assertEqual(response.status_code, 200, response.text)
        self.assertEqual(response.json(), {'items': [{'id': 10, 'status': 'canceled', 'total_won': 8000}], 'total': 1, 'limit': 20, 'offset': 0})


names = {1: ['probe_quote_zero_floor_and_shipping_after_discount'], 2: ['probe_cancel_late_write_failure_rolls_back', 'probe_cancel_persisted_key_result'], 3: ['probe_list_canceled_items_and_unequal_counts']}[args.case]
checks = []
for name in names:
    result = unittest.TestResult()
    AuditProbes(name).run(result)
    checks.append({'text': name, 'passed': result.wasSuccessful(), 'evidence': 'Post-hoc API/SQLite audit probe passed.' if result.wasSuccessful() else '\n'.join(e for _, e in result.errors + result.failures)})
output = {'case': args.case, 'post_hoc': True, 'all_passed': all(c['passed'] for c in checks), 'checks': checks}
args.output.write_text(json.dumps(output, ensure_ascii=False, indent=2) + '\n', encoding='utf-8')
print(json.dumps({'case': args.case, 'post_hoc': True, 'all_passed': output['all_passed']}))
sys.exit(0 if output['all_passed'] else 1)
