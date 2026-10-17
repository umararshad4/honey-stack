# Infrastructure as code

## Pick
- **Terraform** — industry standard, huge provider ecosystem. License is BSL 1.1 since v1.6. Pick for an existing TF estate or HCP Terraform.
- **OpenTofu** — MPL-2.0 fork (Linux Foundation). Drop-in `tofu` for most configs; exclusive: native state encryption, `for_each` on providers, `-exclude`. Pick for the OSS license or those features.
- **Pulumi** — real languages (TS/Python/Go/C#); pick when teams want programming constructs and tests over HCL.
- **CDK** — AWS-only, synthesizes CloudFormation; pick for AWS-native shops.

## State
Remote state with locking: S3 (native lockfile now), GCS, Azure Blob, or HCP/Scalr. One state per environment. **Never commit `terraform.tfstate`** — it holds secrets.

## Plan/apply safety
Always `plan`/`preview` and read it. **Confirm before applying a plan that destroys or replaces** anything. Save and apply the reviewed plan: `tofu plan -out=plan.tfplan` then `tofu apply plan.tfplan`; `cdk diff`, `pulumi preview`. Never `-auto-approve` in prod; use `-target` sparingly.
