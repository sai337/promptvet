# Acceptance checks

| # | Done when | Proved by |
|---|---|---|
| 1 | Jailbreak, injection, secret, adult prompts are blocked | `tests/unit/test_core.py`, golden set (recall 1.0) |
| 2 | Safe prompts are approved (no medium/high finding) | golden set (precision 1.0) |
| 3 | Defensive or negated mentions go to review, never block | golden `borderline` label, `false_blocks == 0` |
| 4 | Secrets are never echoed in reports; placeholder keys ignored | `test_secret_is_redacted_and_placeholder_ignored` |
| 5 | Near-duplicates are found and the better copy is kept | `tests/unit/test_dedupe.py` |
| 6 | Approved export uses prompts.chat's CSV schema | `test_load_csv_and_exports` |
| 7 | SKILL.md pack has frontmatter, inputs, guardrails, evals, provenance, no contributor emails | `test_skill_pack`, `io._contributor` |
| 8 | CLI gate exits 1 when anything is blocked | `test_cli_scan_outputs_and_gate` |
| 9 | API validates input (400/413) and returns tiers | `test_api_contract`, `test_http_server_roundtrip` |
| 10 | Same e2e suite passes on POC and EKS | `tests/e2e` with `BASE_URL` |
| 11 | Full prompts.chat audit runs end-to-end | `scripts/build_report.py`, CI `audit` job |
| 12 | Custom org rules can add and disable rules | `test_custom_rules_file` |
