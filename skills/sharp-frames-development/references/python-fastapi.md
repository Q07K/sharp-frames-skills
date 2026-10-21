# Python and FastAPI implementation

Follow actual project versions/conventions. Do not force async conversion or a
prescribed folder tree. Read only concerns relevant to the current task.

## Contracts

Use supported Pydantic APIs for stable requests/responses. Validate relevant
ranges, lengths, and invariants: annotations alone are not runtime validation.
Distinguish schemas from ORM state where responsibilities differ. Return an
intentional public shape rather than all internal fields.

Obtain identity and permissions from trusted auth context; check access for the
object/action. Use authoritative prices/privileges, not client claims. Match HTTP
status/error handling to the established contract. An error dictionary under a
success status miscommunicates failure unless explicitly required by that API.

## Application structure

Follow the established application/router and domain/layer layout. Use `APIRouter`
when a real split of routes is useful, rather than reorganizing a tiny application
as a prerequisite to a local change. Make transport mapping
recognizable and isolate substantive reusable policy where it helps. A small
endpoint can query/write directly; do not generate a Service/Repository/Interface
stack for each model. Introduce an application boundary when an operation truly
spans policies/effects, rather than a universal helper with many flags.

## Sessions and transactions

- Scope/close sessions using project dependencies/context managers; no global
  request session.
- Identify the transaction owner. Keep atomic writes together and retain failure
  diagnostics.
- Check transaction state before adding `session.begin()`: auth/earlier reads can
  already start a transaction on the shared session.
- Understand actual `flush`, `commit`, expiration, and refresh configuration.
  Failure after successful commit does not prove an order was never created.
- Use database enforcement for relevant concurrency/uniqueness invariants;
  read-then-write checks alone can race.
- DB rollback does not undo external effects. Examine actual payment/job/retry
  guarantees without automatically adding distributed infrastructure.

## Async and resources

Use `async def` for awaitable non-blocking work. Do not block the event loop with
sync DB/HTTP calls. Use sync endpoints or established offload patterns where
appropriate. CPU work does not become concurrent computation by adding `async`.
Inspect query count, pagination, timeouts, and cleanup when relevant, before caches.

## Readability and failures

Use meaningful names/units and annotate useful contracts. Respect installed
Pydantic optional/nullable semantics. Avoid catch-all handlers that swallow
defects, return internal strings, or misreport success. Do not use `Any`, casts,
`type: ignore`, or `noqa` as substitutes for understanding an interface.

Comment on non-obvious policy. Docstrings describe usage, not a line-by-line Python
tutorial or mechanical repetition of annotations.

## Tests

Use existing formatter/linter/type/pytest configuration; do not assume Ruff, mypy,
async clients, or a particular Python version. Consult official docs for uncertain
version-specific APIs. Test actual handlers with suitable dependency overrides,
keeping internal policy real. Use a test DB capable of exercising the relevant
constraints: an in-memory fake cannot prove production transaction guarantees.

Use the real test client/ASGI path for important multi-request persona workflows,
with trusted test identities, isolated state and relevant follow-up reads. Check
authorization and persisted side effects, not just HTTP status. Dependency overrides
may supply test auth or an external adapter; do not override away the policy or DB
constraint the test claims to verify. Test-client flows do not prove browser UX,
production isolation levels or live provider behavior.

For money, establish unit/currency/rounding and check thresholds. Avoid unsuitable
binary float arithmetic. Never import a discount, tax, shipping, or auth policy
from an illustrative example as if it were the project's requirement.
