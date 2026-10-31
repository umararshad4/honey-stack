# Reproduce and fix a qualified report

Use this branch only for an explicit reproduce/fix request. Reproduce-only permits investigation, not product edits. Issue readiness and an existing publication setting do not expand the task's authority.

## 1. Establish the target

Read the report, current ownership, relevant code/history and existing fix artifacts. Identify the exact build, account role, dataset, platform and user surface. Reuse an existing project-local verification harness; if creating or maintaining one is requested, read [the project-verify procedure](../../project-verify/SKILL.md) as reference guidance. Its standalone command stays explicit-only. Use `qa` for browser driving and `debug` for root-cause analysis. If another person owns the implementation, report that fact and coordinate rather than creating a competing patch. If a fix PR/commit exists, switch to verifying it.

Name the correct end state, broken end state and discriminating step. A screenshot of a loading dialog is not proof of the reported final-state failure. For API/CLI/library reports use the corresponding public interface; do not require a browser for a non-UI bug.

Done when: target identity, control path, discriminating observation, scope and existing-fix/ownership status are known.

## 2. Reproduce the exact symptom

Run the reported path, capture the action and resulting state, reset only test-owned state, then repeat independently. A UI report must fail through the real UI; forcing an internal state flag, editing markup or using a test-only setter is not a UI reproduction. For nondeterministic failures, record attempts and observed frequency rather than claiming two clean attempts disprove the report.

Capture logs, responses, screenshots or recordings that show the discriminating state. Inspect that evidence and retain it outside source control. Missing prerequisites are `blocked`; a usable environment without the symptom is `not reproduced`; neither is `fixed` or grounds for automatic closure.

Done when: the same symptom is independently observed twice, or the report states attempts, conditions and why confirmation is unavailable.

## 3. Verify existing work or implement

For an existing fix, retain baseline proof and run the same path against the candidate revision. Do not edit, replace or merge that artifact from a verification-only request. If the baseline cannot be obtained, report candidate-only evidence and the missing before comparison.

For an authorized new fix, require a confirmed reproduction, a supported root cause and no competing implementation. Use `debug`, then `tdd` where a cheap seam exists. Scope the fix to the confirmed mechanism. Stop implementation and return a brief if the required change exceeds the agreed scope or needs unavailable access.

Done when: the existing artifact is evaluated without duplicate work, or the minimal authorized fix and its regression check address the confirmed cause.

## 4. Prove and hand off

Keep baseline evidence. Repeat the same path on the changed revision with the same relevant conditions, showing the expected state and absence of the original symptom. Cover adjacent states, roles and failure paths affected by the change. Use `verify` and `review`; a passing unit test is supporting evidence, not a substitute for reproducing a UI defect through the UI.

Report revision/build IDs, attempts, before/after evidence, test results and unresolved limits. Preserve artifacts through cleanup. Clean only processes, profiles and data this run owns, using the project's harness cleanup instructions. When a PR is requested, hand this evidence to `ship`; do not merge or release merely because reproduction and local checks passed.

Done when: the original symptom has before/after evidence on named revisions, required checks pass or are explicitly limited, and the requested handoff accurately reflects delivery state.
