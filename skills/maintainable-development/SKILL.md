---
name: maintainable-development
description: >
  Implement features, fix bugs, and refactor application code so requested
  behavior is complete, existing capabilities are reused, and humans can review
  and change the result safely. Use for repository implementation work, including
  APIs, backend services, frontend behavior, and shared modules, even when the
  user does not explicitly ask for clean code. For tiny edits apply only relevant
  checks. Do not turn conceptual explanations, naming discussions, code-reading-only
  requests, or documentation-only edits into implementation work.
---

# Build code people can trust and change

Deliver the requested behavior with clear design, useful reuse, and evidence.
Optimize correctness, review effort, future changes, and runtime behavior together.
A first draft that merely looks clean is not the target: inspect and verify the
work before handoff. This skill does not guarantee first-pass correctness.

## Scale the process to the task

Respect user scope, repository instructions, stack, conventions, and authorization.
Continue ordinary authorized implementation autonomously. Ask only when missing
information changes observable behavior or a consequential decision; do not add
a planning approval to routine work.

- **Small/local change:** inspect affected code and relevant tests, implement,
  and run checks that can expose its failure. A rename needs no architecture doc.
- **Feature/cross-module change:** identify behavior, reuse candidates, caller
  contracts, and verification before implementation. Keep reasoning concise and
  use existing planning conventions when helpful.
- **Sensitive boundary:** examine the actual risks when changing authorization,
  money, transactions, concurrent state, destructive operations, or compatibility.

Read only the references needed for the task:

- Design, reuse, boundaries, naming, types, comments, and state/failures:
  [design.md](references/design.md).
- Tests, regression coverage, review, and evidence:
  [verification.md](references/verification.md).
- Python/FastAPI implementation:
  [python-fastapi.md](references/python-fastapi.md).

## 1. Ground the change in behavior and existing code

Identify success conditions: inputs, outcomes, important failures, and behavior
to preserve. Resolve material ambiguity before encoding a guessed policy. State
reasonable low-impact assumptions and continue. Do not invent product features.

Search for a capability before creating it. Read relevant implementations,
callers, tests, configuration, and local instructions. Search by domain concept
as well as guessed symbol name: different names can hide the same policy.
Prefer targeted search and authoritative source over whole-repository summaries.

For meaningful reuse choices, determine:

1. What existing code, library, or platform capability already does this?
2. Does its actual behavior fit, including errors, units, side effects, and scope?
3. Should this change call it, extend it compatibly, or introduce a separate rule?

Use existing verified behavior when it fits. Otherwise explain the substantive
difference instead of copying it under another name or forcing unrelated business
rules into one abstraction. A search cannot prove the absence of every semantic
duplicate.

## 2. Choose a coherent design before spreading implementation

Put code where maintainers expect the behavior. Group things that change together
and give independently changing policies a clear boundary. Preserve the working
architecture unless the task needs to change it. Folders alone enforce no boundary.

Distinguish business decisions from transport, persistence, and external effects
when this improves understanding or tests. Use plain functions where sufficient.
Introduce a class, layer, protocol, framework, or dependency only for a concrete
problem in this change.

Define useful contracts: inputs, results, error meaning, state changes, and
compatibility. Check callers before changing a shared contract. Centralize a
genuinely shared policy, not merely similar text. Shared code increases the impact
of future changes.

## 3. Implement complete behavior with readable code

- Name values by domain meaning, units, and state. Avoid repeatedly changing one
  variable's meaning through a workflow.
- Keep the main path readable. Split functions when it reduces reasoning, not to
  hit a line count. Avoid both tangled logic and pass-through indirection.
- Make dependencies and side effects visible. Prefer meaningful contracts to
  hidden globals, surprising mutation, and loosely shaped data bags.
- Use useful types at boundaries and shared contracts. Distinguish static hints
  from runtime validation. Do not evade checks with blanket `Any`, casts, ignores,
  or equivalent suppressions.
- Validate untrusted input at the right boundary; enforce domain invariants and
  authorization at the authoritative layer. Client claims are not authority for
  identity, ownership, price, permissions, or account state.
- Handle failures by meaning. Retain operator diagnostics and return appropriate
  public errors. Do not swallow programming errors, expose secrets, or report a
  failed operation as successful.
- Use appropriate resource lifetimes, transaction boundaries, concurrency handling,
  and data representations for the real operation. Consult relevant guidance
  when crossing those boundaries.
- Consider realistic performance/resource use, including repeated queries,
  unbounded input, and blocking calls. Avoid speculative optimization.
- Complete the requested user path. A mock, TODO, empty handler, disconnected
  module, or unrequested redesign is not a substitute for working behavior.

Comments add information: rationale, non-obvious policy, external constraints,
tricky algorithms, or usage hazards. Prefer clear code to line-by-line narration.
Public contracts may need docstrings for inputs, outcomes, exceptions, or side
effects. Keep documentation true; omit boilerplate that only repeats names/types.

## 4. Verify against requirements, not just implementation

Use actual repository commands and tools. Select checks capable of exposing the
changed behavior's failure, then execute before handoff. Small reversible changes
do not automatically justify new tests or a full suite.

For behavior changes, derive expectations from requirements and domain policy.
Check important boundaries and failures, not only normal success. Exercise affected
callers of shared modules. For API/persistence changes, verify the relevant
integration instead of relying only on mocked logic.

Do not weaken expectations, remove safeguards, disable checks, or mock away the
behavior under test to get green results. Change expectations only when requested
behavior warrants it, and make the reason visible.

Distinguish behavior-preserving refactoring from observable behavior changes in
the diff or explanation. Follow local lint, format, type, architecture, build,
and test rules. Do not add quality tooling as an automatic side effect of this skill.

## 5. Review the actual diff and hand off evidence

Inspect final code, not just the plan: missing requirements, duplicate policies,
broken callers, unintended contract changes, excess abstraction/comments, unrelated
edits, and tests that could pass despite the central requirement being wrong.
Fix material issues before completion.

Keep handoff proportionate: behavior and why; important reuse/design decisions;
checks actually run and their results; material unverified behavior. Point to real
files/symbols where useful. Distinguish passed, failed, skipped, and not-run checks.
A command in a plan is not execution evidence.

Do not create a stack of reports by default. Update affected contracts and keep
consequential rationale in the repository's established place. Preserve unrelated
work. This skill grants no additional permission to publish, deploy, or alter
unrelated configuration.
