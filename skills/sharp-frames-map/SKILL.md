---
name: sharp-frames-map
description: >
  Map an unfamiliar repository or subsystem and find existing capabilities before implementation. Use for 프로젝트 구조 파악, architecture walkthrough, where does this behavior live, or reusable module discovery. Build a factual code map with evidence and gaps; do not turn explanation into an audit verdict or code rewrite.
---

# Find where the behavior lives

Create a concise map that helps a developer enter the codebase and reuse what
already exists. Read only the scope required by the request; keep source, index
and branch unchanged. Do not create architecture files unless requested.

Start with project purpose, repository instructions, revision/dirty state,
workspace packages, stack manifests and entry points. Follow selected user flows
through validation/authority, domain decisions, persistence, external systems and
tests. Cite files and symbols at each boundary. Record where policy is owned,
which callers depend on it, where configuration enters, and which assumptions
are established or still unknown. Do not infer dependencies from folder names.

For reuse discovery, search domain concepts, caller patterns and alternate names.
Compare candidate inputs/outputs, errors, side effects, units, authority and scope.
Return a table of capability, location/symbol, actual responsibility, callers/tests,
fit for the requested use and caveats. Mark hypotheses as candidates until the
implementation is read. Avoid claiming exhaustive absence after a few searches.

If similar code has different policies or change lifecycles, explain that boundary
rather than prescribing a universal helper. Identify compatible extension points
and important caller contracts. A diagram is useful only if it clarifies a real
flow; support arrows with code evidence, and label missing external knowledge.

End with suggested starting files and coverage/unread areas. This mode describes
the system; prioritize defects only if the user also requested an audit. Do not
claim to understand the whole repository from its README and file list.
