# Evals

## Golden set (`evals/datasets/golden.jsonl`, 72 cases)
Labels: `unsafe` (34, must be flagged with the right category), `safe` (30, no medium/high finding), `borderline` (8, defensive or negated mentions: review is fine, block is not).
Gate: recall, precision, category accuracy ≥ 0.95 and zero false blocks. Current: 1.0 / 1.0 / 1.0 / 0.

Honest caveat: the same author wrote the rules and most of the golden set, so the golden set measures regressions, not real-world accuracy. Several cases were added from real misses found in the prompts.chat audit.

## Real-corpus check (prompts.chat, 3,013 prompts)
- Blocked: 4/4 manually confirmed true positives.
- Iteration log: the first run blocked 28; manual review found defensive prompts quoting attacks, image negative prompts ("nsfw" in a do-not list), "no filters" in photography, `rm -rf /var/lib/apt/lists` and placeholder keys. Fixes: context downgrade, defensive-genre detection, negative-prompt line check, placeholder filter, tighter patterns. Each fix added a golden case.
- Known gaps: paraphrased jailbreaks without trigger words; non-English prompts; 416 low-quality reviews are a rubric judgement, not a risk.

## Nightly
`.github/workflows/evals.yml` writes `evals/results/<date>/golden.json`.
