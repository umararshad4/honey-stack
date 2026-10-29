# Integrated delivery and verification fixes

**Goal:** Resolve the tested integration gaps without weakening verification or losing local changes.
**Approach:** Consolidate RSI publication, automatic releases and local response modes into the existing delivery branch. Add a trusted subprocess runner for hosts that cannot report inner tool events.

## Constraints
- Preserve both changelog additions and the original local checkout until its changes are committed and validated elsewhere.
- Do not parse or execute arbitrary tool-wrapper code, trust printed success, or manufacture lifecycle events.
- A runner result requires an actual successful subprocess, unchanged task identity and a matching Git source snapshot.
- Known edits, failed checks, changed HEAD/index and changed source invalidate proof. Opaque bookkeeping alone may preserve verified, matching proof.
- Keep publishing, release and mode changes together so they can be reviewed and merged without the earlier conflict.

## Tasks
- [x] Merge release work into the RSI branch and preserve both CHANGELOG additions.
- [x] Copy and commit validated local mode changes while retaining the original checkout.
- [x] Add `honey task run` and regression tests for failed, stale, forged and opaque-wrapper results.
- [ ] Run integrated suites on Python 3.9/3.14, workflow lint and direct installed verification.
- [ ] Push the consolidated PR update and report the exact remaining release state.

## Limits
The runner snapshots Git HEAD/index and tracked/non-ignored source only. Ignored dependencies and external services are outside its proof. Source symlinks and oversized snapshots fail explicitly.

## Review corrections
- Shared per-session locks now serialize hook and CLI state updates; the runner releases that lock while the subprocess runs. A regression proves a concurrent new prompt cannot be overwritten by verification.
- Opaque progress events during a long check do not invalidate its real result; file timestamps/content, HEAD and index still invalidate changed source.
