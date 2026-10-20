"""Replay saved TDD/workflow evidence; no fresh agents or production calls."""
from pathlib import Path
import hashlib
import json
import os
import shutil
import subprocess
import sys
import tempfile
import zipfile

ROOT = Path(__file__).resolve().parent

def run(script, candidate, logs, name):
    result = subprocess.run([sys.executable, '-B', str(ROOT / script), str(candidate)],
                            cwd=candidate, env=os.environ.copy(), capture_output=True,
                            text=True, encoding='utf-8', timeout=90)
    (logs / (name + '.txt')).write_text(result.stdout + result.stderr, encoding='utf-8')
    rows = [line for line in result.stdout.splitlines() if line.startswith('{')]
    if not rows:
        raise RuntimeError(f'{name}: no summary\n{result.stdout}\n{result.stderr}')
    summary = json.loads(rows[-1])
    if result.returncode not in (0, 1) or (result.returncode == 0) != summary['successful']:
        raise AssertionError(f'{name}: unexpected exit/summary: {summary}')
    return summary

def require(condition, message):
    if not condition:
        raise AssertionError(message)

def test_files(path):
    return {p.relative_to(path).as_posix(): p.read_bytes() for p in (path / 'tests').rglob('test*.py')}

def replay(extraction, logs):
    observations = {}
    feature = extraction / 'feature'
    red = feature / 'evidence/03-contract-red'
    green = feature / 'evidence/04-contract-green'
    require(test_files(red) == test_files(green) == test_files(feature / 'input'), 'Red/green tests changed')
    require((red / 'app.py').read_bytes() == (feature / 'baseline/app.py').read_bytes(), 'Red implementation differs from baseline')
    require((green / 'app.py').read_bytes() == (feature / 'input/app.py').read_bytes(), 'Green differs from final implementation')
    for case in ('feature', 'test-only'):
        folder = extraction / case
        require((folder / 'input/tests/test_reads.py').read_bytes() == (folder / 'baseline/tests/test_reads.py').read_bytes(), f'{case}: original read tests changed')
        require((folder / 'input/README.md').read_bytes() == (folder / 'baseline/README.md').read_bytes(), f'{case}: contract changed')
    original_tests = test_files(feature / 'baseline')
    require(all(test_files(feature / 'input')[name] == value for name, value in original_tests.items()), 'Original feature tests lost')

    observations['feature_red'] = run('unittest_checks.py', red, logs, 'feature-red')
    value = observations['feature_red']
    require(not value['successful'] and value['failures'] > 0 and value['errors'] == 0 and value['skipped'] == 0, 'Red does not reproduce a real assertion failure')
    observations['feature_green'] = run('unittest_checks.py', green, logs, 'feature-green')
    value = observations['feature_green']
    require(value['successful'] and value['skipped'] == 0, 'Feature suite failed or skipped')
    observations['feature_external_contract'] = run('contract_checks.py', feature / 'input', logs, 'feature-contract')
    require(observations['feature_external_contract']['successful'], 'External feature contract failed')

    test_only = extraction / 'test-only'
    require((test_only / 'input/app.py').read_bytes() == (test_only / 'baseline/app.py').read_bytes(), 'Test-only case changed product')
    observations['test_only_original'] = run('unittest_checks.py', test_only / 'input', logs, 'test-only-original')
    value = observations['test_only_original']
    require(not value['successful'] and value['failures'] > 0 and value['errors'] == 0 and value['skipped'] == 0, 'Test-only case hid the defect or did not execute')
    variants = extraction / 'replay-variants'
    variants.mkdir()
    for variant in ('correct', 'mutant_owner', 'mutant_repeat', 'mutant_shipped'):
        target = variants / variant
        shutil.copytree(test_only / 'input', target)
        shutil.copy2(extraction / 'oracles' / (variant + '.py'), target / 'app.py')
        value = run('unittest_checks.py', target, logs, 'test-only-' + variant)
        observations['test_only_' + variant] = value
        require(value['errors'] == 0 and value['skipped'] == 0, variant + ': test execution blocked/skipped')
        require(value['successful'] if variant == 'correct' else not value['successful'] and value['failures'] > 0, variant + ': sensitivity expectation failed')

    review = extraction / 'review/input'
    observations['review_green_suite'] = run('unittest_checks.py', review, logs, 'review-suite')
    require(observations['review_green_suite']['successful'] and observations['review_green_suite']['skipped'] == 1, 'Review fixture no longer illustrates a misleading green suite')
    observations['review_external_contract'] = run('contract_checks.py', review, logs, 'review-contract')
    require(not observations['review_external_contract']['successful'] and observations['review_external_contract']['errors'] == 0, 'Review regression did not reproduce')
    return observations

def main():
    archive = ROOT / 'forward-evidence.zip'
    expected = (ROOT / 'archive-sha256.txt').read_text(encoding='utf-8').split()[0]
    require(hashlib.sha256(archive.read_bytes()).hexdigest() == expected, 'Archive hash mismatch')
    manifest = json.loads((ROOT / 'archive-manifest.json').read_text(encoding='utf-8'))
    with tempfile.TemporaryDirectory() as directory:
        extraction = Path(directory).resolve()
        with zipfile.ZipFile(archive) as z:
            members = z.infolist()
            require(len({m.filename for m in members}) == len(members), 'Duplicate archive member')
            require({m.filename for m in members} == set(manifest), 'Archive member set mismatch')
            for member in members:
                require((extraction / member.filename).resolve().is_relative_to(extraction), 'Unsafe archive path')
                require(hashlib.sha256(z.read(member)).hexdigest() == manifest[member.filename], 'Archive entry hash mismatch')
            z.extractall(extraction)
        logs = extraction / 'replay-logs'
        logs.mkdir()
        observed = replay(extraction, logs)
        expected_observations = json.loads((ROOT / 'checks.json').read_text(encoding='utf-8'))['replay_observations']
        require(observed == expected_observations, f'Saved observations differ: {json.dumps(observed)}')
        print(json.dumps({'saved_runs_replayed': len(observed), 'observations': observed, 'fresh_agents': False, 'causal_quality_uplift_established': False}, ensure_ascii=False))

if __name__ == '__main__':
    main()
