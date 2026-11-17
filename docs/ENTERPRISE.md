# Enterprise path (EKS)

1. Image: `Dockerfile` (distroless, non-root, read-only FS). CI pushes `ghcr.io/sai337/promptvet`.
2. Manifests: `infra/eks/k8s/base` (restricted PSA, HPA 2–10, PDB, NetworkPolicy with DNS-only egress, internal ALB).
3. Org rules: mount a ConfigMap and add `--rules /etc/promptvet/rules.yaml` to the container args.
4. Judge (optional): set the three `PROMPTVET_JUDGE_*` env vars from a Secret, point the base URL at your internal AI gateway, and add one egress rule for it.
5. SSO: put the service behind your ingress auth (OIDC at the ALB, or an auth proxy). The scanner itself is stateless and stores nothing.
6. Ephemeral e2e: deploy `infra/eks/bootstrap/github-oidc.yaml` once in a personal AWS account, store the role ARN as `AWS_E2E_ROLE_ARN`, add a reviewer to the `eks-e2e` environment, then run `eks-e2e.yml` (apply → e2e → destroy, $20/month budget alarm).

Status: manifests and workflow are written and YAML-validated; the cluster run has not been executed (needs AWS access).
