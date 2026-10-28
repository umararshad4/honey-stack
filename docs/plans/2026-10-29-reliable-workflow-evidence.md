# Reliable workflow evidence plan

**Goal:** Make installed hook behavior observable, completion and feedback task-aware, and RSI improvements measurable before applying them.
**Approach:** HOLD scope. Extend the existing dispatcher, session state, doctor and RSI evaluator. A documentation-only change would leave the reproduced adapter and attribution gaps open; a second agent runtime would duplicate the host. Use stdlib modules and deterministic checks, with paid behavioral evaluation remaining explicitly budgeted.
**Design:** The six improvements accepted in the conversation on 2026-10-29. The user authorized implementation, push and merge.

## Constraints
- Preserve existing user modes, privacy, pause switches, budget limits and native permission boundaries.
- Do not execute tool payloads while normalizing them. Opaque wrappers must be reported as unverified, never represented as inspected.
- Task intent is advisory context, not an authorization bypass. Explicit inspection stays read-only until the user changes the scope.
- Completion evidence must follow the latest relevant mutation; unknown tool outcomes are not successful checks.
- Ambiguous feedback must not penalize all recent skills or trigger automatic patches.
- Independently maintained behavioral cases cannot be changed by the generated skill patch they judge.
- Preserve unrelated work; no paid provider evaluations or production changes are necessary for local tests.

## Existing pieces
Reuse `dispatch.py`, `receipt.py`, `doctor.py`, `rsi/observe.py`, `rsi/signals.py`, `rsi/patch.py` and the isolated stdlib test runner. Existing before/after patch evaluation, budgets, runtime snapshots and fail-closed apply checks remain in place.

## File map and parallel lanes
| Lane | Files / responsibility | Dependency |
| --- | --- | --- |
| Adapter and health | create `honey/tool_events.py`, `honey/health.py`; modify `honey/doctor.py`; focused tests | root wires dispatcher |
| Feedback and efficiency | `honey/rsi/observe.py`, `honey/rsi/signals.py`, `honey/rsi/curate.py`, `honey/rsi/coach.py`; create `honey/metrics.py`; focused tests | shared normalized event contract |
| Behavioral evaluation | `honey/rsi/patch.py`, maintained `evals` cases, behavioral evaluator module and tests | existing patch pipeline |
| Task and completion | root owns `honey/tasks.py`, `honey/receipt.py`, `honey/dispatch.py`, `honey/cli.py`, bootstrap, skills and docs | integrate all lanes |

## Shared interfaces
- `tool_events.normalize(payload)` returns `tool`, `kind`, `command`, `path`, `skill`, `supported`, `exit_code`, `duration_ms`, `call_id`, `cwd`. Kinds: shell/read/edit/skill/other/opaque. Unknown results remain null.
- `health.record(ctx)` records bounded delivery metadata in session state; `health.report(agent, session_id)` reads it. Root invokes recording for every received hook.
- Session `task` is a bounded object with `id`, `mode`, `request`, `operation`, `targets`, `approved_actions`, `checks`, and mutation/evidence state. Observations attach its `id` when present; absent IDs retain backwards compatibility without claiming certainty.
- Metrics collect normalized tool events once per completed call and report bounded task/session counters. No raw command or output is retained beyond existing redacted records.

## Tasks and proof
- [x] Normalize actual shell/read/edit payloads and expose installed/enabled/delivery/coverage status. Prove direct `exec_command/cmd`, legacy shell, malformed and opaque wrapper cases, missing/stale sessions and both agents with isolated tests.
- [x] Add explicit task contracts and fresh completion evidence. Prove inspect/execute transitions, continuation retaining scope, code and uninstall check requirements, failed/unknown/stale results, and no new permission bypass.
- [x] Attribute feedback to one relevant task/skill or record uncertainty; distinguish requirement, preference, environment and behavior feedback. Prove unrelated recent skills are not blamed. Measure repeated reads/checks, failures and durations without suppressing necessary tools.
- [x] Add maintained behavioral cases to before/after RSI evaluation and preserve cross-skill coverage and evaluator budgets. Prove missing cases, tampered cases and behavior failures block application.
- [x] Update bootstrap and relevant skills so strict coding checks do not impose TDD on read-only work; document commands, limits and measurement meaning.
- [x] Independently review each lane, run all tests, release consistency and diff checks.

## Review focus and failure modes
- Missing hook events: report inactive/unknown; installation is not proof of enforcement.
- Wrapper code or malformed response: never evaluate code or fabricate an exit status.
- Concurrent session updates: keep new state bounded and document existing last-writer-wins limitation; do not claim event completeness.
- New task / mutation: old evidence and permissions must not silently authorize or verify it.
- Feedback ambiguity / evaluator failure: retain uncertainty and fail closed for automatic skill application.
- Metrics: repeated reads are opportunities, not proof of waste; observation is not a speedup measurement.

## Not in scope
Changing the T3 host's hook delivery, a new background daemon, automatic deletion of user files, general-purpose JavaScript parsing, or claiming paid model behavior was tested without running it. These limits do not prevent implementing and testing the plugin-side interfaces.

## Verification and delivery
- All 29 isolated test scripts passed on Python 3.14.7. The new regressions were observed failing before their fixes.
- All four independent review lanes approved after fixes: adapter/health, task/evidence, feedback/metrics, and behavioral evaluation.
- Release consistency and whitespace checks passed. `claude plugin validate .` passed with an existing missing-listing-icon warning.
- Offline fixtures and evaluator boundaries were tested; no paid model evaluation or live host-enforcement claim was made.
- Delivery: commit the independent adapter layer and the dependent integration layer; push and merge through a PR after remote checks. The PR and completion report record delivery state.

## Rulings
- Preserve the host as the runtime. Opaque JavaScript needs inner events; a local heartbeat cannot prove host enforcement.
- Keep the maintained evaluator explicitly Claude-only until another runner has real execution proof. Preserve existing evaluation budgets.
- An explicit task contract may bind the actual project directory when the host starts in scratch. It records evidence requirements and never grants permission.
- Keep unknown feedback and unobserved outcomes visible rather than converting them into failures or success.
- Add test-helper isolation after a legacy discovery invocation reached local RSI state. Its synthetic proposal was archived and affected retry metadata restored; direct helper imports now use throwaway state and a fake provider.
