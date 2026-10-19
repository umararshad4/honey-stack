# Autonomous RSI plan

**Goal:** Let RSI learn, validate, apply and report improvements across all existing tiers without per-change approval.
**Approach:** HOLD. Reuse the proposal queue and existing apply functions; add one shared autonomous application dispatcher. Enable autonomy for this user's installation after tests, while preserving review mode for other installations.
**Design:** This document; user approved implementation on 2026-10-18.

## Decisions and constraints

- User requested fully autonomous RSI, including instruction edits, skill patches and guards.
- Store `rsi.autonomous` in existing `~/.honey/config.json`; absent means false. Add `honey rsi autonomy on|off|status`.
- Autonomy bypasses human review, not evidence checks, budgets, never-list exclusions or mode/user-instruction precedence.
- Reuse existing session-end and weekly scheduling. Do not run expensive generation on prompt/tool hooks.
- Drain eligible pending proposals after reflection and weekly generation. Process a bounded snapshot, with generated child proposals handled on the next pass.
- Do not automatically activate bootstrap-only proposed learnings without the existing evidence/promotion checks.
- Apply only structured supported operations. Never execute free-form proposal fix text as shell commands.
- LLM-only toolkit diagnoses without structured repair payload remain blocked with an explicit reason; autonomy cannot turn an unimplemented repair into an executable operation.
- Record automatic decisions separately from user decisions; do not feed them into golden user-feedback evaluation or precision counters.
- Apply deterministic toolkit repairs to the specific reported setting or link; preserve unrelated settings and installation backups. Do not run the full installer to fix one finding.
- Keep failed or blocked proposals distinguishable from applied proposals, with timestamped reasons and retryable state. One failure must not stop unrelated proposals.
- User skip/never/revert decisions remain respected; applied items must not reapply.
- Preserve local README edits. Do not commit this implementation or push, release or deploy. Once enabled, autonomous RSI may create its existing local skill-patch commits and fast-forward the local source checkout after evaluation; RSI data history also remains enabled. Neither workflow may push remotely.
- Existing code installation and active plugin paths must be inspected before local activation; do not claim a source change is live without verifying installed behavior.

## What already exists

- `honey/rsi/curate.py`: evidence-based rule promotion, never-list and brief generation.
- `honey/rsi/review.py`: persistent proposal queue and outcomes.
- `honey/rsi/cli.py:decide`: current side-effect dispatcher; extract for reuse rather than invoking CLI subprocesses.
- `honey/rsi/instructions.py`: exact-line edits, before snapshots and reverts.
- `honey/rsi/patch.py`: worktree regression evaluation, fast-forward apply and sync.
- `honey/rsi/guards.py`: replay validation and guard activation.
- `honey/rsi/store.py`: locks and atomic state writes. Avoid nesting its non-reentrant locks.
- `honey/rsi/weekly.py` and `reflect.py`: detached jobs and budget checks.

## Alternatives

- Only automate learned preferences: smallest, but already largely implemented and does not satisfy all tiers.
- Reuse the proposal pipeline with an automatic dispatcher: recommended; retains current validation and inspection commands.
- Replace RSI with a new general agent: unnecessary new execution and permission system.

## File map

- Create `honey/rsi/autonomy.py`: configuration, supported application dispatch, bounded queue draining and outcomes.
- Modify `honey/rsi/cli.py`: autonomy controls/status and shared manual application path.
- Modify `honey/rsi/weekly.py`, `reflect.py`: invoke automatic draining under a clear lock owner; refresh brief after changes.
- Modify `honey/rsi/review.py`: accurate outcome reporting and automatic-change notices instead of approval prompts in autonomous mode.
- Modify `honey/rsi/patch.py`: recheck stored eval evidence, fail honestly on sync errors, record recoverable partial application.
- Modify `honey/rsi/instructions.py`, `guards.py` only where apply-time validation, history or truthful wording requires it.
- Create `tests/test_rsi_autonomy.py`; extend existing tier tests for real side effects and failures.
- Modify `README.md`, `skills/rsi/SKILL.md` and directly affected RSI docs/comments so autonomous behavior and review mode agree.

The cross-tier surface needs more than eight files; reuse existing functions and one new orchestration module to avoid a parallel framework.

## Review focus

- A proposal must never become applied when its effect did not occur or sync failed.
- Reject invalid/stale instruction targets, absent guards, incomplete evals and unsupported operations.
- No lock recursion or duplicate side effects across concurrent jobs/repeated runs.
- Never/skip decisions and direct user instructions must survive automatic passes.
- Partial multi-file operations must retain backups and honest recovery information.

### Task 1: Autonomous instruction application and controls

**Interfaces:** `autonomy.enabled() -> bool`, `autonomy.run() -> dict`, shared `autonomy.apply(proposal) -> str`; caller owns the RSI lock.

