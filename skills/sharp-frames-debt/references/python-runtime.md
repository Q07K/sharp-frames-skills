# Running the optional helper

`python` in the example means an available Python 3 interpreter. On Windows,
that command may resolve to a nonworking application execution alias. Reuse an
installed interpreter's full path, or `py -3` or `uv run python` if available:

```text
py -3 <skill-dir>/scripts/scan_debt.py --root <repo>
uv run python <skill-dir>/scripts/scan_debt.py --root <repo>
```

Replace placeholders with actual paths and quote paths containing spaces.
PyYAML is not a dependency of this helper. uv can provision missing runtimes;
prefer an existing interpreter and follow the environment's installation and
network permissions. If no runtime is usable, inspect candidates directly and
report the helper as not run, not as a successful scan with no candidates.
