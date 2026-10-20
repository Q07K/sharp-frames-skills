# Dependency evidence and local impact

## Inventory without changing the environment

Use the repository's package manager and workspace structure. A requirement range,
lock resolution and running process can disagree. Report their provenance rather
than collapsing them to one version. A test or archived fixture's dependency is
not automatically a production dependency. Identify runtime vs development/build
usage and shared constraints before prioritizing a large repository.

Inspect lockfiles as data. Read-only package inventory may help if the environment
is known; do not assume a shell's global interpreter belongs to the service. Avoid
unrequested install, lock regeneration, code generation or commands that execute
dependency lifecycle scripts. Do not transmit private source or credentials to a
public search service. Search package names and public API/error names instead.

Useful coupling evidence depends on the stack: Python runtime and framework/model
library constraints; Node engines, peer dependencies and build plugins; JVM/.NET
runtime/BOM/platform requirements; native ABI, OS/architecture and container base
images. Inspect what this project uses rather than applying every stack checklist.

## Build a small evidence set

For each consequential claim record the URL, checked date, applicable release
or range, and why it affects this service. Use the upstream release/migration
document for intended changes, registry metadata for release identity and constraints,
official support policy for support status, and advisories for affected/fixed ranges.
Verify package identity; similarly named packages or distribution versions can differ.

Search version-specific issues/discussions as well as successful migrations.
Assess whether a report's runtime, plugin, workload and deployment match ours.
Check follow-up fixes, workarounds, duplicates and maintainer confirmation. An
old open issue may apply only to a superseded release; a closed issue may still
affect a candidate older than its fix. A popular post is not a failure rate.
Firsthand Korean and international posts can reveal operating costs absent from
a release note, but preserve their anecdotal status and applicability limits.

When sources disagree, show the disagreement and the experiment or authoritative
metadata needed to resolve it. Lack of a reported regression is not evidence that
all integrations work. Keep prerelease adoption distinct from the supported path.

## Trace impact, not just imports

Map each applicable change to its policy owner and callers, including indirect
behavior: coercion/defaults, error payloads, ordering, serialization/schema output,
authentication/session handling, async resource lifetime and external side effects.
Use only the dimensions implicated by the change. Cite inspected paths and distinguish
confirmed edits, likely impact requiring a spike, and uninspected areas.

Group work into compatibility edits, optional feature adoption, verification, and
deployment/data migration. A compatibility bridge may reduce immediate edits but
retain a future obligation; record its support limits and removal condition.
Do not call an upgrade beneficial merely because it removes deprecation messages.

Use reproducible same-workload benchmarks for local speed/cost claims. Upstream
benchmarks describe upstream conditions; they are candidates for validation here.
If estimating effort, use a justified range and assumptions or qualitative scope;
do not express fabricated precision as an engineering estimate.

## Suggested decision record

Adapt the report to the number of dependencies and decision importance:

| Choice and exact target | Relevant changes and service benefit | Required edits / optional adoption | Compatibility and operating risk | Evidence / confidence |
| --- | --- | --- | --- | --- |
| Keep current supported line | Why sufficient; exposure and cost of waiting | Any necessary mitigations | Support/advisory status checked as of date | Known facts and gaps |
| Within-line update | Applicable fixes or useful changes | Located compatibility changes and checks | Coupled requirements and regressions | Primary + relevant firsthand reports |
| Larger or staged migration | Required capability or support path | Migration batches, bridge removal, optional scope | Contract/data/rollout constraints | What is verified vs needs a spike |

Only include viable options; explain if keeping a version is unacceptable. State
the recommended next action, verification needed before adoption, and a revisit
condition for deferral. Rollback may require old artifacts, reversible data changes,
or mixed-version compatibility; changing a version pin alone may be insufficient.
