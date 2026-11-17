# Runbook

- Health: `GET /healthz`, `GET /readyz` → `{"ok": true}`.
- Logs: one JSON line per request (`path`, `msg`).
- Slow scans: large batches are CPU-bound; HPA scales on CPU 70%. Split batches above 500 prompts.
- False block reported: reproduce with `promptvet check "<text>"`, add the case to `golden.jsonl` as `borderline` or `safe`, fix the rule, run `make eval`.
- Missed risk reported: add it as `unsafe` with its category, add or tighten a rule, run `make eval`.
- Refresh audit numbers: bump `PROMPTS_CHAT_SHA` in `scripts/build_report.py`, Dockerfile and Makefile, redeploy.
