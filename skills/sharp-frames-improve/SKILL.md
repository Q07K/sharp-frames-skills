---
name: sharp-frames-improve
description: >
  Apply selected review findings or perform a requested, scoped code improvement/refactor with before/after verification and a debt/impact handoff. Use for 지적한 항목 수정, 이 부분 개선해, or apply these audit findings. A request to review, audit, map, list debt, or show impact alone does not authorize implementation.
---

# Apply a bounded improvement

Implement the improvement the user actually requested. Reuse supplied review,
audit and debt artifacts as leads, then verify each proposed fix against current
code and requirements. A reviewer's assertion is not authority to remove working
behavior. Work independently on understood, authorized items while clarifying
only ambiguity that changes outcomes. Do not require a new planning approval
for ordinary implementation already requested by the user.

## Establish the change and baseline

Inspect local rules, branch/dirty state, intended behavior, affected callers and
actual verification commands. Preserve unrelated work. Name the selected items
and whether each is behavior-preserving refactoring or a behavior correction.
Record meaningful before-state evidence before changing it; valid existing
evidence can be reused with its revision and input identity. A preexisting failing
check stays visible rather than becoming a silently accepted new baseline.

## Make a coherent correction

Find existing policy owners and compatible utilities before introducing code.
Keep independent rules separate. Prefer names, boundaries and useful contracts
that reduce reasoning; do not create layers, interfaces or factories just for
appearance. Use appropriate validation, authority, resource lifetime, transaction
and concurrent-state handling for the operation. Comments should explain relevant
rationale/contracts, not narrate every statement.

Apply a reviewable batch that fully solves the selected obligation. Do not use
TODOs, mocks or a new debt entry as substitutes for requested functionality.
Avoid unrelated cleanup and speculative features. Respect existing APIs and
consumers unless the requested correction intentionally changes them.

## Verify, inspect and account

Run checks capable of exposing the changed failure, boundary or contract and
affected caller regressions. Expectations come from requirements, not a copy of
the new algorithm. Do not weaken checks to make them pass. A small reversible
edit does not automatically need new tests or a full repository suite.

Review the final diff for scope, missed callers, duplicated policy, unnecessary
indirection/comments and verification blind spots. Repair material issues in scope.
For the handoff connect the requested item to its actual code and verification;
identify unresolved/preexisting versus introduced/resolved debt, with a reason
and revisit trigger for material deferrals. Do not auto-create ledger files.

Report observed before/after effects separately from expected maintainability
benefits; include added costs or limitations and use comparable measurements
for numeric claims. Do not claim measured review-time savings from fewer lines.
Avoid automatically running every suite command on each change. Publish, deploy,
merge and external issue/comment actions retain their own authorization boundaries.
