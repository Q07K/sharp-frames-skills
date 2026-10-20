# Fixed qualitative comparison rubric

Compare anonymized pairs independently; do not infer their conditions. This is
an AI review with condition labels hidden, not measured human review time.
Use the shared task prompt and original fixture. Equal quality warrants a tie.
Do not prefer more files, types, comments, tests or layers merely by count.

For each pair, report correctness concerns separately from maintainability.
Score these maintainability dimensions 0–4 with concrete code evidence:

1. Policy ownership and semantic reuse: one appropriate authoritative rule;
   no copied policy that drifts or unrelated policies forced into one helper.
2. Change locality and clear responsibilities: understandable request flow,
   transactions and side effects; useful boundaries without pass-through layers.
3. Readability and contracts: meaningful units/names, useful types and comments;
   no explanatory noise, hidden mutation or misleading exception contracts.
4. Verification and truthful handoff: meaningful independent checks of the
   requested behavior and failures; no weakened original checks or unsupported
   claims. Additional test count alone earns no points.

Winner: A, B, or tie. A material behavior defect outweighs cosmetic advantages.
Explain differences only when they affect understanding, safety or future changes.
Give file and line evidence and record uncertainty. These ordinal model judgments
are exploratory, cannot independently prove real developer productivity gains,
and should not be averaged into a universal quality score.
