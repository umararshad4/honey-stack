# AWS deploy

## Pick
- **ECS Fargate** — default for containerized web services; you own the Dockerfile, no node management.
- **ECS Express Mode** — image → public HTTPS URL + autoscaling; AWS's replacement for App Runner.
- **Lambda** — event-driven, bursty, <15 min; API via API Gateway or a Lambda URL.
- **Amplify** — frontend/full-stack JS (Gen 2 = TypeScript `defineBackend` / `npx ampx`).
- **App Runner** — closed to new customers since 2026-04-30; do not use for new projects.

## Commands
- ECR push: `aws ecr get-login-password | docker login --username AWS --password-stdin <acct>.dkr.ecr.<region>.amazonaws.com`
- ECS deploy: `aws ecs register-task-definition …` then `aws ecs update-service --cluster C --service S --force-new-deployment`
- Lambda (SAM): `sam build && sam deploy --guided` (`template.yaml`, `samconfig.toml`)
- Runtimes: pin a supported one (`nodejs22.x`, `python3.13`). After deprecation, create/update is blocked; invocations keep working.

## Two roles — the #1 ECS gotcha
- **Execution role**: pulls the image and secrets at launch — needs `ecr:GetAuthorizationToken`, `secretsmanager:GetSecretValue`.
- **Task role**: the app's own runtime AWS calls. Don't confuse them.

## Top errors
1. Task stops at once / `CannotPullContainerError` → wrong tag, ECR auth, or a private subnet with no NAT/VPC endpoint. Read the "stopped reason".
2. `ResourceInitializationError: unable to pull secrets or registry auth` → execution role missing the permissions above.
3. Service never stabilizes / target unhealthy → ALB health path/port ≠ container port, or health path doesn't return 200.
4. Lambda `AccessDenied` → execution role missing the action, or Logs needs `logs:CreateLogGroup`/`PutLogEvents`.
5. CFN/SAM `ROLLBACK_COMPLETE` → stack stuck; delete before recreate, and read the FIRST failure event, not the rollback cascade.

IaC on AWS: CDK/SAM/CloudFormation (native, state in CloudFormation) if AWS-only; Terraform/OpenTofu if multi-cloud. See `iac.md`.
