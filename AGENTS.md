# Sharp Frames contributor guidance

This repository distributes an agent skill, supporting guidance, and synthetic
evaluation fixtures. Preserve the distinction between package validation,
behavioral evaluation, and actual platform-trigger testing.

Keep general decision criteria in the skill and conditional detail in references.
Change rules in response to demonstrated failures rather than accumulating
universal prescriptions. Do not put evaluation answers into the skill.

Run `python tools/check_repository.py` after edits. Use the supplied evaluation
tasks on independent copies for meaningful behavioral changes. Report ties,
failures, missing metrics, and limited sample sizes honestly. Do not change the
baseline fixture or graders to manufacture an apparent performance gain.
