# Simple response modes

**Goal:** Replace the exposed scope/process/voice axes with `direct`, `explain`, and `balance`.
**Approach:** Reuse the mode parser, session state, bootstrap, and status line. Modes change response detail only. Default to `direct`; read legacy `terse` as `direct` and `normal` as `balance`.
**Design:** none; the user supplied the modes and their meanings.

## Constraints
- `direct`: straight to the point, concise responses.
- `explain`: comprehensive explanations with useful context and examples.
- `balance`: enough explanation to be useful, without being comprehensive or too brief.
- One active mode, displayed as `🍯 HONEY · <mode>`; preserve hook-delivery qualification.
- Keep pause/resume, task sizing, proof before completion, and safety controls.
- Save defaults under `mode`; do not rewrite config during read-only bootstrap.
- Preserve unrelated config, RSI data, and personal instructions.

## What already exists
`honey/modes.py` parses whole-message commands and renders the bootstrap. Session dispatch, global activation, and the Claude status line consume those settings.

## File map
- `honey/modes.py`, `honey/bootstrap.md`: selection, legacy reads, response guidance, indicator.
- `honey/dispatch.py`, `honey/activation.py`, `honey/cli.py`: session migration, fallback, status line.
- `tests/test_modes.py`, existing hook and activation tests: executable behavior coverage.
- `README.md`, affected skills: current commands and consistent workflow guidance.
- `docs/design/plan.md`: mark original mode design superseded.

## Task: Replace modes end to end
- [x] Red/green: real hooks accept and persist each mode, render its guidance, and preserve selection on compact/resume.
- [x] Red/green: legacy defaults and sessions migrate; bootstrap stays read-only; status line displays the selected mode.
- [x] Update parser, bootstrap, consumers, and docs. Reject conflicting commands without changing settings.
- [x] Verify: `python3 tests/run.py` (33 scripts), Python 3.9 focused tests, release consistency, diff checks.
- [x] Review the complete diff and resolve material findings (independent reviewer: no blocking findings).
- [x] Install validated local changes, save the direct default, and verify installed bootstrap/status output.

## Verification results
- 33 isolated test scripts passed on Python 3.14.7; focused mode, activation, hook, and guard tests passed on Python 3.9.
- Fresh Codex sessions displayed each mode with real SessionStart, UserPromptSubmit, Stop, and SessionEnd events. The same explanation prompt produced 160 words in direct, 334 in explain, and 181 in balance; these are observed samples, not enforced length limits.
- A fresh Claude session displayed `🍯 HONEY · direct` with the same four native events.
- Both installed global fallbacks and the Claude status line read the direct default. Unrelated RSI and budget settings remained unchanged.
- Source edits are local and uncommitted; no release or push was requested for this change.

## Review focus
- A saved session override wins over a global default.
- Invalid commands and ordinary prose do not switch modes.
- All modes retain the same workflow and safety rules.
- Switching preserves pause state and unrelated config.

## Not in scope
- New workflow intensity presets, release tags, or RSI policy changes: the request concerns response style.
- Rewriting historical plans: mark the original design superseded.
