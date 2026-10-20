# Declared observation format

The helper compares supplied values; it does not run or authenticate benchmarks.
Keep logs/commands and their input identity available for a reviewer. Use the same
scope, environment and scenario labels only when they actually describe equivalent
conditions. Revision differs; environment/workload/measurement method must match.

Example input (illustrative numbers, not results for this package):

```json
{
  "scope": "order detail request",
  "environment": "Python 3.12, SQLite fixture, same machine",
  "scenario": "one order with ten lines, same seed data",
  "revision": "before-commit",
  "metrics": [
    {
      "name": "database_queries",
      "unit": "queries/request",
      "value": 12,
      "direction": "lower",
      "method": "SQLite statement trace, one request",
      "kind": "measured",
      "evidence": "actual trace log and command location"
    }
  ]
}
```

Prepare a second observation for the after revision. `direction` is `lower`,
`higher`, or `neutral`; a declared kind other than `measured` blocks arithmetic.
Omitted metrics, changed units/methods/directions or incompatible context produce
an incomparable row, never fabricated zeros. For a zero baseline, percentage is
undefined; an absolute change can still be shown. A negative baseline can produce
unhelpful percentages: prefer raw/absolute values for such metrics.

For timing distributions, record sample count, warmup, relevant percentiles and
variance in the supporting evidence. A single scalar with matching labels does
not establish statistical significance or reviewer productivity. Never relabel
different sample definitions merely to make the helper accept a comparison.
