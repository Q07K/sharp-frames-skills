"""Post-generation interface adapters; predeclared semantic checks, no source repair."""

import argparse
import json
import os
from pathlib import Path
import socket
import subprocess
import tempfile
import time
import unittest

import httpx


class Flows(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.db = str(Path(self.temp.name) / 'board.db')
        self.process = None
        self.client = None
        self.addCleanup(self.stop)
        self.start()

    def start(self):
        with socket.socket() as sock:
            sock.bind(('127.0.0.1', 0))
            port = sock.getsockname()[1]
        command = [self.interpreter, '-m', 'uvicorn', self.adapter['entrypoint'], '--host', '127.0.0.1', '--port', str(port)]
        if self.adapter.get('factory'):
            command.append('--factory')
        self.process = subprocess.Popen(command, cwd=self.candidate, env=dict(os.environ, DATABASE_PATH=self.db, PYTHONUTF8='1'), stdout=subprocess.DEVNULL, stderr=subprocess.PIPE, text=True, encoding='utf-8', errors='replace', creationflags=getattr(subprocess, 'CREATE_NO_WINDOW', 0))
        self.client = httpx.Client(base_url=f'http://127.0.0.1:{port}', timeout=10)
        for _ in range(150):
            if self.process.poll() is not None:
                self.fail('Startup failed: ' + self.process.communicate(timeout=10)[1])
            try:
                if self.client.get('/openapi.json').status_code == 200:
                    return
            except httpx.TransportError:
                pass
            time.sleep(0.1)
        self.fail('Startup timed out')

    def stop(self):
        if self.client:
            self.client.close()
            self.client = None
        if self.process:
            if self.process.poll() is None:
                self.process.terminate()
            self.process.communicate(timeout=10)
            self.process = None

    def account(self, name='alice'):
        body = {'username': name, 'password': 'strong-password-123'}
        response = self.client.post(self.adapter['signup'], json=body)
        self.assertIn(response.status_code, (200, 201), response.text)
        self.assertNotIn('password', response.json())
        self.assertNotIn('password_hash', response.json())
        login = self.client.post(self.adapter['login'], json=body)
        self.assertEqual(login.status_code, 200, login.text)
        token = login.json()['access_token']
        self.assertTrue(token)
        return {'Authorization': 'Bearer ' + token}

    def post(self, headers):
        response = self.client.post('/posts', headers=headers, json={'title': 'First', 'content': 'Original'})
        self.assertIn(response.status_code, (200, 201), response.text)
        self.assertEqual(response.json()['title'], 'First')
        self.assertEqual(response.json()['content'], 'Original')
        return response.json()

    def update(self, post, headers):
        return self.client.request(self.adapter['update_method'], '/posts/' + str(post['id']), headers=headers, json={'title': 'Changed', 'content': 'Updated'})

    def test_login_and_crud(self):
        owner = self.account()
        post = self.post(owner)
        url = '/posts/' + str(post['id'])
        self.assertEqual(self.client.get(url).json(), post)
        listing = self.client.get('/posts')
        self.assertEqual(listing.status_code, 200, listing.text)
        items = listing.json()
        if self.adapter.get('list_key'):
            items = items[self.adapter['list_key']]
        self.assertIn(post, items)
        updated = self.update(post, owner)
        self.assertEqual(updated.status_code, 200, updated.text)
        self.assertEqual(updated.json()['title'], 'Changed')
        self.assertEqual(updated.json()['content'], 'Updated')
        self.assertEqual(self.client.get(url).json(), updated.json())
        self.assertIn(self.client.delete(url, headers=owner).status_code, (200, 204))
        self.assertEqual(self.client.get(url).status_code, 404)

    def test_wrong_password(self):
        self.account()
        response = self.client.post(self.adapter['login'], json={'username': 'alice', 'password': 'incorrect-password'})
        self.assertIn(response.status_code, (400, 401, 403), response.text)
        self.assertNotIn('access_token', response.json())

    def test_anonymous_denied_and_state_preserved(self):
        post = self.post(self.account())
        url = '/posts/' + str(post['id'])
        attempts = [self.client.post('/posts', json={'title': 'Intrusion', 'content': 'x'}), self.update(post, {}), self.client.delete(url)]
        for response in attempts:
            self.assertIn(response.status_code, (401, 403), response.text)
        self.assertEqual(self.client.get(url).json(), post)
        listing = self.client.get('/posts').json()
        items = listing[self.adapter['list_key']] if self.adapter.get('list_key') else listing
        self.assertEqual(len(items), 1)

    def test_other_author_denied_and_state_preserved(self):
        owner = self.account()
        post = self.post(owner)
        stranger = self.account('bob')
        url = '/posts/' + str(post['id'])
        self.assertIn(self.update(post, stranger).status_code, (403, 404))
        self.assertIn(self.client.delete(url, headers=stranger).status_code, (403, 404))
        self.assertEqual(self.client.get(url).json(), post)
        self.assertEqual(self.update(post, owner).status_code, 200)

    def test_forged_token_denied(self):
        post = self.post(self.account())
        url = '/posts/' + str(post['id'])
        response = self.client.delete(url, headers={'Authorization': 'Bearer forged-token'})
        self.assertIn(response.status_code, (401, 403), response.text)
        self.assertEqual(self.client.get(url).json(), post)

    def test_post_survives_restart(self):
        post = self.post(self.account())
        self.stop()
        self.start()
        self.assertEqual(self.client.get('/posts/' + str(post['id'])).json(), post)


class Compatibility(Flows):
    def test_frozen_openapi(self):
        expected = json.loads(self.schema.read_text(encoding='utf-8'))
        self.assertEqual(self.client.get('/openapi.json').json(), expected)


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--candidate', type=Path, required=True)
    parser.add_argument('--python', required=True)
    parser.add_argument('--condition', choices=('without-skill', 'with-skill', 'refactored'), required=True)
    parser.add_argument('--output', type=Path, required=True)
    parser.add_argument('--save-schema', type=Path)
    args = parser.parse_args()
    root = Path(__file__).resolve().parent
    adapter = json.loads((root / 'adapters.json').read_text())[args.condition]
    cls = Flows if args.condition == 'with-skill' else Compatibility
    cls.candidate, cls.interpreter, cls.adapter = args.candidate.resolve(), args.python, adapter
    cls.schema = root / 'baseline-openapi.json'
    if args.save_schema:
        probe = Flows()
        probe.candidate, probe.interpreter, probe.adapter = cls.candidate, cls.interpreter, cls.adapter
        try:
            probe.setUp()
            args.save_schema.write_text(json.dumps(probe.client.get('/openapi.json').json(), ensure_ascii=False, indent=2), encoding='utf-8')
        finally:
            probe.doCleanups()
    result = unittest.TextTestRunner(verbosity=2).run(unittest.defaultTestLoader.loadTestsFromTestCase(cls))
    failed = {test.id(): detail for test, detail in result.failures + result.errors}
    names = unittest.defaultTestLoader.getTestCaseNames(cls)
    payload = {'condition': args.condition, 'tests_run': result.testsRun, 'cases': {name: {'passed': not any(key.endswith('.' + name) for key in failed)} for name in names}, 'failures': failed}
    args.output.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding='utf-8')
    raise SystemExit(0 if result.wasSuccessful() else 1)


if __name__ == '__main__':
    main()
