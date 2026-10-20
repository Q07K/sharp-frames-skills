# Verification and review evidence

## Establish the oracle

Expected behavior comes from requirements, documented contracts, and domain policy.
The new implementation must not be the sole oracle for its own tests. Existing
regressions, independently read specifications, integrations, and invariant checks
can expose a shared misunderstanding.

Reproduce a relevant bug when feasible. Test behavior changes and important
preserved behavior. A changed status or error contract is observable behavior,
even if the surrounding work is mostly mechanical refactoring.

## Select useful checks

| Change | Useful evidence |
| --- | --- |
| Calculation/policy | Boundaries, errors, units, invariants |
| Shared helper | New behavior and affected callers |
| API | Validation, status, response contract, access, real handler path |
| Frontend behavior | Real interaction, loading/empty/error states, keyboard/accessibility or layout when affected |
| Persistence | Real constraint/transaction behavior and migration impact |
| Concurrent state | A test or analysis exposing the actual race |
| External integration | Adapter/contract tests and clear fake/live limitations |
| Build/config/dependency | Relevant build/startup/type/compatibility checks |
| Tiny cosmetic change | Direct inspection or relevant existing checks; no automatic new test |

Run fast focused checks first, then required broader checks and justified
integration coverage. Do not rerun a passed full suite without a new change or
unresolved concern. Mocks belong at unavailable/expensive external boundaries,
not in place of the policy, transaction, or endpoint claimed to be tested.

Avoid tests that merely reproduce formulas, implementation call order, or new
wording when observable behavior is what matters.

## Keep checks honest

Investigate failures before calling them unrelated. Do not weaken assertions,
remove tests, disable checks, broaden catches, or add unexplained ignores to pass.
For intentional behavior changes, update contracts/tests with explicit rationale.

Discover current commands and pinned environments. Do not automatically install
a new lint/type framework, rewrite CI, or force a style migration. If a necessary
check is missing, implement within authorized scope or report the blocker.

## Review the diff

Check code, tests, and contracts together:

- Is the whole requested path implemented and integrated?
- Is an existing capability unnecessarily bypassed, copied, or shadowed?
- Did a shared contract or caller change accidentally?
- Do boundaries reduce reasoning or only add indirection?
- Are failures truthful and diagnostics appropriate?
- Did input validation hide an access-control or concurrency omission?
- Do comments add information and remain true?
- Do types express rather than evade the contract?
- Are unrelated files/configurations/generated artifacts changed?
- Could tests pass while the central requirement is wrong?

An AI reviewer adds feedback but is not an independent correctness oracle.
Preserve a readable connection between requirement, implementation, and evidence.

## Handoff

Use the established PR/report format. For nontrivial changes, useful evidence is
behavior before/after; reuse or reason for a new module; caller/contract impact;
executed checks and environment limits; and remaining unverified behavior.
Keep trivial handoffs short. Do not say "all tests pass" for a subset. Earlier
results may no longer apply after a meaningful subsequent code change.
