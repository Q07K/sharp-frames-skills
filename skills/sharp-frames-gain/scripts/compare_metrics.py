"""Compare declared observations; this does not authenticate their provenance."""
import argparse
import json
import math
from pathlib import Path
import sys

CONTEXT = ('scope', 'environment', 'scenario')


def validate(document):
    if not isinstance(document, dict) or any(not isinstance(document.get(k), str) or not document[k].strip() for k in (*CONTEXT, 'revision')):
        raise ValueError('Each observation needs nonempty scope, environment, scenario and revision strings')
    if not isinstance(document.get('metrics'), list) or not document['metrics']:
        raise ValueError('Each observation needs a nonempty metrics list')
    metrics = {}
    for item in document['metrics']:
        if not isinstance(item, dict) or any(not isinstance(item.get(k), str) or not item[k].strip() for k in ('name', 'unit', 'method', 'evidence', 'kind')):
            raise ValueError('Each metric needs name, unit, method, evidence and kind strings')
        value = item.get('value')
        if isinstance(value, bool) or not isinstance(value, (int, float)) or not math.isfinite(value):
            raise ValueError('Metric values must be finite numbers, not booleans')
        if item.get('direction') not in ('lower', 'higher', 'neutral'):
            raise ValueError('Metric direction must be lower, higher or neutral')
        if item['name'] in metrics:
            raise ValueError('Metric names must be unique in an observation')
        metrics[item['name']] = item
    return metrics


def compare(before, after):
    left, right = validate(before), validate(after)
    shared_reasons = [f'{key} differs' for key in CONTEXT if before[key] != after[key]]
    rows = []
    for name in sorted(left.keys() | right.keys()):
        a, b = left.get(name), right.get(name)
        reasons = shared_reasons.copy()
        if a is None or b is None:
            reasons.append('missing before observation' if a is None else 'missing after observation')
        else:
            reasons += [f'{key} differs' for key in ('unit', 'method', 'direction') if a[key] != b[key]]
            if a['kind'] != 'measured' or b['kind'] != 'measured':
                reasons.append('both observations must be declared measured')
        row = {'name': name, 'before': a['value'] if a else None, 'after': b['value'] if b else None, 'status': 'incomparable' if reasons else 'comparable', 'reasons': reasons, 'absolute_delta': None, 'percent_change': None, 'effect': 'unknown'}
        if not reasons:
            delta = b['value'] - a['value']
            if not math.isfinite(delta):
                row.update(status='incomparable', reasons=['numeric range exceeded'])
                rows.append(row)
                continue
            percent = delta / a['value'] * 100 if a['value'] else None
            if percent is not None and not math.isfinite(percent):
                percent = None
                row['percent_note'] = 'percentage exceeds numeric range'
            row.update(unit=a['unit'], absolute_delta=delta, percent_change=percent)
            if a['value'] == 0:
                row['percent_note'] = 'zero baseline: percentage undefined'
            direction = a['direction']
            row['effect'] = 'unchanged' if delta == 0 else 'unranked' if direction == 'neutral' else 'improved' if (delta < 0) == (direction == 'lower') else 'worse'
        rows.append(row)
    return {'schema_version': 1, 'before_revision': before['revision'], 'after_revision': after['revision'], 'declared_observations_only': True, 'metrics': rows, 'causal_skill_effect_established': False}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('before', type=Path)
    parser.add_argument('after', type=Path)
    args = parser.parse_args()
    try:
        result = compare(json.loads(args.before.read_text(encoding='utf-8-sig')), json.loads(args.after.read_text(encoding='utf-8-sig')))
    except (OSError, ValueError, TypeError, OverflowError) as error:
        print(json.dumps({'error': str(error)}), file=sys.stderr)
        return 2
    print(json.dumps(result, ensure_ascii=True, indent=2, allow_nan=False))
    return 0


if __name__ == '__main__':
    sys.exit(main())
