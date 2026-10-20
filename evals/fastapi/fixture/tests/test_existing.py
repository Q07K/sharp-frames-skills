import tempfile
import unittest
from pathlib import Path
from fastapi.testclient import TestClient
from store.api import create_app
from store.db import initialize, session


class ExistingBehavior(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.path = str(Path(self.temp.name) / 'store.sqlite')
        initialize(self.path)
        self.client = TestClient(create_app(self.path))
        self.headers = {'Authorization': 'Bearer alice'}

    def tearDown(self):
        self.client.close()
        self.temp.cleanup()

    def test_order_policy_and_stock(self):
        response = self.client.post('/orders', headers=self.headers, json={'lines': [{'sku': 'A', 'quantity': 2}], 'coupon_code': 'SAVE500'})
        self.assertEqual(response.status_code, 201)
        self.assertEqual(response.json()['total_won'], 2001)
        with session(self.path) as connection:
            self.assertEqual(connection.execute("SELECT stock FROM products WHERE sku='A'").fetchone()[0], 8)

    def test_access_boundary(self):
        self.assertEqual(self.client.get('/orders/20', headers=self.headers).status_code, 404)
        self.assertEqual(self.client.get('/orders/12', headers=self.headers).status_code, 404)
        self.assertEqual(self.client.get('/orders/12', headers={'Authorization': 'Bearer manager'}).status_code, 200)
        self.assertEqual(self.client.get('/orders/10').status_code, 401)

    def test_rollback_and_validation(self):
        response = self.client.post('/orders', headers=self.headers, json={'lines': [{'sku': 'B', 'quantity': 1}, {'sku': 'A', 'quantity': 99}]})
        self.assertEqual(response.status_code, 409)
        with session(self.path) as connection:
            self.assertEqual(connection.execute('SELECT count(*) FROM orders').fetchone()[0], 4)
            self.assertEqual(connection.execute("SELECT stock FROM products WHERE sku='B'").fetchone()[0], 8)
        response = self.client.post('/orders', headers=self.headers, json={'lines': [{'sku': 'A', 'quantity': True}]})
        self.assertEqual(response.status_code, 422)


if __name__ == '__main__':
    unittest.main()
