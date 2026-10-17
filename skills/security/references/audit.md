# Security audit

Read for a full audit, threat model or pre-launch review. Condensed from garrytan/gstack 1.60.1.0 `cso/SKILL.md.tmpl` and `cso/sections/audit-phases.md` (MIT).

An audit is read-only. It produces findings and recommendations, and changes code only after the user picks which fixes to apply. Real attack surface is often outside the app code: CI logs, git history, dependencies, forgotten configs. Start there.

Scope to what the user named (a domain such as auth, infra only, the branch diff). With `--diff`-style scope, limit each phase to files and commits on the current branch. Send independent phases to subagents and keep their findings here.

## 0. Mental model

Detect the stack from the manifests (`package.json`, `pyproject.toml`, `go.mod`, `Gemfile`, `Cargo.toml`, `pom.xml`) and the framework. Read the README and key config. Write a short summary: components, how they connect, where user input enters and leaves, and what trust boundaries sit between them. Stack detection sets priority, not scope: still run a quick catch-all pass for SQL injection, command injection, hardcoded secrets and SSRF across every language present.

## 1. Attack surface census

Count, from the code and config:

```
CODE: public endpoints, authenticated, admin-only, machine-to-machine APIs,
      file uploads, external integrations, background jobs, websocket channels
INFRA: CI workflows, webhook receivers, container configs, IaC files,
       deploy targets, secret management (env | KMS | vault | unknown)
```

## 2. Secrets archaeology

```bash
git log -p --all -G 'AKIA[0-9A-Z]{16}|sk_live_|sk-ant-|ghp_|gho_|github_pat_|xox[abp]-|-----BEGIN [A-Z ]*PRIVATE KEY-----'
git ls-files | grep -E '(^|/)\.env(\.|$)' | grep -vE '\.(example|sample|template)$'
grep -nE '(password|token|secret|api_key):' .github/workflows/*.y*ml | grep -v '\${{'
```

Critical: live key formats anywhere in history. High: a tracked `.env`, inline credentials in CI. Placeholders (`your_`, `changeme`) and test fixtures not used by real code are noise. A secret that was later removed still counts: it was exposed.

## 3. Dependencies and supply chain

- Run the ecosystem's audit tool when installed: `npm audit` / `pnpm audit` / `yarn npm audit`, `pip-audit`, `bundle audit`, `cargo audit`, `govulncheck`. A missing tool is a skipped check, not a finding.
- Production dependencies with `preinstall`, `install` or `postinstall` scripts.
- The lockfile exists and is tracked (for apps; libraries may omit it).
- For each CVE, check whether the vulnerable function is actually imported or called. Called: verified. Not called: unverified, with that reason.

## 4. CI/CD

- Third-party actions not pinned to a commit SHA.
- `pull_request_target` that checks out the PR head: critical, since fork code runs with secrets.
- Script injection: `${{ github.event.* }}` interpolated into `run:` steps.
- Secrets exposed through `env:` at job or workflow level, or echoed in logs.
- Workflow files without CODEOWNERS protection.

## 5. Infrastructure

- Dockerfiles: no `USER` (runs as root), secrets passed as `ARG`, `.env` copied into the image.
- Committed connection strings with credentials that point beyond localhost; staging configs that reach the production database.
- IaC: `"*"` in IAM actions or resources, secrets in `.tf` or `.tfvars`. Kubernetes: `privileged`, `hostNetwork`, `hostPID`.
- Local-dev compose files on localhost are not findings.

## 6. Webhooks and integrations

- Webhook routes with no signature verification anywhere in their middleware chain. Trace the code; send no live requests.
- TLS verification disabled outside tests (`verify=False`, `InsecureSkipVerify`, `NODE_TLS_REJECT_UNAUTHORIZED=0`).
- OAuth scopes broader than the feature needs.

## 7. LLM and AI features

- User input reaching system prompts or tool schemas. (User text in the user-message position is not prompt injection.)
- Model output rendered as HTML or passed to `eval`, `exec` or `Function`.
- Tool or function calls executed without validation; RAG sources that outsiders can write to.
- Provider keys in code; unbounded calls a user can trigger (cost amplification counts as a finding).

## 8. Agent and skill supply chain

Scan repo-local agent config (`.claude/`, `.codex/`, `AGENTS.md`, skill folders, hooks) for exfiltration (`curl`, `wget` with credential variables), credential reads (`process.env`, API key names) and prompt-injection text. Scan global skills or user settings only with the user's permission, since that reads outside the repo.

## 9. OWASP Top 10

The categories below use the 2021 numbering. The 2025 edition folds SSRF into access control and adds software supply chain failures and mishandling of exceptional conditions; phases 3 and 4 cover the supply chain.

