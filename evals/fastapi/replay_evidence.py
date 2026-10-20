"""Recheck published candidates, not new model executions."""
import hashlib
import json
import os
from pathlib import Path
import subprocess
import sys
import tempfile
import zipfile


def main():
    root = Path(__file__).resolve().parent
    frozen = json.loads((root / 'pre-evaluation-sha256.json').read_text(encoding='utf-8'))
    for name, expected in frozen.items():
        if hashlib.sha256((root / name).read_bytes()).hexdigest() != expected:
            raise ValueError(f'Frozen protocol or checker differs: {name}')
    fixture = json.loads((root / 'fixture-sha256.json').read_text(encoding='utf-8'))
    for name, expected in fixture.items():
        if hashlib.sha256((root / 'fixture' / name).read_bytes()).hexdigest() != expected:
            raise ValueError(f'Frozen fixture differs: {name}')
    expected_archive = (root / 'archive-sha256.txt').read_text(encoding='utf-8').split()[0]
    archive_path = root / 'candidate-evidence.zip'
    if hashlib.sha256(archive_path.read_bytes()).hexdigest() != expected_archive:
        raise ValueError('Evidence archive hash mismatch')
    manifest = json.loads((root / 'archive-manifest.json').read_text(encoding='utf-8'))
    summary = json.loads((root / 'summary.json').read_text(encoding='utf-8'))
    environment = os.environ.copy()
    with tempfile.TemporaryDirectory() as directory:
        extraction = Path(directory)
        environment['TMP'] = environment['TEMP'] = str(extraction)
        with zipfile.ZipFile(archive_path) as archive:
            for member in archive.infolist():
                target = (extraction / member.filename).resolve()
                if not target.is_relative_to(extraction.resolve()):
                    raise ValueError('Invalid evidence archive path')
                payload = archive.read(member)
                if member.filename in manifest and hashlib.sha256(payload).hexdigest() != manifest[member.filename]:
                    raise ValueError(f'Evidence file differs: {member.filename}')
            archive.extractall(extraction)
        checked = 0
        for run in summary['runs']:
            run_path = extraction / f"runs/case-{run['case']}-r{run['repeat']}/{run['condition']}"
            report = run_path / 'replay.json'
            execution = subprocess.run([sys.executable, '-X', 'utf8', str(root / 'evaluate.py'), '--case', str(run['case']), '--candidate', str(run_path / 'outputs'), '--output', str(report)], env=environment, capture_output=True, text=True, encoding='utf-8', timeout=120)
            if not report.exists():
                raise RuntimeError(execution.stdout + execution.stderr)
            observed = json.loads(report.read_text(encoding='utf-8'))
            if observed['complete_success'] != run['complete_success'] or observed['summary'] != run['groups']:
                raise AssertionError(f"Published result did not reproduce: {run_path.name}; {observed}")
            probe_report = run_path / 'replay-probes.json'
            probe_execution = subprocess.run([sys.executable, '-X', 'utf8', str(root / 'audit_probes.py'), '--case', str(run['case']), '--candidate', str(run_path / 'outputs'), '--output', str(probe_report)], env=environment, capture_output=True, text=True, encoding='utf-8', timeout=120)
            if not probe_report.exists():
                raise RuntimeError(probe_execution.stdout + probe_execution.stderr)
            expected_probe = json.loads((run_path / 'audit-probes.json').read_text(encoding='utf-8'))
            actual_probe = json.loads(probe_report.read_text(encoding='utf-8'))
            if actual_probe['all_passed'] != expected_probe['all_passed']:
                raise AssertionError(f'Post-hoc probe did not reproduce: {run_path.name}')
            checked += 1
        print(f'Reproduced {checked} published candidate check results. This is replay, not {checked} new agent executions.')


if __name__ == '__main__':
    main()
