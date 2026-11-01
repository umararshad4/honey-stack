# Native WebMCP evaluation

This local fixture tests the shipped adapter and runner in a real Chromium browser. It does not test a customer's application or claim a speedup. No model provider is needed.

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
