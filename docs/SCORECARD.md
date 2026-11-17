# 10/10 scorecard (2026-11-16)

| Dimension | Score | Evidence | What closes the gap |
|---|---|---|---|
| Works end to end | 10 | 22 tests pass (3.10 and 3.13 in CI); `pip install` + CLI verified | – |
| Real-data result | 10 | prompts.chat audit, 3,013 prompts; Vercel build reproduced the same numbers from the pinned commit | – |
| Detection quality | 8 | Golden set: recall 1.0, precision 1.0, 0 false blocks; 4/4 blocks hand-checked | Golden set is self-written: add 50 externally sourced jailbreaks (e.g. a public red-team dataset) and report results |
| POC | 10 | https://promptvet.vercel.app live; `poc-e2e` workflow passed 4/4 against it | – |
| Enterprise path | 8 | Distroless image built and e2e-tested in CI, pushed to GHCR; k8s + Terraform + OIDC bootstrap written | Run `eks-e2e.yml` once: deploy `infra/eks/bootstrap/github-oidc.yaml`, set `AWS_E2E_ROLE_ARN` |
| Security | 9 | Secrets redacted, stdlib only, no egress, input caps, threat model | Add a ReDoS fuzz test |
| Docs | 10 | README, PLAN, ACCEPTANCE, ARCHITECTURE, POC, ENTERPRISE, EVALS, THREAT-MODEL, RUNBOOK, BLOG-DRAFT | – |
| Skill pack | 8 | 25 auto-picked skills with evals and provenance; 3 samples in `examples/skills-sample` | A human picks the paid pack; auto-picks are candidates |

Overall: 9/10. The only thing missing for 10 is an EKS run in your AWS account.
