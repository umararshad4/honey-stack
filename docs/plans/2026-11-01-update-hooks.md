# Update hooks plan

**Goal:** Let a user request an immediate Honey release check and delegate review of Honey's Codex hooks with `$honey update hooks`.
**Approach:** Reuse the release updater and Codex's native hook review. The request authorizes one run for Honey only; it does not preapprove later releases. HOLD scope.
**Design:** none.

## Global constraints

- Never change another plugin's trust, bypass Codex hook trust, or update a dirty or diverged checkout.
- The existing automatic check remains hourly; an explicit request can check immediately.
- Test against disposable repositories and plugin homes; do not update the installed plugin while developing.

## Review focus

- A forced check must respect opt-out, pending refresh and concurrent update work.
- A checkout already at the release must still allow the installed plugin to refresh.
- A native review must target the exact Honey version and leave unrelated hooks untouched.

## File map

- `honey/autoupdate.py`, `honey/cli.py`: immediate update check and CLI.
- `tests/test_autoupdate_local.py`: isolated release and concurrency behavior.
- `honey/bootstrap.md`, `tests/test_modes.py`: route the plain phrase even when hooks are unverified.
- `skills/honey/SKILL.md`, `skills/honey/references/update-hooks.md`, `README.md`: explicit invocation and review procedure.

### Task 1: Immediate release check

**Interfaces:** `run(force=False)` preserves normal scheduling; `honey autoupdate --now` requests a fresh check.
- [ ] Verify a recent check does not prevent an explicit request, while opt-out and dirty checkout still block it.
- [ ] Verify a current checkout refreshes its installed copy and concurrent checks do not race.
- [ ] Run `python3 tests/test_autoupdate_local.py`.

### Task 2: User-invoked hook review

**Interfaces:** `$honey update hooks` authorizes the agent to review and trust Honey for this run only.
- [ ] Inspect release and installed bytes, use Codex's review UI, and stop if unrelated hooks or mismatched content could be approved.
- [ ] Verify docs, CLI help and skill references agree; check actual hook delivery separately from trusted status.
