# RSI runtime recovery

**Goal:** Restore authorized Honey hook execution and keep automatic improvements observable and retryable within the existing budget.
**Approach:** HOLD scope. Reuse Codex's hook registry and trust API, Honey's existing background jobs, and the existing evaluated patch pipeline.
**Design:** User requested resolving the hook and budget blockers, then explicitly requested removing budget caps. Disable dollar caps for this installation while preserving the daily cadence, evaluation and source-validation rules.

## Constraints
- Restore approval only for the reviewed installed Honey bundle; never automatically trust future changed code.
- Keep evidence validation, before/after evaluation, user pause controls, and rate limits. Dollar caps remain the default for other installations.
- Do not fabricate an applied improvement or a live hook event for verification.
- Preserve concurrent work and test only with isolated RSI state.

## What already exists
- Codex `hooks/list` reports current bundle trust; `config/batchWrite` records explicit approvals.
- `honey doctor` observes actual session delivery but incorrectly counts saved approvals as current trust.
- `rsi improve` prepares and applies evaluated changes, but consumes its daily attempt before a budget refusal.

## File map
- `honey/codex_hooks.py`: bounded, read-only Codex registry inspection.
- `honey/doctor.py`: expose actual trust alongside delivery.
- `honey/rsi/improve.py`: distinguish budget deferral from a generation attempt.
- `honey/rsi/reflect.py`, `honey/rsi/patch.py`, `honey/rsi/cli.py`: explicit uncapped-dollar mode, retaining usage accounting and cadence.
- `tests/test_codex_hooks.py`, `tests/test_health.py`, `tests/test_rsi_continuous.py`: regression coverage.
- `README.md`: describe trust renewal and automatic budget retries accurately.

## Task 1: Restore the runtime and repair diagnostics/retries
- [x] Back up previous approvals and restore the nine explicitly authorized Honey hooks through Codex's normal config API.
- [x] Red/green: explicit dollar-cap disablement removes weekly, monthly and per-call dollar limits, while preserving rate limits and usage accounting.
- [x] Red/green: budget refusal must not call the generator or consume the daily attempt; recovery within 24 hours can run once.
- [x] Red/green: saved legacy approvals cannot make modified hooks look trusted; registry failure is unknown, not success.
- [x] Verify isolated targeted tests, full suite, Python 3.9 compatibility, release consistency, and whitespace.
- [x] Independent review and installation parity check.
- [x] Verify registry trust and actual live delivery separately; run a real due improvement only within the user's budget.

## Failure modes and review focus
| Failure | Handling and proof |
| --- | --- |
| Registry unavailable or malformed | Report unknown; never claim trusted or hang indefinitely. |
| Plugin code changes after approval | Report modified; no background approval bypass. |
| Budget unavailable | Record deferral without starting the daily attempt. |
| Provider fails after an actual attempt | Preserve the existing cooldown and reserved usage. |
| Current T3 session retains old config | Report separately and require host refresh; do not fake delivery. |

## Not in scope
- Rewriting the T3 host or removing Codex trust protection.
- Applying vague or unverified queued proposals just to empty the queue.
- Publishing or merging without authorization.

## Verification and limits
- All 31 isolated test scripts passed on Python 3.14.7; targeted budget, queue and registry tests also passed on Python 3.9.
- Independent review approved the hook completeness and unknown-cost fixes.
- Nine current Honey hooks were explicitly reviewed and trusted through Codex's config API. No future automatic approval mechanism was added.
- Installed Codex source parity was checked across 401 files.
- A fresh native Codex session using isolated RSI state delivered SessionStart, UserPromptSubmit, Stop and SessionEnd; its real detached job recorded a completed improvement check. No synthetic event was injected into the user's learning history.
- The real user-state improvement command ran without budget deferral. It applied no patch because none of the retained proposals had sufficient verified evidence or a supported repair.
- The existing T3 session still has no hook delivery; a fresh T3 session is required to load the restored approvals.
- Dollar caps are explicitly disabled in the user's local config; daily cadence and validation remain active.
- This verification record describes the locally installed change. Local budget settings and hook approvals are not distributed by the source commit.
