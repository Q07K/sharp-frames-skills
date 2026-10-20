---
name: sharp-frames-plan
description: >
  Create a repository-grounded implementation or migration plan with reusable components, ordered changes, verification, and material rollout concerns. Use for 구현 계획, 작업 분해, 단계적 마이그레이션, or planning a multi-module feature. Clarifying what to build belongs to brainstorming; a plan-only request does not authorize implementation.
---

# Make the intended change executable

Create a plan that another developer can follow and verify without rediscovering
its critical assumptions. Size the plan to the change; a small local edit needs
only a short approach, not a new document or full delivery process.

## Establish the starting point

Read the relevant repository instructions, current source and tests. Distinguish
the checked-out revision, uncommitted work, and any other ref being planned against.
Trace entry points, policy owners, callers and side effects before naming files
to change. Cite existing modules worth reusing and explain their fit or limitation;
do not assume a function is reusable from its name alone.

Carry forward the requested behavior, non-goals, constraints and decisions already
made. Identify material unresolved policy questions. Ask when they block a correct
plan; otherwise label assumptions and the step that will validate them. For a
new project, use the chosen stack and standard capabilities rather than inventing
an existing architecture. If source is unavailable, label proposed paths and do
not describe them as inspected facts.

## Build reviewable increments

For each meaningful increment, specify:

- The behavior or contract it delivers and what must remain compatible.
- Existing code to reuse or extend, proposed changes, affected callers and data.
- Dependencies on other increments and the reason for the ordering.
- Requirement-derived cases before implementation: relevant boundaries, actual
  roles/ownership and state transitions, with the actual project commands.
- A test-first red/green/refactor sequence for changed behavior and a small set
  of connected persona workflows checking responses and final state. Keep a
  behavior-preserving refactor green rather than inventing a red stage.
- Case inventory/test locations and material existing test expectation, fixture,
  skip or collection changes, with a contract-based justification and coverage
  retained. Distinguish cases to write from checks actually executed.

Prefer increments that can be verified together over an arbitrary layer-by-layer
list. Describe risky algorithm or schema choices where they affect correctness;
do not write a speculative full implementation into the plan. Avoid invented
line counts, exact completion times, test outcomes or test commands not found in
the project. Mark new commands as proposed when necessary.

For changes involving persisted data, external contracts, background work or
deployment coupling, include compatibility during transition, backfill/idempotency,
failure recovery and rollout checks as relevant. Explain rollback limits when old
code cannot read new data; a Git revert alone may not restore service state.
For dependency migrations, establish the target and compatibility evidence first.

## Present the handoff

Lead with the approach and affected scope, then give the ordered increments,
acceptance checks, material risks and remaining decisions. Separate inspections
already performed from planned verification. Record deliberate deferrals with
their reason and revisit condition. Save a plan only when requested or established
project conventions call for it; do not automatically commit it.

Planning alone keeps implementation unchanged. A request to plan and implement
already authorizes ordinary work in that scope: proceed after resolving required
questions without adding a blanket plan-approval gate. Available implementation
skills may help, but this plan must remain usable without another installed skill.
