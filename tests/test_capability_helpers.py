import copy
import importlib.util
import json
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest

ROOT = Path(__file__).resolve().parents[1]


def module_at(name, relative):
    spec = importlib.util.spec_from_file_location(name, ROOT / relative)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


debt = module_at('debt_scanner', 'skills/sharp-frames-debt/scripts/scan_debt.py')
gain = module_at('gain_compare', 'skills/sharp-frames-gain/scripts/compare_metrics.py')


class DebtInventory(unittest.TestCase):
    def test_comments_ignored_files_unicode_untracked_and_read_only(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            subprocess.run(['git', 'init', '-q', str(root)], check=True)
            (root / '.gitignore').write_text('ignored.py\n', encoding='utf-8')
            (root / '주문.py').write_text('message = "TODO: not a comment"\n# TODO: revisit when volume grows\nvalue = 1  # shortcut: single process; revisit with workers\n', encoding='utf-8')
            (root / 'ignored.py').write_text('# FIXME: ignored\n', encoding='utf-8')
            (root / 'notes.md').write_text('TODO: prose is not a source comment\n', encoding='utf-8')
            (root / 'web.ts').write_text('// FIXME: handle canceled request\n', encoding='utf-8')
            (root / 'binary.py').write_bytes(b'\xff\xfe')
            before = {p.name: p.read_bytes() for p in root.iterdir() if p.is_file()}
            status = subprocess.check_output(['git', '-C', str(root), 'status', '--porcelain', '-z'])
            result = debt.inventory(root)
            self.assertEqual([(h['path'], h['line']) for h in result['candidates']], [('web.ts', 1), ('주문.py', 2), ('주문.py', 3)])
            self.assertTrue(all(h['needs_context_review'] for h in result['candidates']))
            self.assertIn({'path': 'binary.py', 'reason': 'UnicodeDecodeError'}, result['skipped'])
            self.assertFalse(result['semantic_debt_assessment'])
            self.assertNotIn('ignored.py', [h['path'] for h in result['candidates']])
            self.assertEqual(before, {p.name: p.read_bytes() for p in root.iterdir() if p.is_file()})
            self.assertEqual(status, subprocess.check_output(['git', '-C', str(root), 'status', '--porcelain', '-z']))

    def test_tracked_files_size_limit_and_literal_custom_marker(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            subprocess.run(['git', 'init', '-q', str(root)], check=True)
            (root / 'tracked.py').write_text('# debt+: old adapter\n# debtX: not this marker\n', encoding='utf-8')
            subprocess.run(['git', '-C', str(root), 'add', '.'], check=True)
            (root / 'large.py').write_text('# debt+: ' + 'x' * 100, encoding='utf-8')
            result = debt.inventory(root, ['debt+'], max_bytes=80)
            self.assertEqual(len(result['candidates']), 1)
            self.assertEqual(result['candidates'][0]['text'], 'old adapter')
            self.assertIn({'path': 'large.py', 'reason': 'size limit'}, result['skipped'])

    def test_non_repository_is_an_error_not_clean(self):
        with tempfile.TemporaryDirectory() as directory:
            with self.assertRaises(ValueError):
                debt.inventory(Path(directory))


class GainComparison(unittest.TestCase):
    def observation(self, value=10):
        return {'scope': 'order API', 'environment': 'same fixture runtime', 'scenario': 'one ten-line order', 'revision': 'before', 'metrics': [{'name': 'queries', 'unit': 'queries/request', 'method': 'sqlite trace', 'value': value, 'direction': 'lower', 'kind': 'measured', 'evidence': 'trace.log'}]}

    def test_delta_direction_zero_and_no_causal_claim(self):
        before, after = self.observation(10), self.observation(6)
        after['revision'] = 'after'
        result = gain.compare(before, after)
        row = result['metrics'][0]
        self.assertEqual((row['absolute_delta'], row['percent_change'], row['effect']), (-4, -40, 'improved'))
        self.assertFalse(result['causal_skill_effect_established'])
        row = gain.compare(self.observation(0), self.observation(1))['metrics'][0]
        self.assertIsNone(row['percent_change'])
        self.assertEqual(row['effect'], 'worse')
        self.assertEqual(gain.compare(before, before)['metrics'][0]['effect'], 'unchanged')

    def test_mismatched_or_unmeasured_comparisons_are_blocked(self):
        before = self.observation()
        for field, value, location in [('environment', 'new hardware', 'context'), ('scenario', 'different workload', 'context'), ('unit', 'seconds', 'metric'), ('method', 'different collection', 'metric'), ('kind', 'expected', 'metric')]:
            after = copy.deepcopy(before)
            (after if location == 'context' else after['metrics'][0])[field] = value
            row = gain.compare(before, after)['metrics'][0]
            self.assertEqual(row['status'], 'incomparable')
            self.assertIsNone(row['absolute_delta'])
            self.assertIsNone(row['percent_change'])

    def test_missing_metric_has_no_fabricated_zero(self):
        before, after = self.observation(), self.observation()
        after['metrics'][0]['name'] = 'latency'
        result = gain.compare(before, after)
        self.assertEqual(len(result['metrics']), 2)
        self.assertTrue(all(row['status'] == 'incomparable' for row in result['metrics']))
        self.assertIsNone(result['metrics'][1]['after'])

    def test_invalid_values_duplicates_and_cli_error(self):
        for value in (True, float('nan'), float('inf'), '10'):
            with self.assertRaises(ValueError):
                gain.compare(self.observation(value), self.observation())
        before = self.observation()
        before['metrics'].append(copy.deepcopy(before['metrics'][0]))
        with self.assertRaises(ValueError):
            gain.compare(before, self.observation())
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / 'bad.json'
            path.write_text('{}', encoding='utf-8')
            result = subprocess.run([sys.executable, str(ROOT / 'skills/sharp-frames-gain/scripts/compare_metrics.py'), str(path), str(path)], capture_output=True, text=True)
            self.assertEqual(result.returncode, 2)
            self.assertIn('error', json.loads(result.stderr))
            self.assertEqual(result.stdout, '')

    def test_extreme_finite_inputs_do_not_emit_infinite_json_values(self):
        result = gain.compare(self.observation(-1e308), self.observation(1e308))
        self.assertEqual(result['metrics'][0]['status'], 'incomparable')
        json.dumps(result, allow_nan=False)
        result = gain.compare(self.observation(1e-308), self.observation(1e308))
        self.assertIsNone(result['metrics'][0]['percent_change'])
        self.assertEqual(result['metrics'][0]['effect'], 'worse')
        json.dumps(result, allow_nan=False)


if __name__ == '__main__':
    unittest.main()
