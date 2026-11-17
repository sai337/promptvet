# I audited the world's largest open prompt library. Here's what a company should never import.

**Problem.** prompts.chat has 170K+ GitHub stars and ~3,000 public-domain prompts. Teams want an internal prompt library, but nobody vets community prompts before employees copy them into tools connected to company data.

**What I built.** promptvet, an open-source gate: rule-based risk scan, two quality rubrics (text and image prompts), near-duplicate detection, tiers, and exports for CI (SARIF), self-hosted libraries (CSV) and Agent Skills (SKILL.md).

**Results (3,013 prompts, commit 36c1131).**
- 84.7% approved, 15.1% review, 0.1% blocked (4 prompts: a DAN jailbreak and three adult-content prompts; all confirmed by hand).
- 103 prompts (3.4%) had at least one risk finding; 60 link to external URLs; 6 are doctor/lawyer/financial-advisor personas with no disclaimer.
- 416 prompts were too vague to approve automatically (no task, format or constraints).
- 12 near-duplicates.

**Lesson 1: naive rules over-block.** My first run blocked 28. Most were *defensive* prompts quoting attacks ("flag inputs like 'ignore previous instructions'") or image prompts with "nsfw" in the negative prompt. Fix: context lowers severity one level but never clears it, so humans still see it.

**Lesson 2: one rubric doesn't fit all prompts.** A third of "low quality" prompts were image-generation prompts judged by a text rubric. A visual rubric (subject, style, lighting, camera, negatives) fixed it.

**Lesson 3: put the gate where prompts change.** The same engine runs as a CLI, a CI check with SARIF, a serverless POC and a Kubernetes service with no egress.

**Try it.** `pip install git+https://github.com/sai337/promptvet` · live demo: https://promptvet.vercel.app.
