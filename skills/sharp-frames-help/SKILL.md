---
name: sharp-frames-help
description: >
  Explain Sharp Frames commands, choose the right capability, and show invocation examples. Use for sharp frames help, 명령어 목록, Sharp Frames 사용법, or which Sharp Frames skill should I use. This is a help display; do not inspect or mutate a project merely to list commands.
---

# Show the available capabilities

Read [the command catalog](references/catalog.json) and show a compact table of
command, purpose, and source-edit behavior in the user's language. Include a
relevant example and the difference between reviewing a diff and assessing a
whole repository. No project scan, tests, file writes, mode changes or global
configuration are needed to answer a help request.

The catalog describes this package, not proof that every skill is installed in
the host. For a request about installed availability, check available metadata
or the actual installation rather than assuming every catalog entry is present.
Natural-language requests can select capabilities where the host supports it;
explicit `$skill-name` examples are the direct Codex form used by this package.
Do not promise slash-menu registration, persistent always-on activation, hooks,
status panels or telemetry without an actual corresponding host adapter.

Route by intent: explore what to build (brainstorm), sequence a substantial change
(plan), design/manage test cases and persona workflows (test), evaluate dependency
choices with current evidence (versions), implement a clear feature
(maintainable-development), review a change, assess whole-project
risks, explain flows/reuse candidates, account for debt, or explain improvement
effects. Listing commands does not invoke them. A request for review, audit, debt,
gain, map, brainstorm, plan or versions alone keeps implementation unchanged;
applying changes is a separate user intent.

The test skill can plan cases read-only or write/run requested tests. It does not
authorize production fixes or changing expectations merely to pass. Feature
implementation already includes test-first work; a separate test call is optional.
