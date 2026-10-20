"""Independent assertions for the synthetic cancellation contract, not an agent test."""
from contextlib import closing
from pathlib import Path
import importlib.util
import json
import sqlite3
import sys
import tempfile
import unittest

spec = importlib.util.spec_from_file_location('candidate_app', Path(sys.argv[1]) / 'app.py')
module = importlib.util.module_from_spec(spec)
spec.loader.exec_module(module)
from fastapi.testclient import TestClient

ALICE = {'X-Session': 'alice-session'}
BOB = {'X-Session': 'bob-session'}
SUPPORT = {'X-Session': 'support-session'}

class Contract(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.db = Path(self.temp.name) / 'orders.db'
        self.client = TestClient(module.create_app(self.db), raise_server_exceptions=False)
        self.addCleanup(self.client.close)

    def state(self):
        with closing(sqlite3.connect(self.db)) as conn:
            return (conn.execute('SELECT * FROM orders ORDER BY id').fetchall(),
                    conn.execute('SELECT * FROM inventory ORDER BY sku').fetchall())

    def stock(self):
        return self.state()[1][0][1]

    def test_customer_repeat_and_cross_persona_reads(self):
        self.assertEqual([r['id'] for r in self.client.get('/orders', headers=ALICE).json()], [1, 3])
        self.assertEqual(self.client.get('/orders/1', headers=ALICE).json()['status'], 'reserved')
        for _ in range(2):
            response = self.client.post('/orders/1/cancel', headers=ALICE)
            self.assertEqual(response.status_code, 200, response.text)
            self.assertEqual(response.json(), {'id': 1, 'status': 'cancelled'})
            self.assertEqual(self.stock(), 5)
            self.assertEqual(self.client.get('/orders/1', headers=ALICE).json()['status'], 'cancelled')
        self.assertEqual(self.client.get('/orders/2', headers=BOB).json()['status'], 'reserved')
        self.assertEqual(self.client.get('/orders/1', headers=BOB).status_code, 404)
        self.assertEqual(self.client.get('/orders/1', headers=SUPPORT).json()['status'], 'cancelled')

    def test_other_customer_denial_then_own_action(self):
        before = self.state()
        self.assertEqual(self.client.post('/orders/1/cancel', headers=BOB).status_code, 404)
        self.assertEqual(self.state(), before)
        self.assertEqual(self.client.get('/orders/1', headers=BOB).status_code, 404)
        self.assertEqual(self.client.post('/orders/2/cancel', headers=BOB).status_code, 200)
        self.assertEqual(self.stock(), 4)
        self.assertEqual(self.client.get('/orders/1', headers=ALICE).json()['status'], 'reserved')

    def test_support_reads_but_cannot_write(self):
        self.assertEqual(len(self.client.get('/orders', headers=SUPPORT).json()), 3)
        before = self.state()
        self.assertEqual(self.client.post('/orders/1/cancel', headers=SUPPORT).status_code, 403)
        self.assertEqual(self.state(), before)
        self.assertEqual(self.client.get('/orders/1', headers=SUPPORT).json()['status'], 'reserved')
        self.assertEqual(self.client.post('/orders/1/cancel', headers=ALICE).status_code, 200)

    def test_anonymous_and_invalid_session_have_no_effect(self):
        before = self.state()
        for headers in ({}, {'X-Session': 'unknown'}):
            self.assertEqual(self.client.post('/orders/1/cancel', headers=headers).status_code, 401)
            self.assertEqual(self.state(), before)
        self.assertEqual(self.client.post('/orders/1/cancel', headers=ALICE).status_code, 200)

    def test_shipped_denial_and_recovery(self):
        before = self.state()
        self.assertEqual(self.client.post('/orders/3/cancel', headers=ALICE).status_code, 409)
        self.assertEqual(self.state(), before)
        self.assertEqual(self.client.get('/orders/3', headers=ALICE).json()['status'], 'shipped')
        self.assertEqual(self.client.post('/orders/1/cancel', headers=ALICE).status_code, 200)
        self.assertEqual(self.stock(), 5)

    def test_missing_order_has_no_effect(self):
        before = self.state()
        self.assertEqual(self.client.post('/orders/999/cancel', headers=ALICE).status_code, 404)
        self.assertEqual(self.state(), before)

    def test_storage_failure_rolls_back_then_retry_recovers(self):
        with closing(sqlite3.connect(self.db)) as conn:
            conn.execute("CREATE TRIGGER fail_stock BEFORE UPDATE ON inventory BEGIN SELECT RAISE(ABORT, 'injected stock failure'); END")
            conn.commit()
        before = self.state()
        self.assertGreaterEqual(self.client.post('/orders/1/cancel', headers=ALICE).status_code, 400)
        self.assertEqual(self.state(), before)
        self.assertEqual(self.client.get('/orders/1', headers=ALICE).json()['status'], 'reserved')
        with closing(sqlite3.connect(self.db)) as conn:
            conn.execute('DROP TRIGGER fail_stock')
            conn.commit()
        self.assertEqual(self.client.post('/orders/1/cancel', headers=ALICE).status_code, 200)
        self.assertEqual(self.stock(), 5)

result = unittest.TextTestRunner(verbosity=2).run(unittest.defaultTestLoader.loadTestsFromTestCase(Contract))
print(json.dumps({'tests': result.testsRun, 'failures': len(result.failures), 'errors': len(result.errors), 'skipped': len(result.skipped), 'successful': result.wasSuccessful()}))
raise SystemExit(0 if result.wasSuccessful() else 1)
