---
name: sharp-frames-debt
description: >
  Identify and reconcile technical debt, deliberate shortcuts, and deferred work after a change or across a repository. Use for 기술 부채 정리, what debt did this change introduce, TODO/shortcut inventory, or debt ledger reconciliation. Reporting and ledger maintenance are distinct from implementing fixes; a marker scan alone is not a complete debt assessment.
---

# Account for debt without hiding defects

Relate concrete maintenance obligations to decisions, changes and evidence.
Default to a report. Respect an existing ledger/schema. Update a tracking file
when the user requests tracking/persistence or a repository workflow already
requires it; otherwise show the proposed entries without creating a file.

## Choose the requested lens

- **Change:** compare explicit base/head or the current change; distinguish
  introduced, increased, unchanged/preexisting, reduced/resolved and unknown-origin.
  If the baseline is absent, say the origin is unknown rather than calling every
  observed weakness new debt.
- **Scan:** inspect deferral markers, existing issue/decision records, constrained
  implementations and the code they describe. Read the actual behavior: a TODO
  or shortcut marker is a candidate, not automatically valid technical debt.
- **Reconcile:** compare prior ledger items with current code, callers and
  verification. A removed/moved comment does not prove resolution. Keep stable
  IDs, history and accepted/deferred decisions; avoid replacing the whole ledger.

For marker candidates you may run [scan_debt.py](scripts/scan_debt.py):
`python <skill-dir>/scripts/scan_debt.py --root <repo>`.
Use an existing Python 3 interpreter; the helper needs only the standard library.
For an unavailable `python` command, see [runtime guidance](references/python-runtime.md).
If the helper cannot run, inspect candidates directly and disclose that it was
not run; do not install a runtime merely to perform this optional scan.
It reads Git-listed tracked and untracked nonignored files and emits JSON only.
Python comments are tokenized; other languages use a documented comment-line
heuristic. Review every candidate and disclose skipped/unsupported files. A
nonzero error is not a clean scan. Custom markers use repeatable `--marker WORD`.

## Decide what belongs in the account

Distinguish a reachable correctness/security defect, intentional accepted tradeoff,
missing verification, and speculative preference. Preserve an active defect's
urgency; filing debt never counts as fixing it. Include unmarked but evidenced
debt when in scope. Do not add comments throughout source just to populate a ledger.

For each material item record ID if available, status/origin, location and symbol,
what is constrained, consequence/affected users, evidence, reason for deferral,
revisit trigger or ceiling, proposed correction and verification. Owner/date/effort
are unknown unless supported; do not invent them. Mark a missing trigger or reason
as missing. Merge duplicate entries for the same obligation without merging
independent business policies.

For reconciliation, resolution requires evidence of the implemented change and
its relevant verification; absence from search is only a clue. Mark partial fixes
and reopened items accurately. Report remaining/new tradeoffs of the correction.
Close only the scope actually verified, and retain unresolved history.

End with introduced/increased, existing/unknown, resolved/partial and remaining
counts for the inspected scope. Marker count is not a repository quality score.
Keep code changes for a separate implementation request.
