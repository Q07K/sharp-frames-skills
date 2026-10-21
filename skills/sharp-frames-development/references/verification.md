# Verification and review evidence

## Establish the oracle

Expected behavior comes from requirements, documented contracts, and domain policy.
The new implementation must not be the sole oracle for its own tests. Existing
regressions, independently read specifications, integrations, and invariant checks
can expose a shared misunderstanding.

Reproduce a relevant bug when feasible. Test behavior changes and important
preserved behavior. A changed status or error contract is observable behavior,
even if the surrounding work is mostly mechanical refactoring.

## Drive behavior changes with tests

Before implementation, inspect existing tests and baseline failures, the real
runner/collection configuration and commands. Define the intended behavior and
failure conditions independently of the implementation. For each small behavior
increment, write or extend a test, run it against the before-state, inspect why it
fails, implement only the increment, run the same test, then refactor and run
affected regressions. Use a named observable behavior rather than one test per
private method. Existing correctly passing cases remain useful; do not break code
or change an assertion merely to create a red stage.

A missing new interface can be an initial red signal, but prove its observable
assertions once wired. Dependency/import/setup failures unrelated to the feature
are a blocked check, not a reproduced defect. If implementation precedes a test,
say so; do not reconstruct or invent a test-first chronology. An isolated before
revision can establish regression sensitivity when practical without resetting
unrelated work. A behavior-preserving refactor normally starts and stays green.

Use a targeted counterexample or isolated mutation when a critical test might
pass with the core rule broken: would it catch bypassed authorization, an omitted
write or a double side effect? Keep such experiments isolated and restore them;
do not add a mutation tool or a numeric mutation target by default.

## Design cases beyond the new branch

Identify the changed contract and nearby preserved contracts, actual user roles,
ownership/tenant boundaries, prerequisites and state transitions. Choose applicable
equivalence classes and boundaries, missing/null/invalid inputs, empty/duplicate
cases, retry/reentry, stale state, external failure and partial completion. Select
the dimensions that can cause harm here; do not create their full Cartesian product
or invent unsupported business rules. Explicitly record consequential unknown policy.

For each affected persona, trace a representative goal through connected actions:
setup/authentication, action, response, follow-up read or repeat, persisted state
and absence of forbidden side effects. Include a meaningful denied/failure/recovery
journey where risk warrants it. Personas are roles with different authority, state
or goals, not cosmetic names. Check identity/session changes and cross-user reads
when relevant. Never infer browser coverage from direct service calls.

Keep most checks focused; add integration/contract tests where modules meet and a
small number of critical workflows through real application entry points. For an
API service, multi-request API tests with a disposable database can be workflow
tests. For UI changes, exercise the actual visible interaction as well. Keep internal
authorization/calculation/persistence real; isolate unavailable external providers.

## Maintain a reviewable case inventory

Use established case IDs/names and test documents. For a nontrivial feature without
such a convention, use tests/CASE_MATRIX.md, grouped by feature. A compact row can
link requirement/contract source, persona and precondition, action/sequence,
expected response and state, risk, test path/name and coverage gap. Stable test
names can serve as IDs. Extend the existing inventory instead of creating one
document per run. Tiny local changes can use their test names and handoff directly.

Keep definitions separate from dated execution evidence. Distinguish planned,
implemented-but-not-run, passed, failed, skipped and blocked. A result needs the
command, relevant revision/worktree state and environment; an old pass is not the
current result after code or fixtures change. Preserve superseded case history
and its replacement when a requirement intentionally changes. Track material
deferrals with reason and revisit condition, not fictional owners or dates.

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
Classify a test edit as an authorized contract change, a demonstrated test defect,
or a behavior-preserving test refactor. Show the old/new expectation and independent
requirement evidence for a changed oracle; a current implementation result is not
that evidence. Resolve material ambiguity instead of silently selecting its oracle.
Ordinary justified test edits do not require a new blanket approval round.

Review fixture, snapshot, mock, tolerance, skip/xfail, retry and collection/CI
changes as well as assertion text. Check relevant collected case identities and
skipped/not-run cases against the baseline; the total test count alone can hide
replaced obligations. Do not substitute a mocked success path for a real workflow
or update snapshots wholesale because the runner offers a refresh flag. A flaky
test's first failure remains evidence; a retry pass does not erase it. Quarantines
need the reason, coverage gap and revisit condition under project policy.

These instructions do not make files tamper-proof. Stronger assurance requires
acceptance oracles/graders outside the implementation writer's editable scope and
reviewed changes to protected checks. CI and reviewer protections must actually be
configured to enforce that boundary; a manifest or another AI reviewer editable by
the same writer is not independent enforcement. Do not change branch protection,
CI or tool permissions automatically.

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
- Did test changes remove obligations, hide failures or reduce collected coverage?
- Do persona workflows verify final state and failure recovery at real boundaries?

An AI reviewer adds feedback but is not an independent correctness oracle.
Preserve a readable connection between requirement, implementation, and evidence.

## Handoff

Use the established PR/report format. For nontrivial changes, useful evidence is
behavior before/after; reuse or reason for a new module; caller/contract impact;
executed checks and environment limits; and remaining unverified behavior.
Keep trivial handoffs short. Do not say "all tests pass" for a subset. Earlier
results may no longer apply after a meaningful subsequent code change.
