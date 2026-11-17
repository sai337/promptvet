# POC on Vercel

- `public/index.html`: paste-a-prompt UI. `api/scan.py`: Python function, same contract as the container.
- Build: `python3 scripts/build_report.py` downloads prompts.csv at a pinned commit and renders `public/report.html` + `summary.json`.
- No secrets or env vars needed. The judge is off on the POC.
- Verify: `BASE_URL=https://<deployment> pytest -q tests/e2e`.
