# Fast e2e and WebMCP QA

Use this path for an existing web project. Keep every requested case and viewport. Speed comes from avoiding repeated work and using supported concurrency, not shortening timeouts until defects disappear.

## Run the existing suite first

Read the matching test/config and run it. Reuse known versions and setup from this session. Load an upstream guide only when a missing API or setup question requires it. Do not write a second runner or report converter for ordinary QA.

```sh
npx e2e run tests/search.e2e.ts --retries 0 --reporter list,markdown
```

Read `.e2e/report.json` and `.e2e/summary.md`. The canonical report already contains case status, errors, attempts and artifact paths. `--reporter json` emits the JSON report to stdout. Build custom output only when the user or an integration requires a schema the native report cannot satisfy.

## Use isolated workers

Upstream e2e defaults locally to half the available cores, and to one worker in CI. Do not copy `workers: 1` into every project. For independent web cases with separate contexts, test users and fixture records, start with two workers. Try four when the machine and app can support them; keep the faster setting only after checking outcome parity and variance.

```sh
npx e2e run tests/search.e2e.ts --workers 2 --retries 0 --reporter list,markdown
```

Keep one worker for shared accounts, global app state, ordered workflows, device limits or constrained services. A fresh browser context alone does not isolate a shared database. Never run destructive cases in parallel against shared state. Prefer a browser shared for a worker's lifetime with isolated contexts over launching one browser per case.

The scheduler assigns a file/target unit to a worker. A single test file on two targets exposes only two parallel units, even with four workers. Split independent flows into a few balanced files, with reusable fixtures in a helper module. Count files × targets before adding more files: two files on two targets already expose four units. Extra short units can add worker startup and teardown without useful concurrency. Compare a few coherent groupings; do not split dependent steps or create one file per assertion. Verify the report shows overlapping execution before claiming parallel speedup. See the [upstream scheduling unit](https://github.com/tester-army/e2e/blob/main/packages/e2e/src/run/units.ts).

## Keep the browser path light

Check the browser before tuning tests. On the matched 24-case fixture, Playwright's headless Chromium build with its automation switches ran the same suite in about a third of the time full Chromium's new headless mode took with minimal switches, with identical outcomes. e2e's ordinary local target already uses that build. The bundled [WebMCP launcher](webmcp.md#3-add-the-e2e-adapter-to-an-app) uses it too, starts e2e while its browsers boot and enables Node's compile cache.

Give each worker its own browser rather than attaching several workers to one browser over CDP: each worker's Playwright also adopts and instruments every other worker's pages. Pass `--workers` to the WebMCP launcher; it starts that many browsers. More workers are not free: each adds a Node process and its module loading. Six workers on an 8-core laptop were no faster than four for this suite. Use full Chromium only when a requirement needs a feature the headless build lacks, and say so in the report.

## Read state once after readiness

Use auto-waiting locators for interactions and for asynchronous outcomes. Wait for the real completion signal, such as the relevant response, a loading indicator disappearing, or the app's documented saved state.

After that signal, compare the value already read instead of querying the same state again with another polling matcher:

```ts
await expect(screen.getByRole('status')).toHaveText('Saved');
const text = await screen.getByRole('listitem').filter({ hasText: title }).textContent();
expect(text).toContain('Priority: High');
```

Do not assume that visible means fully loaded. Keep polling when the value can still change asynchronously. Do not replace a required eventual-state assertion with an immediate read merely to fail faster. A static page whose load has completed can use direct comparisons of its read values; a background save needs its completion signal first.

Batch reviewed WebMCP fixture writes through `webmcpBatch`, then assert the resulting state. Keep form, keyboard, search and checkbox acceptance actions on the actual controls.

## Assert the intended state, not an unintended quiet period

In e2e, a negated locator matcher waits for continuous truth for up to 1000ms. Use it when that stability window is the requirement. For a checkbox that should become unchecked, the positive state matcher keeps asynchronous polling without adding that window:

```ts
const done = screen.getByRole('checkbox', 'Complete Plan sprint');
await done.uncheck();
await expect(done).toBeChecked({ checked: false });
```

Prefer a unique accessible name for a control over scanning a row and then locating its child when both identify the same control. Keep the surrounding row assertion when it proves a separate requirement. Do not rewrite “must stay absent” as “is absent now” for speed. See [e2e matcher semantics](https://github.com/tester-army/e2e/blob/main/docs/reference/expect.mdx).

## Choose the evidence cost deliberately

The normal trace mode is `retain-on-failure`. A bare `--trace` means `on`, including passing tests. Do not add it to every command without a need.

For a fast audit that requires failure screenshots and observed values but no full step trace, `--trace off` is supported. e2e still captures failed-attempt screenshots when the engine can. Verify the actual required files exist. If they do not, the audit is incomplete. Add a requested screenshot for each distinct visual state the task needs.

```sh
npx e2e run tests/search.e2e.ts --workers 2 --retries 0 --trace off --reporter list,markdown
```

Keep full traces when requested, when investigating an intermittent/unknown failure, or when they are required by the project. To investigate a known failure, rerun just its `file:line` with `--trace on`. Do not rerun the whole suite solely to capture that case.

The native failure report already captures a screen tree and screenshot when available. Reuse those artifacts rather than requesting the same tree again in a `catch` or `finally`; collect extra fields only when the native report omits the fact needed to diagnose the case. Capture whole-screen trees during initial locator discovery, not before and after every successful action. Preserve original failure evidence before reruns. Never suppress page errors or replace failed assertions to make the report green.

The bundled WebMCP launcher cancels its shutdown deadline after Chrome exits. Keep that behavior when adapting it: `Promise.race` does not cancel a losing timer, and an uncleared timer adds idle wall time to every command. Keep the bounded forced-shutdown path for an unresponsive owned browser.

## Prove the improvement

Compare against the previous command with the same cases, viewports and assertions. Preserve exact failure identities, not just counts. Record worker count, tracing mode and whether startup is included. If concurrency changes, say so; do not call it an equal-resource engine benchmark. Measure first-time agent work separately from prepared runs.

Sources checked 2026-11-01: [e2e configuration](https://github.com/tester-army/e2e/blob/main/docs/reference/config.mdx), [runner API](https://github.com/tester-army/e2e/blob/main/docs/reference/runner.mdx), [debugging and report artifacts](https://github.com/tester-army/e2e/blob/main/docs/debugging.mdx), [browser fixture](https://github.com/tester-army/e2e/blob/main/docs/browser.mdx), [Node cancellable timers](https://nodejs.org/api/timers.html#timerspromisessettimeoutdelay-value-options).
