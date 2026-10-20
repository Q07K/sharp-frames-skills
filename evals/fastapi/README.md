# FastAPI comparison evidence

Three synthetic task types, three fresh executions per condition per task: 18
executions. Read [the results](../results/fastapi-2026-10-20.md) and
[execution notes](execution-notes.md) before interpreting the numbers.
The unchanged skill snapshot is included; no benchmark answers are injected into it.

## Reproduce checks

Use Python 3.12, install `requirements.txt` in an isolated environment, and extract
`candidate-evidence.zip` in this directory. Then run, for example:

```sh
python evaluate.py --case 2 --candidate runs/case-2-r1/with_skill/outputs --output recheck.json
```

The evaluator checks actual HTTP/SQLite behavior and an external copy of original
regression tests. Missing endpoints fail; those negative controls are in `controls`.
Independent grader audit found coverage gaps. `audit_probes.py` checks selected gaps
on every candidate after the original grades were frozen. Those post-hoc results
are separately recorded in `audit-probe-summary.json` and the evidence archive.
`python replay_evidence.py` verifies the archive hashes and rechecks all 18 saved
candidates. Replaying a saved candidate is not another independent model execution.
No network service, payment, real user data or production credentials are involved.
On Windows, if sandbox restrictions block SQLite/TestClient, use an authorized
local test environment and a writable TMP/TEMP directory.

`summary.json` records complete task success as the primary metric. Per-test-group
counts are diagnostic. Unknown duration/tokens are null, not zero. The three repeats
of one fixture task are correlated, not three independent problem types.

## Review evidence

`candidate-evidence.zip` includes every candidate's source, added tests, reports,
grading and process records. Runtime caches and temporary DBs are omitted. Local
command paths are replaced by placeholders; process records are worker self reports.
The archive manifest hashes the published text. `blind-label-mapping.json` maps
review pairs 1–9 to cases, repetitions and conditions. Reviewers did not receive it.
Model review with hidden labels is exploratory and does not measure human review time.
`evaluated-skill.zip` preserves the exact evaluated skill without adding a duplicate
discoverable SKILL.md under this repository's evaluation directory.

The local static review viewer presents all outputs and formal checks. Its HTML
is not needed to reproduce the API checks; source and JSON evidence are portable.
