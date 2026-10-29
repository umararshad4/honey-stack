# RSI publication plan

**Goal:** Push validated shareable RSI skill changes to GitHub and open a reviewable PR automatically.
**Approach:** HOLD scope. Reuse evaluation, local application, the RSI lock and proposal storage. Add opt-in publication after local application, with a separate public commit containing only the skill file.
**Design:** none; user requested publication as part of the flow.

## Constraints and existing behavior
- Personal rules, instruction edits, guards, installer repairs, raw evidence and generated evaluation prompts stay local.
- Existing regression evaluation and local sync remain prerequisites. Publication cannot report local application as failed.
- Use authenticated `gh` and ordinary Git pushes; no automatic merge, release, force push or raw evidence in PR text.
- Preserve concurrent edits. Fail visibly on source/remote drift, unexpected paths, missing auth and conflicting remote branches.
- Retries reuse the saved public SHA and branch and find an existing PR before creating one.

## File map
- `honey/rsi/publish.py`: configuration, public commit construction, push/PR, persistent retry state (create).
- `honey/rsi/autonomy.py`: publish applied skills during automatic processing (modify).
- `honey/rsi/cli.py`: on/off/status and visible publication results (modify).
- `tests/test_rsi_publish.py`: disposable Git remote and mocked GitHub API boundary (create).
- `README.md`, `CHANGELOG.md`: controls and publication boundaries (modify).

## Tasks
- [x] Add CLI configuration and publish a locally applied evaluated skill using a clean commit containing only its skill file. Prove with a real disposable Git remote and synthetic private evaluation text.
- [x] Retry push/PR failures without duplicates or losing local application; reject drift and unpublished local runtime history. Prove with negative integration tests.
- [x] Wire automatic and explicit application, show publication receipts, document behavior; run `python3 tests/run.py`, `python3 scripts/release.py --check`, `git diff --check`.
- [ ] Review all changes, commit and push this implementation branch and open a PR.

## Failure modes
| Failure | Handling and proof |
|---|---|
| GitHub auth/push/create fails | Save blocked publication with reason, retain applied state, retry next pass |
| PR exists after ambiguous create failure | Find by exact branch/base, verify its head SHA, reuse it |
| Remote/runtime moved | Block before push; require fresh evaluation on the new runtime |
| Private prompt in patch ancestry | Build public tree from remote base, copy only target skill blob; inspect pushed history in test |

## Not in scope
- Publishing personal preferences or machine-specific configuration: private local data.
- Merging PRs or cutting releases: separate actions.
- Automatically resolving changed evaluation baselines: requires new evaluation.

## Verification
- `python3 tests/test_rsi_publish.py`: 12 integration tests passed; real disposable Git push with a mocked GitHub API.
- `python3 tests/run.py`: all 33 test scripts passed on Python 3.14.7.
- `python3 scripts/release.py --check`: version 0.11.0 consistent.
- `git diff --check`: clean.
- Self-review: publication allowlist, history isolation, CLI callers, partial failures, retry identity and closed-PR behavior checked.
