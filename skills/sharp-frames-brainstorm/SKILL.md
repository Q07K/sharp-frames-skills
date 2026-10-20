---
name: sharp-frames-brainstorm
description: >
  Explore an unclear feature or product problem, compare viable approaches, and form a concrete recommendation with acceptance criteria. Use for 브레인스토밍, 기능 아이디어 구체화, 요구사항 탐색, or choosing what to build. Clear implementation requests do not require a separate brainstorming ceremony; execution sequencing belongs to planning.
---

# Decide what is worth building

Turn uncertainty about the goal or solution into a decision a human can assess.
Scale the exploration to the uncertainty. A clear small feature can proceed
through the normal implementation workflow without this separate exercise.

## Ground the problem

Identify the user, the troublesome situation, the desired outcome, constraints,
and what would count as success. Separate what the user specified, what the
project demonstrates, and what you are proposing. Read relevant existing flows,
modules and conventions when a repository is supplied; do not design a parallel
feature because its current name differs from the request.

Ask only questions whose answers materially change the recommendation. Prefer
a concrete scenario to a generic questionnaire. Continue useful independent
research while waiting; do not treat silence as approval of a required business
decision. For optional uncertainty, offer a stated assumption and a provisional
recommendation. Do not reopen choices the user already made.

## Compare choices

Consider the smallest sufficient change, reuse or extension of existing behavior,
and a genuinely different approach when one offers a meaningful tradeoff. Compare
user benefit, maintenance burden, operational cost, failure modes and reversibility.
Do not pad the comparison with intentionally bad alternatives or invent savings.
If keeping the current behavior is viable, include why it may be sufficient.

Check current primary sources when the choice depends on changing external
capabilities. Mark facts, firsthand experience and your inference separately.
A prototype or experiment can resolve an important unknown, but label its limited
purpose and obtain implementation scope from the request before creating it.

## Hand off a decision

Lead with the recommended direction and why it fits this project. Give the
alternatives and the reason for rejecting or deferring them, the proposed scope
and non-goals, observable acceptance criteria, and unresolved decisions that could
change the design. State whose decision each material assumption is.

Stop exploring once the next step is clear. Do not create or commit a design
document by default; save one when requested or required by project conventions.
A brainstorming-only request does not authorize source changes. If implementation
is already requested, continue within that authorization once required questions
are resolved; do not add a ritual approval round or require another installed skill.
