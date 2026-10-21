"""Reproduce the saved short-prompt submissions without another model call."""

from pathlib import Path
import argparse
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
    parser = argparse.ArgumentParser()
    parser.add_argument('--output', type=Path)
    args = parser.parse_args()
    observations, differences = {}, []
    archive = ROOT / 'evidence-2026-10-21.zip'
    if hashlib.sha256(archive.read_bytes()).hexdigest() != (ROOT / 'archive-sha256.txt').read_text().split()[0]:
        raise ValueError('Evidence archive hash mismatch')
    with zipfile.ZipFile(archive) as z:
        pre = json.loads(z.read('frozen/pre-generation-sha256.json'))
        for name, digest in pre.items():
            member = 'frozen/protocol.json' if name.endswith('protocol.json') else 'evaluated-skill/' + name.split('skills/sharp-frames-development/')[1]
            if hashlib.sha256(z.read(member)).hexdigest() != digest:
                raise ValueError('Pre-generation fingerprint mismatch: ' + name)
        cleanup = json.loads(z.read('frozen/cleanup-frozen.json'))
        for name, digest in cleanup['checks'].items():
            member = 'results/without-skill.json' if name == 'without-skill-results.json' else 'frozen/' + name
            if hashlib.sha256(z.read(member)).hexdigest() != digest:
                raise ValueError('Pre-cleanup fingerprint mismatch: ' + name)
        for name in ('protocol.json', 'evaluate.py', 'adapters.json', 'baseline-openapi.json', 'cleanup-frozen.json', 'verify.py'):
            if normalized((ROOT / name).read_bytes()) != normalized(z.read('frozen/' + name)):
                raise ValueError('Saved check changed: ' + name)
        submissions = json.loads(z.read('observations.json'))
        for record in submissions:
            condition = record['condition']
            candidate = REPO / 'examples/fastapi-short-prompt' / condition
            for name, digest in record['files_sha256'].items():
                payload = z.read('submissions/' + condition + '/' + name)
                if hashlib.sha256(payload).hexdigest() != digest or normalized((candidate / name).read_bytes()) != normalized(payload):
                    raise ValueError('Submission changed: ' + condition + '/' + name)
                if condition == 'without-skill' and cleanup['baseline'][name] != digest:
                    raise ValueError('Original baseline changed: ' + name)
            with tempfile.TemporaryDirectory() as temporary:
                output = Path(temporary) / 'result.json'
                result = subprocess.run([sys.executable, '-X', 'utf8', str(ROOT / 'evaluate.py'), '--candidate', str(candidate), '--python', sys.executable, '--condition', condition, '--output', str(output)])
                actual = json.loads(output.read_text(encoding='utf-8'))
            saved = json.loads(z.read('results/' + condition + '.json'))
            observations[condition] = actual
            if result.returncode != 0 or actual['cases'] != saved['cases'] or actual['tests_run'] != saved['tests_run']:
                differences.append(condition)
                print(condition + ': HTTP outcomes DIFFER from first run; failure retained', flush=True)
            else:
                print(condition + ': saved HTTP outcomes reproduced', flush=True)
        with tempfile.TemporaryDirectory() as temporary:
            output = Path(temporary) / 'operator.json'
            result = subprocess.run([sys.executable, '-X', 'utf8', str(ROOT / 'verify.py'), '--output', str(output)])
            actual = json.loads(output.read_text(encoding='utf-8'))
        saved = json.loads(z.read('results/operator-checks.json'))
        if result.returncode != 0 or {key: (value['exit_code'], value['counts']) for key, value in actual.items()} != {key: (value['exit_code'], value['counts']) for key, value in saved.items()}:
            raise ValueError('Saved self-test / unchanged baseline / discovered regression outcomes changed')
        print('Self-tests, original obligations and expected failing regression reproduced.', flush=True)
    if args.output:
        args.output.write_text(json.dumps(observations, ensure_ascii=False, indent=2), encoding='utf-8')
    if differences:
        raise SystemExit('HTTP outcomes changed: ' + ', '.join(differences))


if __name__ == '__main__':
    main()
