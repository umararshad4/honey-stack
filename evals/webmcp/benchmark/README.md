# Matched full QA benchmark

From `evals/webmcp`, run `npm ci` if dependencies are absent, install Chromium with `npx @e2e-dev/web install chromium --with-deps`, then run:

```sh
npm run benchmark
```

The same 12 tests run at desktop 1440x900 and mobile 390x844 in two modes. `ui` creates fixture records through the form; `webmcp` creates them through the existing native tool. Actual form, checkbox, search, keyboard, reload and layout acceptance actions are identical. Four tests per viewport create eight setup records each. Both modes use the same native Chromium launcher, timeouts, retries, single worker and screenshot policy.

The WebMCP setup uses one sequential `webmcpBatch` call per fixture group. It stops after errors or navigation and still checks the resulting rows independently. The full contract smoke suite in the parent directory also verifies that later writes do not run after a partial batch failure.

Five measured pairs alternate mode order after an excluded warm-up pair. Each command starts a fresh isolated browser; tests use isolated contexts. Dependencies and the local fixture server are outside the timer. Wall time includes the browser/CLI launcher; runner time is separately read from e2e's report. No agent/model calls or cache-replay performance are measured.

The fixture deliberately has five failing behaviors: ignored High/Low priorities, lost tasks after reload, lost completion after reload, Escape not dismissing the dialog and mobile overflow. Every run must produce the same 13 passing and 11 failing case/viewport pairs. The benchmark driver fails if a defect disappears, a new failure occurs, or any case is skipped. A raw e2e exit code of 1 is expected for this defective fixture; it is never rewritten as passing product QA.

Results, per-run logs, screenshots and traces are under `benchmark/.e2e/<timestamp>/`. `summary.json` records each run and median/tail timings. With five samples, p95/p99 are the observed maximum, not reliable population-tail estimates. This benchmark measures this fixture and workload; it does not establish a speedup for every application or whole agent sessions.
