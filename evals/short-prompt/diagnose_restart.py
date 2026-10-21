"""Exploratory repeated check of a restart race observed during first replay."""

from pathlib import Path
import argparse
import io
import json
import sys
import unittest

from evaluate import Flows


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--python', default=sys.executable)
    parser.add_argument('--output', type=Path, required=True)
    parser.add_argument('--runs', type=int, default=10)
    args = parser.parse_args()
    root = Path(__file__).resolve().parent
    repo = root.parents[1]
    adapters = json.loads((root / 'adapters.json').read_text())
    observations = {}
    for condition in ('without-skill', 'with-skill', 'refactored'):
        Flows.candidate = repo / 'examples/fastapi-short-prompt' / condition
        Flows.interpreter, Flows.adapter = args.python, adapters[condition]
        outcomes = []
        for index in range(args.runs):
            stream = io.StringIO()
            result = unittest.TextTestRunner(stream=stream).run(unittest.TestSuite([Flows('test_post_survives_restart')]))
            output = stream.getvalue().replace(str(repo), '<REPO>').replace(str(repo).replace('\\', '/'), '<REPO>')
            outcomes.append({'run': index + 1, 'passed': result.wasSuccessful(), 'output': output})
        observations[condition] = outcomes
        print(condition + ': ' + str(sum(item['passed'] for item in outcomes)) + '/' + str(args.runs) + ' restart checks passed', flush=True)
    args.output.write_text(json.dumps(observations, ensure_ascii=False, indent=2), encoding='utf-8')


if __name__ == '__main__':
    main()
