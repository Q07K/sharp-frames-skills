---
name: sharp-frames-audit
description: >
  Assess a whole repository or substantial subsystem for correctness, architecture, reuse, security boundaries, verification gaps, and maintainability risks. Use for 전체 프로젝트 검토, repository audit, codebase health, or prioritized technical assessment. Read and report; a narrow diff review or requested implementation is a different task.
---

# Assess a codebase with visible coverage

Produce an evidence-based assessment and a prioritized next-change backlog.
Keep source, index and branch state unchanged. Do not rewrite code or create
tracking files/issues merely because you found problems. A requested report path
is permission to write that report, not to repair the project.

## Map before judging

Record scope, revision and dirty state. Read local instructions, product purpose,
workspace/package boundaries, manifests, runtime/build/deploy configuration,
entry points, existing checks and relevant operational assumptions. Exclude
generated/vendor/cache trees from ordinary source analysis and disclose exclusions.
Do not inspect credentials or production data to manufacture additional coverage.

Follow representative flows end to end, prioritizing authority, money, writes,
external effects, shared state and complicated change boundaries. Trace callers
and the actual policy-owning implementation; a folder diagram is not proof of
how dependencies behave. Record what establishes each important invariant and
what remains an open question. Distinguish observed load from assumed load.

For large repositories, cover the inventory broadly and deepen selected flows.
Use a coverage table: subsystem/flow, evidence locations, depth (flow-traced,
file-read, inventory-only, not inspected), checks executed and remaining questions.
Never describe a sampled audit as reading every file. Ask for a scope decision
only when the ambiguity would materially change the assessment; keep progressing
on known scope rather than blocking ordinary inspection.

## Investigate concrete risks

Check contracts and failure paths, trust/tenant boundaries, transaction and
resource lifetime, concurrency, query growth, tests and release assumptions.
For maintainability, look for conflicting duplicate policies, misleading names or
types, stale comments, hidden effects, inappropriate dependencies and boundaries
that force unrelated changes. Check usages, exports, configuration and dynamic
entry points before calling something dead. Similar code can embody different rules.

Rank findings by reachable impact and evidence, not by a generic quality score.
Separate demonstrated defects, evidenced maintenance debt, and hypotheses needing
validation. A missing test is a verification gap; it is not automatically a bug.
Run appropriate local checks and state failures/unavailable checks honestly.
Installed-version facts and tool advisories require actual inspection or current
authoritative documentation, not recalled version tables.

## Report a useful next step

Include a short system map, findings with path/line/trigger/consequence, and the
coverage table. For prioritized work give rationale, blast radius/dependencies,
smallest viable change, verification and a qualitative effort range with assumptions.
Offer a bounded first batch that can be reviewed independently; do not apply it
until implementation is requested. No evidence of a problem in sampled code does
not establish whole-repository health. Do not manufacture findings to fill a quota.
