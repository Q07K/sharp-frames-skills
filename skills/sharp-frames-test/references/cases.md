# Case design, workflow coverage and change records

## Make risk analysis concrete

Begin with the requirement and independently inspected contract, then trace the
entry point, decisions, state, integrations and caller-visible outcomes. An invalid
input class matters because of a contract or failure mechanism, not just because
a framework can generate it. Useful dimensions, when applicable, include:

- Identity, role, object ownership, tenant, expiry or session changes.
- Missing/empty/null/malformed data; ranges, units and exact boundaries.
- Allowed/forbidden state transitions, duplicates, retries and repeated actions.
- Partial writes, provider timeout, reconciliation and recovery.
- Concurrent conflict and stale reads for shared state.
- Existing callers and contracts that must remain compatible.

Select combinations by actual risk. A read-only preview and a paid cancellation
have different hazards. Do not guess a refund policy, retry limit or admin privilege
because the test needs an expected value. List the unresolved decision instead.

## Model personas as authority and state

Use roles the product actually has, not invented demographic biographies. The
same endpoint may behave differently for an owner, another user, a read-only
operator or an expired session. A workflow case describes precondition → actions
→ observations → final state. A status-code assertion alone cannot prove that an
unauthorized write did not occur or that a repeat did not duplicate a side effect.

Pick a few journeys that span the relevant connections. Reuse real auth/policy
and internal persistence where the test claims to verify them. Supply test identity
through the trusted test boundary; do not let a mock grant the permission whose
enforcement is under test. Use isolated clocks/data/provider stubs when necessary,
and disclose what those stubs cannot establish. Browser paths require actual
rendered interactions; API tests are valuable but cannot establish UI completion.

For a recovery journey, assert both immediate failure and what the user sees or
can do next, including persisted data and forbidden effects. Use teardown and
isolation so one persona's session or state does not leak into another case.

## Suggested case inventory

Adapt the existing repository format. Otherwise group a compact matrix by feature
inside tests/CASE_MATRIX.md. For small changes test names plus the handoff suffice.

| Stable case ID / test name | Requirement or contract source | Persona / starting state | Actions and relevant input | Expected response and final state | Level and test location | Risk / gap |
| --- | --- | --- | --- | --- | --- | --- |
| Existing or proposed name | Actual requirement link or inspected policy | Real authority/ownership and prerequisite | Sequence including repeat/follow-up where needed | Observable result, stored state, forbidden effects | Unit / integration / API workflow / browser workflow, path and name | Coverage limit or unresolved policy |

Keep planned cases visibly distinct from executable tests. Link parameterized cases
to identities/inputs where useful. Reuse an existing case for the same obligation;
do not duplicate it solely to inflate counts. When a contract changes, retain why
the case was superseded and point to its replacement.

## Execution evidence

Store run evidence in the repository's established place or the task handoff:
command, revision/worktree state, environment/input identity, actual outcome and
limitations. The matrix defines obligations; it is not a timeless pass badge.
Distinguish planned, implemented-not-run, passed, failed, skipped and blocked.
For TDD, capture the relevant before failure and after pass, including any test
changes between them. Passing a different or weakened case is not the same cycle.

## Test change accountability

For each material changed oracle or removed obligation, explain:

1. The old and new expectation or collected case.
2. The independent requirement change, demonstrated test defect, or equivalent
   behavior-preserving test refactor that justifies it.
3. The replacement coverage and actual execution evidence or remaining gap.

Review fixtures, snapshots, mocks, retries, tolerances, skip/xfail and test selection
alongside assertions. Configuration can exclude a case without deleting its file.
Characterization tests document observed legacy behavior; label that provenance
instead of automatically treating a known defect as a required business contract.

For stronger separation, maintain independent acceptance checks in an actually
protected reviewer/CI scope outside the implementation writer's permissions.
A hash inside the same writable tree only detects drift relative to a trusted
baseline; it does not prevent rewriting both code and hashes. Do not change host
permissions, CI or branch protection as an automatic side effect of writing tests.
