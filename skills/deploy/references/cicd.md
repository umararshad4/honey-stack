# CI/CD deploy

## OIDC to the cloud (no stored keys) — the 2026 default
Give the workflow `permissions: { id-token: write, contents: read }`, then assume a cloud role via OIDC.

AWS:
```yaml
permissions: { id-token: write, contents: read }
steps:
  - uses: aws-actions/configure-aws-credentials@v4
    with:
      role-to-assume: arn:aws:iam::<acct>:role/<role>
      aws-region: us-east-1
```
The IAM role's trust policy uses `sts:AssumeRoleWithWebIdentity` with a condition scoping `sub` to `repo:ORG/REPO:ref:...` and `aud` = `sts.amazonaws.com`. GCP: Workload Identity Federation + `google-github-actions/auth`. Azure: `azure/login` with a federated credential (no secret). Prefer GitHub **Environments** with required reviewers for prod.

## Strategies & rollback (predefine the rollback before deploying)
- **Rolling** — default, gradual in-place.
- **Blue/green** — two envs, switch traffic atomically; roll back by switching back.
- **Canary** — shift a small % first, watch metrics, then ramp.
- Rollback: ECS → previous task def; Cloud Run → `update-traffic` to prior revision; K8s → `rollout undo`; Helm → `helm rollback`; Vercel → promote the previous deployment.

## Common errors
1. `Not authorized to perform sts:AssumeRoleWithWebIdentity` → trust `sub`/`aud` doesn't match repo/branch, or missing `id-token: write`.
2. Deploy succeeds, app broken → migrations not run, or env not set for the target env.
3. Image built for the wrong arch → build `linux/amd64` (or `arm64` for Graviton/Fargate) with buildx.
