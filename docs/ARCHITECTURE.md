# Architecture

```
sources ──► loaders ──► scan_one() per prompt ──► dedupe (MinHash/LSH) ──► tiers ──► exporters
 CSV         io.load     rules: risk + context     64 perms, 16 bands,        approved   report.html / report.json
 JSON                    quality: text|visual      exact Jaccard >= 0.8       review     approved.csv (prompts.chat schema)
 SKILL.md dirs           category classifier                                  blocked    findings.sarif (code scanning)
                                                                                         skills/<name>/SKILL.md + evals + PROVENANCE
transports: CLI (cli.py) · http.server (server.py, EKS) · Vercel function (api/scan.py) ──► api.handle()
optional:   judge.py → OpenAI-compatible endpoint (review tier only, advisory)
```

Design choices
- **Stdlib only.** Nothing to patch, runs in distroless, starts fast in serverless.
- **Rules are data** (`rules.py`), extendable via YAML/JSON (`--rules`).
- **Context never clears a finding**, it only lowers it one level. Humans see every borderline case.
- **Secrets are redacted** in every output; contributor emails are never copied into skill packs.
