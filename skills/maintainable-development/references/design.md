# Design decisions that survive the next change

Use relevant sections as decision criteria, not a demand to introduce every
named technique.

## Reuse and ownership

Find the authoritative implementation of a business decision through callers and
tests. Matching names or text is insufficient. Compare units, rounding, errors,
authorization assumptions, side effects, and domain ownership.

| Choice | Appropriate when | Check |
| --- | --- | --- |
| Call an existing module | Its contract matches | Connect the real caller and exercise it |
| Extend a module | The need belongs to the same policy | Preserve or intentionally migrate callers |
| Add a focused module | A real responsibility is missing | Keep a useful interface and integrate it |
| Keep similar code separate | Policies change independently | Name the distinction; avoid flag-filled helpers |
| Use platform/library support | A maintained capability fits | Verify version, integration, costs, failures |

Do not mandate "abstract after N copies" or "zero duplicated lines." Prefer one
authoritative shared business rule. Incidental duplication may be cheaper than
coupling unrelated domains. Do not gather everything into `utils` or `common`.

Use established domain names and colocate related behavior/tests. A public
interface and representative example should make a module usable without reading
its whole implementation. Link existing docs rather than duplicating the API.

## Boundaries and dependency direction

Keep transport near transport and storage near storage. Where useful, make domain
policy callable without a web server or DB. Do not require a Repository/Service
class for every trivial operation.

Judge a split by whether someone can understand or change the policy with less
context. If it merely adds files, pass-through calls, or cycles, reconsider.
Before changing a public/shared contract, inspect callers and serialized formats.
Preserve compatibility or implement the requested migration. A helper used by two
endpoints is a shared dependency even if it is not a package.

## Names, types, and comments

- Prefer domain and unit names (`amount_won`, `timeout_seconds`) to vague data names.
- Name calculation stages instead of repeatedly redefining `total`.
- Use useful types for stable contracts, without elaborate types for obvious locals.
- Represent distinct states explicitly when it prevents invalid combinations.
- Runtime checks and static types solve different problems. An `int` does not
  prove positive quantity or ownership by the authenticated user.
- Comment on rationale, domain constraints, non-obvious behavior, and meaningful
  algorithm explanations; do not narrate ordinary assignments.
- Document public usage conditions, units, exceptions, and mutation when relevant.
  Do not require a boilerplate docstring on every helper or test.
- Never invent a historical policy rationale or link to justify generated code.
  Resolve an unknown policy if it materially changes behavior.

## Failure, trust, and state

Inspect a concern when the task actually touches it:

| Concern | Questions |
| --- | --- |
| Identity/access | Is identity trusted? Is this action allowed on this object? |
| Money | Are units, currency, precision, rounding, and policy order explicit? |
| Transactions | Which writes are atomic? What happens on rollback/commit failure? |
| Concurrency | Can parallel requests pass the same precondition? Is enforcement atomic? |
| Retries/external calls | Can retry duplicate effects? What are timeout/recovery semantics? |
| Persistence | Are constraints/data compatible? Is migration needed? |
| Resources | Are sessions/files/connections released? Is work bounded appropriately? |
| Diagnostics | Is context useful without leaking secrets in logs/responses? |

Use DB guarantees where durable invariants require them; a read-then-write `if`
can race. Do not blindly retry effects whose outcome is unknown. A DB rollback
cannot undo an external service's completed action.

## Avoid decorative architecture

Do not add knobs, plugins, generic base repositories, distributed services, or
dependencies just in case. Real extension needs may justify an abstraction;
hypothetical future features usually do not. Scope discipline does not excuse
missing error handling or leaving the requested integration unfinished.
