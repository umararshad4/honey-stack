# Native WebMCP evaluation

This local fixture tests the shipped adapter and runner in a real Chromium browser. It does not test a customer's application or claim a speedup. No model provider is needed.

## Delta CLI integration QA

The same pinned e2e installation also runs Honey's Delta commands through a tools-only target. This exercises the actual `bin/honey` entry point; it does not claim browser or native Codex session-sync coverage.

```sh
# From the repository root, after npm ci in evals/webmcp:
python3 tests/qa_delta.py
python3 tests/qa_delta.py --live
```

The first command checks readiness, missing-tool fallback, and rejected inputs. Its two live-history cases are explicitly skipped. `--live` needs a signed-in Delta CLI: it creates one projectless thread with private upload requested, verifies that no worktrees are attached, appends two synthetic messages with local acknowledgement, verifies search and bounded reads, and archives the thread even after a test failure. It never attaches repository files or invokes a model. The observed upload state is recorded separately; local CLI success does not prove cloud sync. Archiving is not server-side deletion. `fixture-state.json` and e2e's native report are retained under `.e2e-delta/<run>/`.

This target has no page or browser. WebMCP remains appropriate for the separate browser fixture below; it is not used to simulate CLI proof.

### Recall and handoff comparison

Preserve the prior source, including untracked integration files, outside the repository before editing. Then run:

```sh
python3 tests/qa_delta_compare.py --baseline /absolute/prior-source --output /absolute/results --pairs 3
python3 tests/qa_delta_compare.py --baseline /absolute/prior-source --output /absolute/live-results --pairs 3 --live
```

The comparison gives both versions the same 40-message corpus and literal ground truth. The prior adapter gets the known corpus length and reads both legal 20-message pages; the new adapter uses `recall`. It measures exact decision recovery, caller-visible characters, native/Honey invocations and wall time. Characters are not model tokens; exact recovery is not an agent-comprehension score. The separate native e2e report covers ambiguity, stale summaries, output budgets, error recovery, capture preview/apply and actual handoff write/restore/drift/fallback. External-boundary fixtures are labeled separately from native Delta calls. No model or browser is involved in these CLI cases.

Live fixtures contain only synthetic messages and no repository attachments. They are archived, and the actual upload/access state is retained; a queued local acknowledgement cannot prove cloud or cross-machine recovery. Existing reports are evidence for their specific source version, not subsequent edits.

## Browser fixture

From this directory, install the pinned dependencies and browser:

```sh
npm ci
npx @e2e-dev/web install chromium --with-deps
npm test
npm run test:fallback
```

The native run must pass discovery, structured calls, independent visible state, actual button interaction, missing tools, error results, exceptions, invalid input and stale discovery after navigation. The ordinary run demonstrates UI fallback without WebMCP enabled and explicitly skips the native-only contract test.

The deliberate broken-button run must exit nonzero even though the native tool works:

```sh
BROKEN_UI=1 npm test
```

Inspect `.e2e/report.json` and `.e2e/results/` after each run, or pass distinct `--output` directories to the runner. These tests use a private fixture and delete the temporary Chromium profile after each command. They do not alter the app or user browser.

From the repository root, `python3 tests/test_webmcp_launcher.py` checks that e2e starts while the browser boots, one isolated browser per worker, headless-build selection with its full-Chromium fallback, a stopped run when a browser fails to start, prompt exit, preservation of a failing runner status, profile removal and forced cleanup of a browser that ignores shutdown. These lifecycle tests use a fake browser; the commands above provide the separate real-browser proof.
