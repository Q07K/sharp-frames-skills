"""Check saved self-tests and unchanged baseline obligations; preserve an expected red."""

from pathlib import Path
import argparse
import json
import re
import shutil
import subprocess
import sys
import tempfile


def run(interpreter, cwd, test_path=None, select=None):
    command = [interpreter, '-m', 'pytest', '-q']
    if test_path:
        command.append(str(test_path))
    if select:
        command.extend(['-k', select])
    result = subprocess.run(command, cwd=cwd, capture_output=True, text=True, encoding='utf-8', errors='replace')
    output = result.stdout + result.stderr
    counts = {name: int(match.group(1)) if (match := re.search(r'(\d+) ' + name, output)) else 0 for name in ('passed', 'failed', 'skipped', 'deselected')}
    return {'command': command, 'exit_code': result.returncode, 'counts': counts, 'output': output}


def verify(interpreter):
    source = Path(__file__).resolve().parents[2] / 'examples/fastapi-short-prompt'
    checks = {condition + '-own': run(interpreter, source / condition) for condition in ('without-skill', 'with-skill', 'refactored')}
    with tempfile.TemporaryDirectory() as temporary:
        tests = Path(temporary) / 'baseline-tests'
        shutil.copytree(source / 'without-skill/tests', tests, ignore=shutil.ignore_patterns('__pycache__'))
        checks['original-tests-on-refactored'] = run(interpreter, source / 'refactored', tests)
    # This fault-injection regression was discovered by the cleanup process,
    # after original generation. It is exploratory evidence, not a frozen A/B score.
    with tempfile.TemporaryDirectory() as temporary:
        test = Path(temporary) / 'test_discovered_regression.py'
        shutil.copyfile(source / 'refactored/tests/test_api.py', test)
        checks['discovered-regression-on-original'] = run(interpreter, source / 'without-skill', test, 'failed_commit_is_not_reported_as_success')
    expected = {'without-skill-own': (0, 8, 0), 'with-skill-own': (0, 41, 0), 'refactored-own': (0, 9, 0), 'original-tests-on-refactored': (0, 8, 0), 'discovered-regression-on-original': (1, 0, 1)}
    for name, (code, passed, failed) in expected.items():
        actual = checks[name]
        if (actual['exit_code'], actual['counts']['passed'], actual['counts']['failed'], actual['counts']['skipped']) != (code, passed, failed, 0):
            raise ValueError('Recorded test outcome changed: ' + name + '\n' + actual['output'])
        print(name + ': ' + str(actual['counts']), flush=True)
    return checks


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('--python', default=sys.executable)
    parser.add_argument('--output', type=Path, required=True)
    args = parser.parse_args()
    checks = verify(args.python)
    args.output.write_text(json.dumps(checks, ensure_ascii=False, indent=2), encoding='utf-8')
