# Execution notes and deviations

- Date: 2026-10-20 (Asia/Seoul).
- The skill snapshot is the initially published `19a2b7a` version. No skill edits
  or grader changes are made in response to candidate results during these runs.
- The fixture and original regression tests passed before workers started.
- The grader and fixture fingerprints were captured locally before the first
  external candidate grading. This is a local protocol record, not an independent
  public preregistration. Task-1 workers were already running when the grader was
  finalized, and their outputs were not read to choose expectations.
- **Deviation:** protocol.json proposed randomized launch order. Actual execution
  uses alternating/counterbalanced condition launch order, with at most 3 workers
  active. It is not randomized. Do not claim otherwise. Reviewer A/B assignment
  is separately randomized with a fixed seed after all code is produced.
- Each execution has a fresh agent with no parent conversation. Both conditions
  inherit the same configured model and general agent instructions; no model or
  reasoning overrides are requested. The exact model build is not exposed by
  the agent completion metadata, so it is not invented in the report.
- Baseline workers are explicitly instructed not to read or apply skills. They
  still share a tool catalog containing skill metadata; this is instruction-based
  isolation, not a harness that physically disables discovery. Their process
  records are self reports, not complete independently captured tool transcripts.
- Windows sandbox prevents SQLite temporary-file access and hangs TestClient.
  Before comparison workers ran, the original fixture passed in escalated local
  execution. All workers received the same runtime workaround instructions.
- Completion messages do not provide token usage or normalized agent duration.
  They remain unavailable; launch times and test runtimes are not substituted.
- Functional checks use an external copy of original regression tests. Candidate
  test counts and additional test choices are descriptive, not a quality score.
- No automated platform skill-trigger test or actual human review-time experiment
  is included. Blind review means condition labels are hidden from AI reviewers;
  code style may still reveal clues, and one cannot guarantee perfect blinding.
- Three repeats per condition estimate stability on these specific three tasks.
  They do not create nine independent task types or establish broad superiority.