- [x] Add a failing public CLI/job test: autonomy on plus an instruction-add proposal changes the isolated CLAUDE.md and marks that proposal applied; autonomy off leaves it pending.
- [x] Implement configuration controls and shared application path using exact existing instruction operations.
- [x] Add red/green tests for stale lines, absent/malformed proposals, invalid target/action, duplicate runs, skipped/never items and per-item failure isolation.
- [x] Keep before snapshots and test revert without overwriting subsequent unrelated edits; record conflicts instead.
- [x] Verify through `python3 tests/run.py` using isolated HONEY_HOME and agent configuration directories.

### Task 2: All existing proposal kinds

- [x] Add failing tests before each handler: verified guard activation; instruction edit/remove; evaluated skill-patch application; upstream-port child generation; deterministic toolkit repair.
- [x] Extract manual CLI dispatch into the shared handler and implement structured repairs for each existing toolkit audit finding. Never treat a prose fallback as successful application.
- [x] Test missing/invalid guard regex and replay evidence, missing/failed/regressed patch evals, dirty/diverged repo and sync failure. Leave state honest and recoverable.
- [x] Reuse budget checks for upstream child generation and bounded queue snapshots to prevent unbounded recursive work.
- [x] Link upstream proposals to their child skill patches; drafting a child is not successful application. Parent completion follows verified child application; no-hunks, budget deferral and failed eval remain explicit outcomes.
- [x] Test toolkit repairs with temporary settings and symlinks, preserving unrelated settings, refusing changed targets and verifying recorded backups.
- [x] Verify `python3 tests/run.py`.

### Task 3: Automatic jobs, reports and installation

- [x] Add failing tests that reflection/weekly jobs drain eligible changes only when configured, obey off/pause behavior, avoid concurrent duplicate application and regenerate brief after edits.
- [x] Integrate the dispatcher without nested locks; keep automatic notices informational and preserve manual review commands.
- [x] Report autonomy state and recent applied/blocked/failed changes through existing status/review commands. Record automatic versus manual decisions.
- [x] Update RSI docs and skill instructions to match both policies, preserving existing README edits.
- [x] Run `python3 tests/run.py`, `python3 scripts/release.py --check`, and `git diff --check`; request an independent reviewer subagent and resolve findings.
- [x] Inspect the local installed command/plugin paths, synchronize only required runtime assets using the existing supported installation mechanism, enable autonomy for this user, and verify command/status behavior. Report any new-session reload requirement explicitly.

## Failure modes

| Path | Failure | Handling and proof |
|---|---|---|
| Queue | Empty, malformed or unknown item | No side effect; tested blocked result |
| Instructions | Target line changed | Keep file intact; record conflict and retain backup |
| Guard | Missing record, invalid regex or failed replay | No activation; tested reason |
| Skill | Eval missing, merge conflict or sync failure | No false applied status; retain recovery info |
| Toolkit | Settings changed since audit | Recheck exact finding; preserve unrelated data |
| Job | Another process holds lock | Skip this pass; test no duplicate write |
| Upstream | Budget/provider error | Record failure; continue unrelated items |
| Revert | User edited file after application | Refuse destructive snapshot restore; report conflict |

## Not in scope

- Removing evidence thresholds, cost limits or never-list protection: these determine whether an improvement qualifies.
- Remote publishing, implementation delivery commits/releases or arbitrary project edits: autonomy is scoped to existing RSI tiers, including their local evaluated patch commits.
- A new scheduler or learning model: reuse existing session/weekly jobs.

## Approval and proof

User approved this plan. Implementation follows test-first slices and independent review. Installed runtime verification is separate from source tests.

## Rulings and verification record

- Preserved review mode by default for other installations; enabled autonomous application only for this user as approved.
- Legacy instruction snapshots used a random short hash. Automatic revert refuses those unverifiable snapshots; the original `before` text remains available for manual recovery.
- Unsupported toolkit diagnoses remain blocked rather than executing prose. This is an actionability limit, not an approval gate.
- Skill patches keep local evaluated commits but never push remotely. The implementation working tree is intentionally uncommitted, so automatic skill patch acceptance waits for a clean checkout.
- Source tests passed across all 13 test scripts on Python 3.14.7; release consistency and diff checks passed. Independent reviewer approved after fixing forgotten sources, queue fairness, malformed proposals, stale audit evidence, stable statusline launchers and revert locking.
- Installed runtime smoke caught copied Git metadata inside Codex's plugin cache. Source resolution must explicitly reject cached Git checkouts and use recorded source metadata.

- Final installed verification passed: all 11 relevant runtime/skill files match source, a disposable installed-runtime catchup applied an instruction automatically, the actual installed status reports autonomy enabled, and the installed resolver selects the source checkout despite copied Git metadata.
- Re-ran all 13 test scripts after the cache fix: all passed. The independent reviewer approved the cache-boundary correction and ran its five source tests.
- No paid live-provider evaluation was run; provider/CLI boundaries use deterministic fixtures. No implementation commits or remote pushes were made. Existing README edits were retained.
- Reused the weekly job's existing call to `reflect.run_pending()` for the automatic drain, avoiding a second queue implementation or duplicate application pass in `weekly.py`.
