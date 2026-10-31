# Retrospective: improve the environment

Distilled from Matt Pocock's `retro` at 4ae2317ddb22b046e26455e4f9c9b3aaaf62212d (MIT).

Use the named session, or the current session when none is named. A retrospective reports recommendations; it does not grant permission to change global instructions, publish issues, or activate guards.

1. Read the actual corrections, failures, tool results and accepted outcomes. Distinguish a wrong requirement, missing evidence, an environment failure and an agent mistake. Cite the local evidence without copying private session content into public artifacts.
2. Inspect the repo's existing checks before suggesting another one. An unwired or broken lint/CI command is a wiring defect, not evidence the project needs a new rule. Inspect navigation pointers, missing logs/tool access, expensive repeated calls and unused instructions too.
3. Classify each remedy:
   - Fixed syntactic pattern, banned API, file layout or repeated command mistake: repair/add a deterministic lint, test, script or CI check at the existing boundary.
   - Slow discovery: add a precise navigation pointer to the relevant source or reference, not a global explanation of the whole repo.
   - Missing observability: expose the needed log/status through an existing read-only tool, with credentials handled by the host.
   - Judgment error: clarify the relevant skill or review rubric through `write-skill`, after evidence supports the change.
   - Redundant instruction: remove it or consolidate it with its owner, rather than append another warning.
4. Rank a small set by evidence and expected recurrence. Record `failure → existing safeguard → proposed structural change → verification`. Mark single-session theories as candidates, not established preferences.
5. For approved changes, use the owning skill and its checks. For issue-worthy unsupported diagnoses, read [the triage procedure](../../triage/SKILL.md); do not treat a proposed remedy as a verified bug or a published issue as an applied fix.

Done when: every recommendation has an observed failure, an owner and a check that would catch recurrence; unresolved uncertainty stays visible.
