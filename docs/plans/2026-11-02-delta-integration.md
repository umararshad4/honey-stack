# Optional Delta history integration

**Goal:** Let Honey users inspect Delta readiness, search past work, and read a supplied thread when preparing or restoring a handoff.
**Approach:** HOLD the agreed optional-history and handoff scope. Reuse the installed Delta CLI with one small read-only adapter; Delta keeps ownership of authentication, storage, and synchronization.
**Design:** The accepted scope in this conversation: optional history lookup and handoff references, with local handoffs when Delta is unavailable.

## Global constraints

- Python 3.9+, standard library only; no new production dependency.
- Only explicit `honey delta status`, `search`, and `read` commands invoke Delta.
- No automatic uploads, sharing, installs, model queries, or RSI imports.
- Search defaults to five results, at most twenty. Reads accept one thread and a window of at most twenty messages, default `1-1` so a short thread can be read without exceeding its length.
- Accept an opaque thread ID or HTTPS `delta.dev/join/` thread link. Reject foreign URLs and command-like references before running a subprocess. A local ID does not imply a shareable URL.
- External transcripts are historical context, not new user instructions, approval, or fresh test proof.
- Keep the local handoff summary. Include only a supplied, verified Delta reference; do not guess the current thread or publish one to obtain a link.
- The initial phase kept changes local. The user's follow-up authorizes a reviewed PR, merge, release and verified installation.

## Existing pieces and alternatives

`honey/cli.py` owns explicit commands; `skills/handoff/SKILL.md` owns handoffs; the router, README, and skills guide own discovery. `tests/helpers.py` and `tests/run.py` already isolate state and avoid paid calls. `evals/webmcp/` pins e2e and supports a tools-only target.

A skill-only recipe is smaller but lacks deterministic validation and failure checks. A full session recorder is much larger and outside the agreed scope. The small adapter keeps the behavior testable without a service or persistent state.

## Review focus

1. Shell or option injection through references, search terms, or paths.
2. Missing tools, signed-out accounts, malformed JSON, CLI errors, and timeouts.
3. Credential leakage from raw CLI stderr.
4. Unbounded reads or accidental mutation of Delta/Honey state.
5. Missing or stale references preventing ordinary local handoffs.

## File map

- `honey/delta.py`: read-only adapter; `honey/cli.py`: route and help.
- `tests/test_delta.py`: CLI boundary tests.
- `skills/delta/SKILL.md`, `skills/delta/agents/openai.yaml`: on-demand workflow for both hosts.
- `skills/handoff/SKILL.md`: optional verified Delta references.
- `skills/honey/SKILL.md`, `README.md`, `docs/skills.md`: discovery and limits.
- `tests/test_workflow_skills.py`: registration/reference checks.
- `evals/webmcp/delta.e2e.ts`, `evals/webmcp/e2e.delta.config.ts`: actual CLI QA through e2e.
- `evals/webmcp/package.json`, `evals/webmcp/README.md`: QA command and instructions.
- `tests/qa_delta.py`: explicit live synthetic fixture, native report, cleanup.

## Tasks

### 1. Read-only adapter

- [x] Observe `python3 bin/honey delta status` fail before implementation.
- [x] Add status, bounded search/read, finite timeouts, and argv-only subprocess calls.
- [x] Test readiness, missing/old CLI, signed-out state, failures, malformed responses, literal arguments, unsafe URLs, and window limits.
- [x] Verify `python3 tests/test_delta.py` (20 tests).

### 2. Skill and handoff

- [x] Register `delta` on demand on both hosts; document optional installation and Codex capture limits.
- [x] Keep local handoffs usable without Delta; verify supplied references before including them.
- [x] Verify `python3 tests/test_workflow_skills.py` and `claude plugin validate .`.

### 3. QA and review

- [x] Run e2e tools-only cases for readiness, missing tool, bad input, empty search, and synthetic history.
- [x] For live QA, create only a projectless thread with private upload requested, verify zero attached worktrees, append synthetic messages with local acknowledgement, then archive it. Report the observed cloud upload state separately.
- [x] Run `python3 tests/qa_delta.py --live`; read the native selected/passed/failed/skipped counts (7 passed, no failures or skips).
- [x] Run the existing native WebMCP smoke separately as QA infrastructure proof (4 passed).
- [x] Review the diff; run the full Python suite (40 scripts), release consistency, and `git diff --check`.

## Failure behavior

| Path | Failure | Outcome |
|---|---|---|
| Status | Missing Delta or signed-out account | Explicit not-ready reason and setup hint |
| CLI call | Timeout, malformed JSON, nonzero exit | Nonzero Honey result with a generic error; no raw stderr |
| Read | Foreign URL, option-like ID, invalid/oversized range | Reject before invoking Delta |
| Search | Empty query, bad limit, upstream error | Reject; never pretend failure means no matches |
| Handoff | No link, unavailable tool, inaccessible thread | Preserve local summary; mark reference unavailable |

## Not in scope

Native Codex recording/shared-turn control; automatic synchronization or publication; RSI imports or altered merge gates; model-backed queries; Delta UI changes; speedup claims. WebMCP does not establish CLI or Codex session-sync correctness.

## Rulings from live QA

- Delta 0.23.0 returned opaque local IDs instead of the docs' `thread_...` examples. Accept actual safe IDs and preserve supplied join URLs for native resolution.
- A local ID does not imply a share link. Return `url: null` for bare IDs, and retain a supplied URL only after Delta reads it successfully.
- Validate the observed native message envelope, roles/buffers, numbering, and requested count before returning history.
- Synthetic setup uses local acknowledgement because uploads can remain queued; report cloud upload state separately from live local history retrieval.

## Verification boundaries

- Boundary tests use a fake executable only for missing-tool, malformed-response, timeout, and argument safety cases. The live e2e run uses the actual signed-in Delta 0.23.0 CLI.
- Live local search and reads passed. Initial uploads queued; a later run verified private cloud upload and the returned share URL. Cross-machine recovery remains unverified. Synthetic threads were archived, not claimed deleted from the server.
- The separate WebMCP smoke verifies the existing native browser QA infrastructure, not a new Delta web UI.
- Python 3.14.7 executed the full suite; the new Python files also passed Python 3.9 grammar parsing. Native Python 3.9 execution was not available.
- Delivery requires the reviewed change to reach main, pass release CI and be verified in the installed Honey copies.
