"""External API contract checks. Run once per isolated candidate process."""
import argparse
from concurrent.futures import ThreadPoolExecutor
from contextlib import ExitStack
from dataclasses import is_dataclass
import importlib
import io
import json
from pathlib import Path
import sys
import tempfile
import threading
import unittest
from unittest.mock import patch

parser = argparse.ArgumentParser()
parser.add_argument('--case', type=int, choices=(1, 2, 3), required=True)
parser.add_argument('--candidate', type=Path, required=True)
parser.add_argument('--output', type=Path, required=True)
args = parser.parse_args()
sys.path.insert(0, str(args.candidate.resolve()))
from fastapi.testclient import TestClient
from store.api import create_app
from store.db import initialize, session


class APIContract(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.path = str(Path(self.temp.name) / 'database.sqlite')
        initialize(self.path)
        self.app = create_app(self.path)
        self.client = TestClient(self.app, raise_server_exceptions=False)

    def tearDown(self):
        self.client.close()
        self.temp.cleanup()

    def headers(self, user='alice', key=None):
        value = {'Authorization': f'Bearer {user}'}
        if key is not None:
            value['Idempotency-Key'] = key
        return value

    def snapshot(self):
        with session(self.path) as connection:
            tables = ['users', 'products', 'orders', 'order_lines', 'stock_movements', 'cancel_requests']
            return {t: [tuple(r) for r in connection.execute(f'SELECT * FROM {t} ORDER BY rowid')] for t in tables}

    def cancel(self, order=10, user='alice', key='retry_1'):
        return self.client.post(f'/orders/{order}/cancel', headers=self.headers(user, key))


class Quotes(APIContract):
    def test_policy_amounts_and_real_checkout(self):
        examples = [
            ('alice', 'A', 2, 'SAVE500', (2002, 701, 700, 2001)),
            ('bob', 'B', 5, None, (12515, 0, 0, 12515)),
            ('alice', 'B', 5, None, (12515, 1252, 0, 11263)),
            ('alice', 'A', 1, None, (1001, 101, 700, 1600)),
        ]
        keys = ('subtotal_won', 'discount_won', 'shipping_won', 'total_won')
        for user, sku, quantity, coupon, values in examples:
            basket = {'lines': [{'sku': sku, 'quantity': quantity}], 'coupon_code': coupon}
            quoted = self.client.post('/quotes', headers=self.headers(user), json=basket)
            self.assertEqual(quoted.status_code, 200, quoted.text)
            self.assertEqual(quoted.json(), dict(zip(keys, values)))
            # Isolated DB per example avoids stock exhaustion contaminating expectations.
            with tempfile.TemporaryDirectory() as directory:
                path = str(Path(directory) / 'checkout.sqlite')
                initialize(path)
                with TestClient(create_app(path)) as client:
                    actual = client.post('/orders', headers=self.headers(user), json=basket)
                    self.assertEqual(actual.status_code, 201, actual.text)
                    self.assertEqual({k: actual.json()[k] for k in keys}, quoted.json())

    def test_database_has_no_quote_side_effects(self):
        before = self.snapshot()
        basket = {'lines': [{'sku': 'A', 'quantity': 2}], 'coupon_code': 'SAVE500'}
        for _ in range(3):
            response = self.client.post('/quotes', headers=self.headers(), json=basket)
            self.assertEqual(response.status_code, 200, response.text)
        self.assertEqual(self.snapshot(), before)

    def test_authoritative_identity_price_and_validation(self):
        basket = {'lines': [{'sku': 'A', 'quantity': 1, 'price_won': 1}], 'tier': 'vip', 'user_id': 1}
        response = self.client.post('/quotes', headers=self.headers('bob'), json=basket)
        self.assertEqual(response.status_code, 200, response.text)
        self.assertEqual(response.json()['total_won'], 1701)
        invalid = [[], [{'sku': 'A', 'quantity': 0}], [{'sku': 'A', 'quantity': True}], [{'sku': 'A', 'quantity': '2'}], [{'sku': 'A', 'quantity': 101}]]
        for lines in invalid:
            response = self.client.post('/quotes', headers=self.headers(), json={'lines': lines})
            self.assertEqual(response.status_code, 422, response.text)

    def test_missing_auth_and_product_coupon_errors(self):
        body = {'lines': [{'sku': 'A', 'quantity': 1}]}
        for headers in ({}, {'Authorization': 'Bearer nope'}):
            self.assertEqual(self.client.post('/quotes', headers=headers, json=body).status_code, 401)
        self.assertEqual(self.client.post('/quotes', headers=self.headers(), json={'lines': [{'sku': 'unknown', 'quantity': 1}]}).status_code, 404)
        body['coupon_code'] = 'invalid'
        self.assertEqual(self.client.post('/quotes', headers=self.headers(), json=body).status_code, 422)


class Cancellation(APIContract):
    def test_success_restores_all_lines_and_records_history(self):
        with session(self.path) as connection:
            with connection:
                connection.execute("INSERT INTO order_lines VALUES (10, 'B', 1)")
        response = self.cancel()
        self.assertEqual(response.status_code, 200, response.text)
        self.assertEqual(response.json(), {'id': 10, 'status': 'canceled'})
        with session(self.path) as connection:
            self.assertEqual(connection.execute('SELECT status FROM orders WHERE id=10').fetchone()[0], 'canceled')
            self.assertEqual([tuple(r) for r in connection.execute('SELECT sku, stock FROM products ORDER BY sku')], [('A', 12), ('B', 9)])
            self.assertEqual([tuple(r) for r in connection.execute('SELECT sku, quantity, reason FROM stock_movements WHERE order_id=10 ORDER BY sku')], [('A', 2, 'cancel'), ('B', 1, 'cancel')])
            self.assertEqual(connection.execute('SELECT count(*) FROM cancel_requests').fetchone()[0], 1)

    def test_permission_boundary_and_auth(self):
        before = self.snapshot()
        for order, user in ((20, 'alice'), (12, 'alice'), (999, 'alice'), (10, 'bob')):
            self.assertEqual(self.cancel(order, user).status_code, 404)
        self.assertEqual(self.client.post('/orders/10/cancel', headers={'Idempotency-Key': 'retry_1'}).status_code, 401)
        self.assertEqual(self.snapshot(), before)
        self.assertEqual(self.cancel(12, 'manager').status_code, 200)

    def test_key_validation(self):
        for key in (None, '', 'x' * 65, 'space key', '한글', 'abc!', 'a/b'):
            # HTTP header encoders reject non-ASCII before reaching the server.
            if key == '한글':
                continue
            response = self.cancel(key=key)
            self.assertEqual(response.status_code, 422, (key, response.text))
        self.assertEqual(self.cancel(key='Az_09-' * 10).status_code, 200)

    def test_retry_and_conflict_are_idempotent(self):
        original = self.cancel()
        self.assertEqual(original.status_code, 200, original.text)
        after = self.snapshot()
        for _ in range(3):
            retry = self.cancel()
            self.assertEqual(retry.status_code, 200, retry.text)
            self.assertEqual(retry.json(), original.json())
        self.assertEqual(self.cancel(11).status_code, 409)
        self.assertEqual(self.cancel(key='another').status_code, 409)
        self.assertEqual(self.snapshot(), after)
        # Keys belong to users; an unrelated user's same textual key is valid.
        self.assertEqual(self.cancel(12, 'charlie').status_code, 200)

    def test_failure_rolls_back_every_table(self):
        with session(self.path) as connection:
            connection.executescript("CREATE TRIGGER fail_movement BEFORE INSERT ON stock_movements BEGIN SELECT RAISE(ABORT, 'injected write failure'); END;")
        before = self.snapshot()
        response = self.cancel()
        self.assertGreaterEqual(response.status_code, 400)
        self.assertEqual(self.snapshot(), before)
        with session(self.path) as connection:
            connection.execute('DROP TRIGGER fail_movement')
        self.assertEqual(self.cancel().status_code, 200)

    def test_concurrent_same_key_is_applied_once(self):
        barrier = threading.Barrier(4)

        def request(_):
            with TestClient(self.app, raise_server_exceptions=False) as client:
                barrier.wait(timeout=10)
                response = client.post('/orders/10/cancel', headers=self.headers(key='parallel'))
                return response.status_code, response.json()

        with ThreadPoolExecutor(max_workers=4) as pool:
            results = list(pool.map(request, range(4)))
        self.assertEqual(results, [(200, {'id': 10, 'status': 'canceled'})] * 4)
        with session(self.path) as connection:
            self.assertEqual(connection.execute("SELECT stock FROM products WHERE sku='A'").fetchone()[0], 12)
            self.assertEqual(connection.execute('SELECT count(*) FROM stock_movements').fetchone()[0], 1)
            self.assertEqual(connection.execute('SELECT count(*) FROM cancel_requests').fetchone()[0], 1)

    def test_concurrent_different_keys_only_one_can_cancel(self):
        barrier = threading.Barrier(2)

        def request(index):
            with TestClient(self.app, raise_server_exceptions=False) as client:
                barrier.wait(timeout=10)
                return client.post('/orders/10/cancel', headers=self.headers(key=f'key{index}')).status_code

        with ThreadPoolExecutor(max_workers=2) as pool:
            codes = list(pool.map(request, range(2)))
        self.assertEqual(sorted(codes), [200, 409])
        with session(self.path) as connection:
            self.assertEqual(connection.execute("SELECT stock FROM products WHERE sku='A'").fetchone()[0], 12)
            self.assertEqual(connection.execute('SELECT count(*) FROM stock_movements').fetchone()[0], 1)


class Listings(APIContract):
    def get(self, user='alice', query=''):
        return self.client.get('/orders' + query, headers=self.headers(user))

    def test_owner_manager_tenant_scope_and_shape(self):
        for user, ids in (('alice', [11, 10]), ('bob', [20]), ('manager', [12, 11, 10]), ('charlie', [12])):
            response = self.get(user)
            self.assertEqual(response.status_code, 200, response.text)
            payload = response.json()
            self.assertEqual(set(payload), {'items', 'total', 'limit', 'offset'})
            self.assertEqual([r['id'] for r in payload['items']], ids)
            self.assertEqual(payload['total'], len(ids))
            self.assertEqual((payload['limit'], payload['offset']), (20, 0))
            for row in payload['items']:
                self.assertEqual(set(row), {'id', 'status', 'total_won'})

    def test_filter_count_and_pagination_order(self):
        with session(self.path) as connection:
            with connection:
                connection.execute("UPDATE orders SET status='canceled' WHERE id=10")
                connection.executemany('INSERT INTO orders VALUES (?,101,1,?,?)', [(i, 'paid' if i % 2 else 'canceled', 5000+i) for i in range(30, 60)])
        response = self.get(query='?status=paid&limit=3&offset=2')
        self.assertEqual(response.status_code, 200, response.text)
        self.assertEqual(response.json(), {'items': [{'id': i, 'status': 'paid', 'total_won': 5000+i} for i in (55, 53, 51)], 'total': 16, 'limit': 3, 'offset': 2})
        empty = self.get(query='?status=paid&limit=3&offset=999')
        self.assertEqual(empty.status_code, 200)
        self.assertEqual(empty.json(), {'items': [], 'total': 16, 'limit': 3, 'offset': 999})
        canceled = self.get(query='?status=canceled')
        self.assertEqual(canceled.json()['total'], 16)

    def test_bad_filters_and_auth(self):
        for query in ('?limit=0', '?limit=101', '?offset=-1', '?limit=x', '?status=draft', '?status=paid%27%20OR%201%3D1--'):
            self.assertEqual(self.get(query=query).status_code, 422, query)
        self.assertEqual(self.client.get('/orders').status_code, 401)
        self.assertEqual(self.client.get('/orders', headers={'Authorization': 'Bearer nope'}).status_code, 401)
        self.assertEqual(self.get(query='?limit=100&offset=0').status_code, 200)

    def test_listing_is_read_only(self):
        before = self.snapshot()
        for user in ('alice', 'bob', 'manager'):
            self.assertEqual(self.get(user, '?limit=1&offset=1').status_code, 200)
        self.assertEqual(self.snapshot(), before)


class Results(unittest.TextTestResult):
    def __init__(self, *a, **kw):
        super().__init__(*a, **kw)
        self.groups = []

    def addSuccess(self, test):
        super().addSuccess(test)
        self.groups.append({'text': test.id(), 'passed': True, 'evidence': 'External API/SQLite assertions passed.'})

    def addFailure(self, test, err):
        super().addFailure(test, err)
        self.groups.append({'text': test.id(), 'passed': False, 'evidence': self._exc_info_to_string(err, test)})

    def addError(self, test, err):
        super().addError(test, err)
        self.groups.append({'text': test.id(), 'passed': False, 'evidence': self._exc_info_to_string(err, test)})


loader = unittest.TestLoader()
suite = loader.loadTestsFromTestCase({1: Quotes, 2: Cancellation, 3: Listings}[args.case])
# Always run an independent copy of original regression tests, not a candidate's edited copy.
original_tests = Path(__file__).resolve().parent / 'fixture/tests'
suite.addTests(loader.discover(str(original_tests), pattern='test_existing.py'))
stream = io.StringIO()
result = unittest.TextTestRunner(stream=stream, resultclass=Results, verbosity=2).run(suite)
grading = {'case': args.case, 'expectations': result.groups, 'summary': {'passed': sum(g['passed'] for g in result.groups), 'failed': sum(not g['passed'] for g in result.groups), 'total': len(result.groups), 'pass_rate': sum(g['passed'] for g in result.groups) / len(result.groups)}, 'complete_success': result.wasSuccessful()}
args.output.parent.mkdir(parents=True, exist_ok=True)
args.output.write_text(json.dumps(grading, ensure_ascii=False, indent=2) + '\n', encoding='utf-8')
print(json.dumps({'case': args.case, **grading['summary'], 'complete_success': result.wasSuccessful()}))
sys.exit(0 if result.wasSuccessful() else 1)
