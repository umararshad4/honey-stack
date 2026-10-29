# Global activation and release readiness

**Goal:** Load Honey's workflow and truthful indicator in Codex and Claude sessions even when startup hooks are absent, and restore automatic-release readiness on the canonical main checkout.
**Scope:** Existing bootstrap, global instruction files and updater. Preserve user preferences, pause controls, dollar-cap opt-out and native hook trust. The user requested fixing the previously identified merge/main/session blockers and global activation.

## Tasks
- [x] Reproduce false updater readiness on a feature branch and a main branch with local commits.
- [x] Reproduce absent global bootstrap and missing read-only bootstrap command.
- [x] Add an idempotent, backed-up global instruction block with conflict-safe removal.
- [x] Add a read-only bootstrap command: load modes and workflow, honor pauses, and label missing native delivery `hooks unverified` without inventing lifecycle events.
- [x] Report feature branches and local-only main commits as skipped before claiming the installed release is current.
- [x] Independent review; both findings reproduced and fixed. All 32 test scripts passed; global activation and updater tests passed on Python 3.9.
- [x] Activate both global instruction entrypoints, preserving existing preferences.
- [ ] Publish and merge the changes through CI, return the source checkout to main, and sync installed copies.
- [ ] Verify a fresh native session's visible indicator, lifecycle delivery, canonical updater readiness and existing-session limitations.

## Limits
- Native hook approval remains a host security control; no unattended approval bypass is added.
- The global fallback activates workflow instructions only. It does not manufacture hook health or pretend background jobs ran.
- Existing running sessions may need to load the new bootstrap or restart; new sessions read the global entrypoint.

## Local runtime proof
- Fresh native Codex session ran bootstrap and displayed `🍯 HONEY · ultra · strict`, with lifecycle events observed.
- Fresh session with native hooks disabled ran the global fallback and displayed `hooks unverified`; no native events were invented.
- Remote delivery and final main/installation checks are recorded in the PR and task completion report.
