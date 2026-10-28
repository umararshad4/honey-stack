# Continuous RSI plan

**Goal:** Keep learning and applying validated Honey improvements during normal use, without repeated approval.
**Approach:** REDUCTION. Repair the existing observation → proposal → evaluation → application loop. Reuse detached session jobs, the ledger, existing patch worktrees, budgets and sync. No new daemon or unrestricted code-writing agent.
**Design:** Request and existing autonomous-RSI contract settle the product decisions. Automatic does not mean unconditional.

## Constraints
- The user authorized committing this implementation, pushing a feature branch and opening a PR on 2026-10-29. Merging and releases remain outside scope. Existing autonomous local evaluated patch commits remain permitted by the installed RSI contract.
- Preserve user edits, pause controls, rejected rules, evidence thresholds and budget ceilings.
- Never execute proposal prose. Only structured, bounded skill drafts/patches can enter evaluation; unsupported runtime/config diagnoses remain visible.
- One paid improvement attempt per daily session-driven pass; retry failed work after cooldown, rotate fairly, keep applying already validated proposals each session.
- Apply only complete passing evaluations, retain false-trigger coverage, and distinguish evaluator errors from behavior regressions.

## Existing pieces and alternatives
Existing reflection, curation, patch evaluation and apply/sync are reused. Merely running weekly more often leaves the evidence and evaluator bugs intact. An unrestricted autonomous coding daemon is unnecessary and harder to validate; repair the current pipeline instead.

## File map
- `honey/rsi/observe.py`, `curate.py`: provenance-aware evidence and durable feedback links.
- `honey/rsi/patch.py`: evaluator-compatible cases, complete results, bounded generation and fair retry.
- `honey/rsi/improve.py` (create): daily preparation of actionable skill diagnoses and new-skill requests, parent/child lifecycle.
- `honey/rsi/autonomy.py`, `reflect.py`, `cli.py`, `weekly.py`: recurring integration and observable results.
- `honey/rsi/coach.py`: genuine-user request evidence for new-skill proposals, excluding orchestration noise.
- `tests/test_rsi_evidence.py`, `tests/test_rsi_continuous.py`, existing apply tests: red/green proof.
- `README.md`, `skills/rsi/SKILL.md`: precise cadence, limits and controls.

## Review focus
Untrusted tool text must not promote rules; existing quarantined records must be revalidated against original user events. Evaluator parse errors must not look like behavior failures. No repeated paid calls on each hook, no starved candidates, no application before child validation, no overwriting concurrent source edits.

## Tasks
1. Reproduce and fix provenance/feedback loss. Tests cover tool-heavy genuine user sessions, injected/untrusted evidence, existing records and retained misfire quotes. Verify `python3 tests/test_rsi_evidence.py`.
2. Reproduce invalid regex grading and incomplete eval acceptance; fix case serialization and fail closed on missing/error results. Verify focused evaluator tests.
3. Add session-driven daily improvement with cooldown/fairness and source-backed parent/child drafting. Test disabled, paused, budget, malformed/noisy requests, failed draft, failed eval, child application and repeated calls. Preserve the weekly audit/radar.
4. Run full `python3 tests/run.py`, `python3 scripts/release.py --check`, `git diff --check`; independent review and corrections. Sync local installation, verify installed-runtime behavior with disposable data and inspect real state without claiming synthetic proof is live outcome improvement.

## Failure modes
- No evidence: retain explicit reason, do not spend on unsupported fixes.
- Invalid draft/evaluator/provider error: record and retry after cooldown, never mark applied.
- Budget cap: defer, keep local deterministic curation/application working.
- Busy lock: next session retries; no duplicate worker.
- Dirty target/diverged branch: preserve source and report conflict; unrelated edits must survive.
- Failed sync: preserve existing recoverable `sync_pending` state.

## Not in scope
Arbitrary runtime Python repairs from prose, new background service, broader spending limits, merging or releasing, or claiming improvement without observed outcomes.

## Verification and local activation

- Evidence fixes passed red/green tests, including legacy provenance recovery and real hook-to-coach ordinary requests. Raw request keywords now derive from redacted text.
- Drafting/evaluation checks cover valid JavaScript regexes, incomplete/error results, new-skill positive/negative cases, cleanup, target validation and conservative cost reservations on failed paid calls.
- Daily queue checks cover diagnosis/new-skill/upstream preparation, cooldown, fairness, blocked-patch isolation, pending-sync recovery and manual-mode preservation.
- Independent reviewer approved after fixing upstream cadence, failed-call accounting and evaluation/install runtime parity.
- Full test runner: all 20 test scripts passed on Python 3.14.7. Release consistency and diff checks passed.
- `honey sync` refreshed Codex's local cache; all 202 runtime files matched source. Disposable installed-CLI smoke proved automatic instruction application and idempotency.
- Live `honey rsi improve --json` activated five previously stuck rules; six rules are now active. Repeating the command activated zero more and respected cooldown.
- No paid live draft/evaluation ran: the recorded weekly spend leaves less than the $0.85 reserved for drafting plus both evaluations. The existing $1.50/week and $5/month caps were preserved.
- Legacy keyword-only new-skill suggestions remain blocked for missing source-backed requests. Unsupported runtime diagnoses remain visible. Learned instructions load in a new session; the session brief retains its existing 1,500-character cap.
- Local RSI state was backed up before activation. The implementation is delivered as a feature-branch PR; it does not merge or publish a release.
- Shortcut: generated new-skill evaluation covers its own positive/negative cases, not every other skill. Broaden the behavioral suite when cross-skill interference is observed and the evaluation budget permits.
- Snapshot overlays with unrelated local runtime edits may leave a dirty evaluation worktree after successful application; it is retained rather than deleting possible user edits.
