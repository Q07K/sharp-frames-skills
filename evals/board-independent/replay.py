"""Recheck saved independent submissions; does not generate or repair AI code."""

from pathlib import Path
import hashlib
import json
import subprocess
import sys
import tempfile
import zipfile

ROOT = Path(__file__).resolve().parent
REPO = ROOT.parents[1]


def normalized(payload):
    return payload.decode('utf-8').replace('\r\n', '\n')


def main():
    archive = ROOT / 'evidence-2026-10-21.zip'
    expected = (ROOT / 'archive-sha256.txt').read_text().split()[0]
    if hashlib.sha256(archive.read_bytes()).hexdigest() != expected:
        raise ValueError('Evidence archive hash mismatch')
    with zipfile.ZipFile(archive) as z:
        frozen = json.loads(z.read('frozen/pre-generation-sha256.json'))['files']
        for name in ('REQUIREMENTS.md', 'evaluate.py', 'protocol.json'):
            payload = z.read('frozen/' + name)
            if hashlib.sha256(payload).hexdigest() != frozen['evals/board-independent/' + name]:
                raise ValueError('Frozen input hash mismatch: ' + name)
            if normalized((ROOT / name).read_bytes()) != normalized(payload):
                raise ValueError('Frozen input changed: ' + name)
        records = json.loads(z.read('observations.json'))
        for record in records:
            label = record['condition'].replace('_', '-')
            candidate = REPO / 'examples/fastapi-board-independent' / label
            for name, digest in record['files_sha256'].items():
                payload = z.read('submissions/' + label + '/' + name)
                if hashlib.sha256(payload).hexdigest() != digest:
                    raise ValueError('Archived source hash mismatch: ' + label + '/' + name)
                if normalized((candidate / name).read_bytes()) != normalized(payload):
                    raise ValueError('Submitted source changed: ' + label + '/' + name)
            with tempfile.TemporaryDirectory() as workspace:
                result_path = Path(workspace) / 'result.json'
                result = subprocess.run([sys.executable, '-X', 'utf8', str(ROOT / 'evaluate.py'),
                                         '--candidate', str(candidate), '--python', sys.executable,
                                         '--output', str(result_path)])
                if not result_path.exists():
                    raise ValueError('Evaluation did not produce a result: ' + label)
                actual = json.loads(result_path.read_text(encoding='utf-8'))
            saved = json.loads(z.read('results/' + label + '.json'))
            actual_cases = {k: v['passed'] for k, v in actual['cases'].items()}
            saved_cases = {k: v['passed'] for k, v in saved['cases'].items()}
            if actual_cases != saved_cases or actual['tests_run'] != saved['tests_run']:
                raise ValueError('Recorded outcome changed: ' + label)
            if result.returncode not in (0, 1):
                raise ValueError('Unexpected evaluator exit code: ' + label)
            print(label + ': recorded external HTTP outcomes reproduced', flush=True)


if __name__ == '__main__':
    main()
