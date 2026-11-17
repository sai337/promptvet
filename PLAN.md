# PLAN

## Goal
A repeatable trust gate for prompt and skill libraries: decide what is safe to import into a company library, what needs a human, and what must never ship.

## What it proves
1. A deterministic, explainable scanner can triage a 3,000-prompt public library in seconds, with every block checked by hand and found correct.
2. One engine, four surfaces: CLI, CI gate (SARIF), serverless POC, Kubernetes service.
3. Public CC0 prompts can be turned into a vetted SKILL.md pack with provenance.

## Scope
In: rules engine, quality rubrics (text + visual), near-dup detection, tiers, exporters (JSON, HTML, approved CSV, SARIF, SKILL.md pack), optional LLM judge, HTTP API, Vercel POC, EKS manifests + ephemeral e2e workflow.
Out (later): multi-language rules, ML classifier, web UI for reviewers to approve/reject, signed skill packs.

## Architecture
See docs/ARCHITECTURE.md. Stdlib-only Python package; transports (CLI, http.server, Vercel handler) call one `api.handle()`.

## POC vs enterprise
POC: Vercel static UI + Python function, audit built at deploy time from a pinned commit.
Enterprise: distroless non-root image on EKS behind an internal ALB, no egress, HPA/PDB, custom org rules mounted as a ConfigMap, judge routed through the company AI gateway.

## Risks
- Regex rules miss paraphrased attacks → optional judge, golden set grows with every miss, review tier as safety net.
- False blocks on defensive content → context downgrade (never clears), borderline label in evals with a zero-false-block gate.
- Upstream data drift → pinned commit, nightly eval.
