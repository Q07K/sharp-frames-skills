---
name: sharp-frames-gain
description: >
  Explain or compare the effects of an improvement using before/after evidence: behavior, maintenance burden, verification, performance, cost, and tradeoffs. Use for 개선 효과, 전후 비교, improvement impact, or what did refactoring gain. Distinguish measured observations from expected benefits; do not modify code or invent savings when a baseline is missing.
---

# Show effects with their evidence

Identify the exact change, scope and baseline. Read the before/after code,
requirements, checks, supplied measurements and relevant debt records. This is
a report, not a request to modify code, invent a previous implementation, install
benchmark tooling, or run expensive/production workloads.

## Separate four kinds of statement

1. **Behavior observed:** changed outcomes with a concrete check and revision.
2. **Static change observed:** a removed duplicate policy, changed call path or
   dependency count, with comparable source boundaries and actual references.
3. **Runtime/cost measured:** a named metric and unit, before/after values,
   workload, environment, measurement method, samples and source of evidence.
4. **Expected benefit:** a plausible reason future understanding or changes may
   be easier, with a proposed way to validate it. This is not measured review time.

Include regressions, unchanged results, added dependencies, migration effort and
new debt alongside wins. Fewer lines/files/comments/tests are not quality proof.
A passed test supports its assertions, not all correctness or all possible races.
Published external benchmark savings are not this project's savings or this skill's
effect. A before/after project change alone cannot isolate the causal effect of
using a skill; that needs a controlled comparison.

## Compare like with like

Do not subtract results with different workloads, units, environments, scope or
collection method. If comparable, show raw before/after values and absolute
delta; percentages need a nonzero baseline. Keep unknowns as unknown rather than
zero, and never combine unrelated metrics into an unsupported quality score.
Different or missing baselines should block the affected comparison, not all
useful qualitative explanation. Reuse valid recorded evidence for unchanged
inputs and identify its provenance; do not claim it was independently rerun.

For supplied numeric observations, use [compare_metrics.py](scripts/compare_metrics.py)
with two JSON paths. Read [measurement format](references/measurements.md) when
preparing inputs. The helper checks declared comparability and arithmetic; it
does not verify that a reported measurement actually happened.

## Deliver a compact impact table

Use aspect, before, after, evidence/verification, confidence/limitations and
tradeoff where useful. State whether the result is improved, worse, unchanged,
incomparable or unmeasured on each axis. Without a baseline, say what is observed
now and what benefit is expected; do not make up a percentage to satisfy a chart.
Match the user's language and depth. Persist a report only when requested.
