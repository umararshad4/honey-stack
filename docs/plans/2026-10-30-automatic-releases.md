# Automatic main releases

**Goal:** Publish a versioned GitHub release automatically after main passes CI.
**Approach:** HOLD scope. Add a release job after the existing test matrix and reuse the manual version-bump code. Release only the tested current main revision; a newer main revision is released by its own successful run.
**Design:** none; user authorized implementation and PR delivery.

## Constraints
- Pull requests and failed tests cannot publish. Default job permissions are read-only; only the main release job has contents write.
- Use the repository token. Publish the GitHub release in the same job because token-authored pushes do not trigger another workflow.
- Conventional commits choose major for breaking changes, minor for features, patch otherwise. Update both plugin manifests, Python version, changelog, commit and tag together.
- Push main and tag atomically. Never force-push or overwrite a tag. Stale CI is skipped; concurrent main changes reject the push.
- Retry a run that already pushed its tag by publishing that same tag without another bump. Preserve manual tagged releases.
- Keep concurrent local work untouched in its existing checkouts. No merge or live release is requested now.

## File map
- `scripts/release.py`: reusable version/changelog preparation; preserve manual CLI.
- `scripts/auto_release.py`: version selection, CI SHA guard, atomic push and idempotent publication.
- `.github/workflows/ci.yml`: guarded release job and pinned current actions.
- `.github/workflows/release.yml`: retain manual tags; pin current actions and serialize publication.
- `tests/test_auto_release.py`: real disposable repositories with a GitHub API fixture.
- `README.md`, `CHANGELOG.md`: describe release timing and retry behavior.

## Tasks
- [x] Add semver selection and refactor shared bump preparation; test patch/minor/major and empty changelog fallback.
- [x] Add auto-release flow; test actual remote commit/tag/version, reruns and failed publication, stale CI, failed tests, dirty checkout and remote races.
- [x] Wire the CI job after all tests; validate workflow syntax, run full suite, version consistency and diff checks.
- [x] Review, push and open a PR against main; verify remote SHA and PR state.

## Failure modes
| Failure | Expected behavior |
|---|---|
| Tests fail after metadata bump | No commit or tag is pushed |
| Another merge lands during release | Atomic push fails; no orphan remote tag |
| Tag push succeeds, GitHub API fails | Rerun finds the source marker and publishes the same tag |
| Old CI completes after newer main | Skip old revision; newer CI owns the release |
| GitHub authentication fails | Fail visibly without treating failure as a missing release |

## Not in scope
- Merging this PR or publishing a release in this session.
- New credentials, paid tooling or release services.

## Review and focused proof
- Workflow/security review: no must-fix findings; actual Actions token permissions remain a post-merge proof boundary.
- Correctness review found tests could commit source changes and leave a clean tree. Added an exact HEAD guard and a regression that failed before the fix and passed afterward.
- Release integration coverage: 18 cases including semantic-version precedence, real commit/tag pushes, failed tests, authentication failure, stale revisions, atomic race rejection, publication recovery and manual releases.
- Actionlint 1.7.12 passes both workflows.

## Final checks
- All 33 test scripts passed on Python 3.14.7 and Python 3.9.6, including 18 release scenarios.
- Both workflows passed actionlint 1.7.12; release version consistency and `git diff --check` passed.
- Actual GitHub release execution remains unverified until the PR merges and main CI succeeds.
