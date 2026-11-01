# Delta recall and handoff improvements

**Goal:** Recover a prior decision and resume verified work, with a reproducible comparison against the current integration.
**Approach:** HOLD the six improvements accepted by the user. Extend the existing stdlib adapter and handoff skill; native Delta owns history, authentication and capture. The baseline is preserved outside the checkout.
**Design:** Accepted recommendations in this conversation. No custom recorder, new service or paid model query. The user's follow-up authorizes remote publication and release installation.

## Constraints and existing pieces

- Keep existing status/search/read callers working. `ready` means installed and authenticated; capture, local readability and cloud upload are distinct facts.
- Reuse `honey/delta.py` for CLI access, and the existing handoff skill for the human summary. A metadata helper attaches provenance and checks restoration.
- Recall uses exact keyword matches in native transcripts, preserves source IDs/message numbers, and returns ambiguity instead of choosing an unrelated thread.
- Read/recall/summary output defaults to 12,000 characters, configurable from 2,000 to 64,000, with explicit truncation. Summaries are used only when marked fresh.
- Capture setup previews by default; applying requires an explicit mode, and an organization for upload modes. Preserve unrelated settings and keep local policy out of Git.
- Global activation is reversible and checked against installed bytes. No automatic upload of real conversations or changes to RSI merge gates.
- Docs alone leave the measured gaps; a recorder duplicates upstream machinery. Extending this adapter is the smallest complete approach.

## File map

- `honey/delta.py`: readiness, recall, summaries, budgets, errors and explicit capture setup.
- `honey/delta_handoff.py`: attach/restore provenance, Git state and evidence hashes.
- CLI/skills/README/docs: route and explain those workflows.
- Delta unit tests and `tests/qa_delta_compare.py`: public behavior and paired measurements.
- Existing `evals/webmcp` Delta suite: native e2e acceptance and reports.

## Failure cases

| Flow | Failure | Expected result |
|---|---|---|
| Status | Authenticated, upload queued | Local-only/queued, never cloud-ready |
| Recall | Early rejected hypothesis, late decision, ambiguous threads | Strongest latest exact match or explicit ambiguity |
| Projection | Stale summary, large output, invalid offsets | Withhold stale text, mark truncation, reject malformed data |
| Errors | Temporary outage or denied access | Preserve safe code; retry only explicit retryable errors |
| Setup | Preview, tracked/invalid config | No preview writes; reject unsafe overwrite; preserve other keys |
| Handoff | Changed Git/evidence or unavailable Delta | Preserve human summary; name drift and availability separately |

## Tasks

### 1. Preserve and measure the current integration
- [x] Snapshot tracked and untracked source and record its hashes.
- [x] Establish independent fixtures and ground truth, then record the baseline before implementation.

### 2. Adapter improvements
- [x] Run public-interface cases red, then implement readiness, safe errors, bounded output and recall.
- [x] Implement explicit capture preview/apply without enabling capture on the user's real repository.
- [x] Verify `python3 tests/test_delta.py` (30 tests).

### 3. Handoff provenance
- [x] Attach source/window and Git/evidence hashes to the existing human handoff.
- [x] Restore checks actual state and preserves local fallback; historical proof remains historical.
- [x] Verify `python3 tests/test_delta_handoff.py` (4 tests).

### 4. Comparison, QA and activation
- [x] Compare identical scenarios with a competent paginated baseline; label unavailable new capabilities honestly.
- [x] Run native e2e with real synthetic Delta history, record upload state and archive only our fixtures (13/13; 11 controlled/local cases and 2 native Delta cases).
- [x] Run the full regression suite, release consistency, skill checks and diff review (41 scripts on Python 3.14.7 and 3.9.6).
- [x] Activate the verified local plugin through native host commands and verify actual bytes and CLI behavior (613 files per host; outside-checkout smoke retained).
- [x] Report outcomes, output size, CLI calls and live limitations in a table (`evals/webmcp/.e2e-delta/improvements-20261101T195010Z/REPORT.md`).

## Observed limits and review resolutions

- Fixed regressions from independent review: symlinked capture parent, malformed error/metadata types, matched text removed by truncation, conflated cloud/local readiness, and handoff call ordering. Added an index-only Git drift regression.
- Native Delta IPC handshake failures occurred on both baseline and updated code. All attempts remain in the report; no reliability or speed gain is claimed.
- Final serial successful median: 38,271 to 2,619 returned characters (93.16% less); three native calls in both, three to one Honey invocations.
- Private synthetic upload and the returned share URL passed in the final follow-up. Cross-machine behavior and real Claude capture remain unverified. Setup was applied only to disposable test repositories.
- Local development installation passed; the follow-up delivery requires a published release and refreshed installation. Active Codex sessions still need normal hook review/new-session loading.

## Not in scope

- Native Codex recording, new MCP server, paid queries, automatic sharing or changed merge gates.
- Claiming cross-machine success without an uploaded thread and a second available machine.
