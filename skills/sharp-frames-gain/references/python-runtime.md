# Running the comparison helper

`python` in the example means an available Python 3 interpreter. On Windows,
that command may resolve to a nonworking application execution alias. Reuse an
installed interpreter's full path, or `py -3` or `uv run python` if available:

```text
py -3 <skill-dir>/scripts/compare_metrics.py <before.json> <after.json>
uv run python <skill-dir>/scripts/compare_metrics.py <before.json> <after.json>
```

Replace placeholders with actual paths and quote paths containing spaces.
PyYAML is not a dependency of this helper. uv can provision missing runtimes;
prefer an existing interpreter and follow the environment's installation and
network permissions. If no runtime is usable, check supplied comparisons
manually and state the helper was not run. Comparability, provenance and missing
baseline rules still apply; do not report an unexecuted check as passed.