- **A01 Broken access control.** Routes missing auth; object ids taken from the request without an ownership check (can user A read user B's record by changing the id?); horizontal and vertical escalation.
- **A02 Cryptographic failures.** MD5, SHA-1, DES or ECB for security purposes; plaintext sensitive data at rest or in transit; hardcoded keys.
- **A03 Injection.** SQL built by string interpolation, shell calls with user input, template injection, `eval`.
- **A04 Insecure design.** No rate limit or lockout on auth endpoints; business rules enforced only on the client.
- **A05 Misconfiguration.** Wildcard CORS in production, missing CSP, debug mode or verbose errors in production.
- **A06 Vulnerable components.** Phase 3.
- **A07 Authentication failures.** Session creation, storage and invalidation; password policy and breach checks; MFA for admins; JWT expiry and refresh rotation.
- **A08 Integrity failures.** Phase 4, plus unvalidated deserialization and unsigned external data.
- **A09 Logging failures.** Auth events, authorization failures and admin actions are logged, and logs can't be tampered with.
- **A10 SSRF.** URLs built from user input; reachability of internal services; outbound allowlists.

## 10. STRIDE per component

For each major component from phase 0, answer: Spoofing (can someone impersonate a user or service?), Tampering (can data change in transit or at rest?), Repudiation (is there an audit trail?), Information disclosure (what can leak?), Denial of service (what's easy to overwhelm?), Elevation of privilege (how could a user gain access they shouldn't have?).

## 11. Data classification

List what the app holds and where: restricted (credentials, payment data, PII), confidential (API keys, business logic, behavioral data), internal (logs, config visible in errors), public.

## 12. Filter before reporting

**Confidence gate.** Default: report only findings at 8/10 confidence or higher (a clear pattern with a known exploit). When the user asks for a comprehensive pass, lower the bar to 2/10 and mark those findings `TENTATIVE`.

**Discard:** generic DoS or resource exhaustion (LLM cost amplification is the exception), missing hardening with no concrete vulnerability, outdated libraries (phase 3 owns them), memory safety in memory-safe languages, test-only files, log spoofing, path-only SSRF, ReDoS on input that isn't user-controlled, missing audit logs, non-security randomness, CVEs under CVSS 4.0 with no known exploit, and findings in archived workflows or local-dev Dockerfiles.

**Precedents:** logging a secret is a finding; logging a URL is not. UUIDs are unguessable. Env vars and CLI flags are trusted input. React and Angular escape by default, so only their escape hatches count. Client-side code doesn't need auth checks; the server does. `pull_request_target` without a PR-head checkout is safe.

**Verify without attacking.** Trace code paths, check key formats by length and prefix, and parse workflow YAML. Never call live APIs, endpoints or webhooks with test payloads. Mark each finding `VERIFIED` (confirmed by tracing), `UNVERIFIED` (pattern match only) or `TENTATIVE`.

**Independent check.** Give each surviving finding to a fresh subagent with only the `file:line` and the rules above, and ask for a 1-10 score. Drop findings it scores under the gate. Without subagents, re-read each one as a skeptic and say it was self-verified.

**Variants.** For each verified finding, grep the codebase for the same pattern and report variants as their own findings.

## 13. Findings

Summary table first:

```
#  Sev   Conf  Status      Category      Finding                         File:Line
1  CRIT  9/10  VERIFIED    Secrets       AWS key in git history          .env:3
2  HIGH  8/10  UNVERIFIED  Integrations  Webhook without signature check api/webhooks.ts:24
```

Then each finding:

```
## Finding N: <title> (<file:line>)
Severity: CRITICAL | HIGH | MEDIUM · Confidence: N/10 · Status: VERIFIED | UNVERIFIED | TENTATIVE
Category: Secrets | Supply chain | CI/CD | Infrastructure | Integrations | LLM | Agent config | OWASP A01-A10
Description: what is wrong.
Exploit scenario: the step-by-step path an attacker follows.
Impact: what the attacker gains.
Recommendation: the specific fix, with an example.
```

Critical needs a realistic exploit path. Three real findings beat three real plus twelve theoretical: people stop reading noisy reports.

**Leaked secret playbook:** revoke the credential, issue a new one, scrub history (`git filter-repo` or BFG) and force-push only with the user's go-ahead, work out the exposure window (when committed, when removed, whether the repo was public), and check the provider's logs for abuse.

**Prevention.** If the repo has no secret-scan config (`.gitleaks.toml`, `.secretlintrc`), recommend one.

**Next step.** For the top findings, give one decision brief per finding with these options: fix now, mitigate, accept the risk with a review date, or add it to the TODO list.

Report in chat. Write a report file only when asked, and keep it out of git.

End every audit with: this is an AI-assisted scan for common vulnerability patterns. It isn't comprehensive and doesn't replace a professional penetration test for systems that handle payments, PII or other sensitive data.
