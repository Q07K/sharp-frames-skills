---
name: sharp-frames-versions
description: >
  Research dependency versions using current official sources and firsthand developer discussions, then assess keeping or upgrading against actual project usage, compatibility, service benefit, and migration scope. Use for 라이브러리 버전 검토, 업데이트 영향, 유지 vs 업그레이드, or dependency upgrade advice. Advisory by default; a version assessment alone does not authorize changing dependencies.
---

# Decide whether a version change helps this service

Evaluate the current state and realistic upgrade paths. The newest release is
a candidate, not the objective. Read [evidence and impact guidance](references/assessment.md)
when researching a dependency; it defines how to connect external changes to the
local code and how to weigh community reports.

## Establish what is actually in use

Inspect manifests, lockfiles, runtime/toolchain requirements, deployment and CI
configuration, and relevant imports/configuration/callers. Distinguish declared
ranges, resolved versions, observed installed versions and deployed versions.
A manifest alone cannot prove the deployed version. Identify direct/transitive
dependencies and coupled plugins or peer requirements relevant to the decision.
Bound broad requests by service risk and important dependency groups, and report
what remains unchecked rather than silently claiming an exhaustive review.

## Research current candidates

Browse official releases, package metadata, migration guides, support/security
policies and advisories. Check the applicable stable or supported release line,
not only a registry's default tag. Establish exact source and candidate versions,
release dates and runtime/peer/transitive constraints. Check withdrawn releases,
known regressions and fixes when relevant. Version numbering alone does not
establish compatibility or security.

Also seek firsthand developer experience in official issues/discussions and
relevant communities. Prefer reproducible reports and maintainer responses.
Record reported version, environment, date and resolution; distinguish a single
report from a general problem and opinion from verified behavior. Search in the
languages relevant to the request, including Korean when it adds applicable
experience. Say when no pertinent community evidence was found; do not invent
consensus or post messages to solicit opinions.

## Connect the evidence to this project

Compare keeping the present line, a supported patch/minor path, and a larger or
staged migration where viable. Explain which changes affect actual used APIs,
validation/serialization, configuration, data, integrations, tests and deployment.
Separate necessary compatibility edits from optional adoption of new capabilities.
Give concrete locations and flow-level effects, scope uncertainty and checks
needed to validate the estimate. Do not invent an exact effort, performance gain
or number of files to edit from a changelog or import count.

Weigh security/support exposure, needed capabilities, observed regressions,
maintenance cost and migration/operational risk. Apply security advisory ranges
to the actual version and assess reachability separately; absent findings are
not proof of safety. Release age is one signal, not a reason to postpone an
applicable urgent fix. Explain why a coupled update is needed rather than
recommending a wholesale latest-version upgrade.

## Report a decision and its limits

Lead with a dated recommendation: keep, update within the line, migrate in stages,
or defer the decision pending specific evidence. Give a compact comparison of
the viable paths, service benefit, required code changes, migration cost/risk and
confidence. Link the supporting primary and community sources next to claims;
include unresolved compatibility facts, meaningful verification and rollout or
rollback constraints. Label measured facts, published claims and expected benefits.
If fresh browsing is unavailable, report local findings and an evidence-gathering
plan, withholding unsupported claims about current releases/support/security.

Assessment does not install packages, rewrite manifests/locks, run migrations or
change the service. Use read-only inventory first; treat package manager commands
that resolve, download or execute code according to their actual side effects.
An explicit upgrade request authorizes implementation in that scope, with the
project's normal verification and migration safeguards. Do not require this
skill or another one to be installed before a developer can use the report.
