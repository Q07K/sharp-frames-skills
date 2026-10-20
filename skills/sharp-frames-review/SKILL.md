---
name: sharp-frames-review
description: >
  Review a diff, commit, branch, pull request, or named code for defects, regressions, unsafe boundaries, and maintenance costs. Use for code review, PR review, 변경 리뷰, or reviewing the last commit. Report findings without editing implementation; whole-project assessment belongs to audit and applying fixes requires an implementation request.
---

# Review a concrete change

Return actionable findings grounded in the requested change and its connected code.
Source, index, branch and history stay unchanged. A request to review is not a
request to repair, create issues, publish comments, or run a project-wide audit.
Write a report file only when requested or when an established review workflow requires it.

## Establish what is being reviewed

- Inspect repository instructions, branch, HEAD and dirty/untracked state.
- Honor an explicit target: staged, uncommitted, commit/range, files, or PR.
  Without a target, review uncommitted changes (including relevant untracked code);
  if clean, state that you are reviewing the last commit. For a root commit, use
  its empty-tree comparison. Never guess the branch base from HEAD~1.
- For a branch, resolve the intended comparison ref and merge base. PR metadata
  is authoritative for its base/head. If inaccessible, report the missing scope
  rather than substituting some local diff as the PR.
- Read requirements, the actual diff, affected implementations, callers, tests,
  and relevant contracts/configuration. Changed lines alone are insufficient.

## Check the behavior and cost of change

Trace inputs through decisions, storage and outputs. Check changed contracts,
authorization, validation, state/failure ordering, transactions, concurrency and
realistic resource use where relevant. Verify preservation of existing behavior.
For reuse, name a real compatible existing implementation; textual similarity
alone does not justify merging independent policies. Identify tests that could
pass while the changed requirement is wrong. Follow project lint/type rules;
do not turn personal formatting preferences into defects.

Inspect test changes for removed assertions/cases, wider tolerances, skipped or
uncollected checks, regenerated snapshots and mocks that bypass the behavior.
Compare changed expectations to the requested contract rather than treating a
green suite or a higher case count as proof. Look for meaningful role/ownership,
state and persona workflow gaps; missing coverage alone is not a proven bug.
Distinguish observed TDD execution evidence from a claimed chronology.

Before reporting a finding, verify its reachable trigger and the observed or
reasoned consequence. Check the callee and safeguards before alleging a missing
check. Read history when needed to distinguish introduced regressions from older
conditions. Known debt is context, not permission to ignore an active contract
violation. Put plausible but unconfirmed concerns in a separate questions section.

Run relevant local checks when useful and authorized. Distinguish executed checks
from static reasoning; use isolated output/cache locations when necessary. Do not
run migrations, production calls or destructive tests as a side effect of review.

## Deliver findings the author can act on

Lead with scope and overall conclusion. For each confirmed finding provide:

- A stable local ID, severity by actual impact, and a tight file/line reference.
- The trigger, current behavior, consequence and evidence kind.
- The smallest sound correction and the regression check it needs.

Separate blocking defects, meaningful maintainability/test gaps and optional
suggestions. Do not inflate severity because a test is missing. Note material
preexisting issues separately from findings caused by this change. No findings
is valid: say no confirmed issues were found in the reviewed scope, then state
checks and limits. Do not certify the entire project or deployment from a diff.
