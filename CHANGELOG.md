# Changelog

All notable changes to honey-stack. The format follows [Keep a Changelog](https://keepachangelog.com/en/1.1.0/) and the project uses [Semantic Versioning](https://semver.org/):

- **MAJOR**: breaking changes to hook commands (Codex would need to re-trust), the `~/.honey` data layout, or the CLI
- **MINOR**: new skills or RSI capabilities
- **PATCH**: fixes

Releases are cut with `python3 scripts/release.py X.Y.Z --push`. GitHub Actions then publishes the release from this file.

## [Unreleased]

### Added
- **Animation guidance** in the `frontend` skill (`references/animation.md`, distilled from Emil Kowalski's design-engineering skills, MIT): animate by action frequency, `ease-out`/never `ease-in` for UI, sub-300ms durations, `transform`/`opacity`-only performance rules, entry/popover/stagger/spring patterns, and a review checklist. The inline motion rule now carries the headline law.
- **End-to-end test guidance** in the `qa` skill (`references/e2e.md`, distilled from the e2e framework docs): split steps into deterministic (`expect`) vs agent-driven, select by role→name→test id, verify locators before asserting, cache only verified steps, explore→pin as regression tests with a repro per finding, and secret/flaky/CI handling.

## [0.8.0] - 2026-10-18

### Added
- **Quality evals** (`evals/quality-*`, run with `--ablation with-without`) that grade skill *output* against a no-plugin baseline, not just whether a skill fires. A pressure case proved real uplift: under "just confirm it's fine, I'm in a hurry" on refund logic, honey-stack holds the line (1.0) where the base model signs off from a read alone (0.0).
- **Hard skill-listing budget gate** (`tests/test_budget.py`, enforced in CI): fails if model-invoked descriptions exceed the total budget or any skill's description would be truncated. Adding a skill can no longer silently break the listing.
- **Freshness tracking**: every skill carries a `reviewed:` date; `tests/test_freshness.py` requires it and `honey doctor` warns when a skill's version-specific facts are over a year old.
- **One-line installer** (`install.sh`): `curl … | bash` clones/updates the repo and shows a dry run before you approve the apply.
- **`honey install --skill-budget <fraction>`**: reversibly raises Claude's `skillListingBudgetFraction` for more skill-description room alongside other installed skills.
- **Router disambiguation**: `honey` now spells out which skill wins when two overlap (debug vs incident, perf vs database, tdd vs test-design vs qa, review vs verify, ship vs deploy, security vs upgrade, docs vs unslop).

### Changed
- Strengthened the always-on proof law: never sign off that a change is fine or safe to ship from a read alone, and hold that on money/auth/data paths even under time pressure.
- Tightened several model-invoked skill descriptions to stay within the listing budget.

### Known
- On strong base models, the other quality cases (debug plan, edge-case listing, API error contract, done-discipline) score 1.0 both with and without honey — these are consistency/preference skills, not capability uplift there. The evals stay as a regression floor.

## [0.7.0] - 2026-10-18

### Added
Six production-engineering skills, each with current (2026) reference files, decision rules, and confirmation gates for risky actions:
- **`database`** — schema design, safe/online (expand-contract) migrations, indexing, slow-query and N+1 fixes, transactions and isolation levels. Postgres-first. Confirms before any production migration.
- **`perf`** — profile-first performance work (per-stack profilers, USE/RED), hot-path fixes, caching layers and invalidation, and load testing with p50/p95/p99. Confirms before load-testing anything live.
- **`observability`** — structured logging, metrics (RED/USE, cardinality traps), distributed tracing, error tracking, SLOs and burn-rate alerting, OpenTelemetry-first.
- **`api-design`** — REST/GraphQL/gRPC/tRPC choice, resource modeling, RFC 9457 error contracts, cursor pagination, idempotency keys, versioning without breaking, schema-first OpenAPI/proto/GraphQL.
- **`upgrade`** — safe dependency upgrades (one major per PR, gated by tests), CVE triage with reachability (osv-scanner, govulncheck), forcing patched transitive deps, framework codemods, runtime EOL, lockfile hygiene.
- **`incident`** — production outage response: severity, mitigate-first (rollback/flag/scale), safe live investigation with the four golden signals, communication, and a blameless postmortem. The agent recommends but never executes a prod mitigation without human approval.

## [0.6.0] - 2026-10-18

### Added
- **`deploy` skill** — platform-aware deploys and infrastructure: AWS (ECS/Lambda), GCP Cloud Run, Azure Container Apps, Vercel/Netlify/Fly/Railway/Render/Cloudflare, plus Docker, Kubernetes/Helm, Terraform/OpenTofu/Pulumi/CDK, and GitHub Actions OIDC CI/CD. Reference files per platform with the top real errors and fixes, a production/destructive-op confirmation gate, and a failed-deploy diagnosis loop.
- **`test-design` skill** — derives the full test matrix and hard edge cases for a feature (equivalence/boundary/decision-table/state/pairwise, data-type and systemic edge-case checklists, property-based tests, mutation-testing as the real coverage signal, level/double choices), then hands concrete cases to `tdd`.
- **`tooling` skill** — monorepo (Turborepo/Nx/pnpm workspaces + Changesets), micro-frontends (Module Federation 2), microservices + Pact contracts, pre-commit hooks (Husky v9/Lefthook/pre-commit), lint/format/typecheck (Biome 2, ESLint 10 flat config, Ruff), test wiring (Vitest 3) and a GitHub Actions pipeline, each with current configs and honest "is this overkill?" guidance.

## [0.5.0] - 2026-10-18

### Added
- `reverse` skill (`/honey:reverse`, `$reverse`): drives the [REA](https://github.com/morluto/rea) toolchain to reverse-engineer a shipped target (binary, APK, JS/Electron, .NET, website, firmware, network capture) without its source, with an authorized-use gate and evidence discipline. REA is a separate MCP server the skill installs on approval; honey-stack doesn't bundle it.

## [0.4.0] - 2026-10-18

### Added
- `unslop` skill (`/honey:unslop` in Claude, `$unslop` in Codex), adapted from pstack. It removes AI tells and filler from any text you pass it: messages, posts, prompts or docs. The `docs` skill now uses it as the single source of its writing rules.

## [0.3.1] - 2026-10-18

### Added
- `honey update`: pulls the latest release into your checkout and refreshes Codex's copy.

## [0.3.0] - 2026-10-18

### Added
- **Reply indicator.** Every reply starts with `🍯 HONEY`, plus any non-default mode (e.g. `🍯 HONEY · ultra · strict`), so you can see at a glance that honey-stack is on. `honey off` hides it.

### Fixed
- The `review` skill now fires reliably on short pasted diffs: the bootstrap routes "review code/diff/PR" requests to the skill instead of an inline opinion (trigger eval 3/3, up from 2/3).
- Verified the Codex agent role format against Codex 0.163: all 4 `honey-*` agents are discovered.

## [0.2.0] - 2026-10-17

### Added
- `honey --version`.
- Release tooling: `scripts/release.py` (bumps every version field, rolls the changelog, tests, tags), CI on macOS and Linux with Python 3.9 and 3.12, and GitHub releases published automatically from tags.
- Install straight from GitHub on both agents: `claude plugin marketplace add umararshad4/honey-stack` and `codex plugin marketplace add umararshad4/honey-stack`.

### Changed
- `honey install` now leaves your `CLAUDE.md` / `AGENTS.md` and your other skills alone by default. Overwriting the instruction files (`--slim-instructions`) and retiring absorbed MCT / Matt Pocock duplicates (`--retire-legacy`) are opt-in.
- Rewrote the README as a public quick-start.

## [0.1.0] - 2026-10-17

### Added
- An always-on bootstrap for Claude Code and Codex: task sizing, the smallest-complete-change ladder, proof before done, decisions over questions. Three mode axes (`honey ultra|lite|full`, `strict|light`, `terse|normal`) plus `honey off`.
- 22 skills distilled from Superpowers, Ponytail, Matt Pocock's skills, pstack and gstack, plus 4 subagents (also rendered for Codex).
- Safety hooks: a destructive-command guard, a scan for secrets in newly written text, and a receipt gate that only fires after turns that edited files.
- The RSI engine:
  - an observer with harness-origin filtering and an event log shared by both agents
  - `remember:` notes
  - a detached reflector with budget caps
  - a deterministic curator: promotion after 2 sessions, decay, budgets
  - `/rsi review` (Tier 1 instruction edits, Tier 2 eval-gated skill patches on branches, Tier 3 learned guards)
  - `/rsi coach`, `/rsi bootstrap`, the upstream radar, a golden suite and holdout sessions
- `honey install | uninstall | doctor | sync`: dry-run first, recorded in a manifest, fully reversible.

[Unreleased]: https://github.com/umararshad4/honey-stack/compare/v0.8.0...HEAD
[0.8.0]: https://github.com/umararshad4/honey-stack/compare/v0.7.0...v0.8.0
[0.7.0]: https://github.com/umararshad4/honey-stack/compare/v0.6.0...v0.7.0
[0.6.0]: https://github.com/umararshad4/honey-stack/compare/v0.5.0...v0.6.0
[0.5.0]: https://github.com/umararshad4/honey-stack/compare/v0.4.0...v0.5.0
[0.4.0]: https://github.com/umararshad4/honey-stack/compare/v0.3.1...v0.4.0
[0.3.1]: https://github.com/umararshad4/honey-stack/compare/v0.3.0...v0.3.1
[0.3.0]: https://github.com/umararshad4/honey-stack/compare/v0.2.0...v0.3.0
[0.2.0]: https://github.com/umararshad4/honey-stack/compare/v0.1.0...v0.2.0
[0.1.0]: https://github.com/umararshad4/honey-stack/releases/tag/v0.1.0
