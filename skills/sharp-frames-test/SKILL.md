---
name: sharp-frames-test
description: >
  Design and maintain requirement-based test cases, add requested regression tests, and verify role/state boundaries and connected persona workflows. Use for 테스트 케이스 설계·관리, 예외 케이스 분석, 페르소나 워크플로 테스트, or regression coverage work. Design/review-only requests stay read-only; writing tests does not authorize changing product behavior to make them pass. Normal feature implementation already includes TDD.
---

# Keep the test oracle useful and visible

Connect requested behavior to cases that can expose a real failure. Read
[case design and records](references/cases.md) for the matrix, workflow and change
record format. Use the project's tools and scale detail to risk; do not add a new
test framework, mandatory report stack or fixed unit/E2E ratio by default.

## Establish scope and the oracle

Identify whether the request is case design, coverage review, test implementation,
or execution. A design/review request leaves files unchanged. Writing requested
tests may change tests, fixtures and case records within scope; it does not itself
authorize product fixes. If implementation is also requested, continue that work
without an extra ritual approval step.

Inspect requirements, actual flows, policy owners/callers, existing tests, runner
configuration and baseline state. Record baseline failures and relevant collected
case identities/skips before changes. Determine expected behavior from contracts,
requirements or independent domain facts, not the result returned by current code.
Mark material unknown policy and resolve it before turning it into a test oracle.

## Analyze risks and personas before writing cases

Map affected requirements, nearby preserved behavior, real roles/ownership,
prerequisites, state transitions and harmful side effects. Choose relevant boundary
and exception classes rather than mirroring the new functions. Include retry,
partial failure, stale state or concurrent actions when the flow makes them material.
Do not invent unsupported rules or enumerate an unhelpful full cross product.

For each relevant persona, express a goal as connected actions through the real
application boundary with follow-up reads and final state assertions. Include
important denied and recovery paths, not only successful unit calls. Use focused
unit tests for local rules, integration/contract checks for connections and a small
set of critical workflows. API workflows with an isolated DB suit backend services;
use real browser interaction for affected UI behavior. Label simulated boundaries.

## Implement and execute honest checks

When implementation is authorized, use red/green/refactor for new or corrected
behavior: observe a relevant failing case before the product change and run that
same case afterwards. A pure refactor normally stays green. If only tests are
requested, a genuine product failure remains reported rather than being fixed
silently. Setup/import failures unrelated to the target are blocked execution.
Never claim a test-first chronology that did not occur.

Keep existing regression obligations. A material change to an expectation, fixture,
snapshot, mock, tolerance, skip or collection configuration needs a demonstrated
test defect, an authorized contract change or a behavior-preserving refactor reason.
Show what was checked before/after and how coverage is retained. Do not remove a
failure because it is inconvenient, accept the implementation as its own oracle,
or hide a real path behind mocked success. Justified test fixes are allowed without
blanket approval; consequential policy ambiguity still needs an answer.

Use deterministic setup, isolated data and bounded external stubs where needed.
Keep internal policy and relevant persistence real. Review collected/skipped cases
and test configuration as well as assertions. Do not erase a flaky first failure
with a later retry; record limitations and any justified quarantine. A writable
manifest or another AI's agreement does not make acceptance checks independent.

## Maintain and hand off the cases

Update the existing case inventory; for a nontrivial feature without one, use
tests/CASE_MATRIX.md. Stable test names can serve as IDs. Link requirement and
persona/scenario to expected response/state, test location, risk and gaps. Preserve
superseded cases' replacement/reason instead of losing history. Keep definitions
separate from dated run evidence so a previous pass cannot masquerade as current.

Report what was added/changed and why; actual commands/environment and results;
red/green evidence where executed; unit/integration/workflow boundaries; material
test changes and retained coverage; failures, skips, blockers and remaining gaps.
Neither many tests nor green unit results certify the whole persona workflow.
