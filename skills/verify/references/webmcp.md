# WebMCP verification

Use the shared [WebMCP with e2e guide](../../qa/references/webmcp.md) for every browser verification. It owns compatibility discovery, runnable templates, call semantics, fallback and evidence requirements. Keep app-specific verification skills aligned with it.

Before marking a web requirement complete:

- Record native WebMCP, intentional app polyfill, no registered tools, or unavailable support. Reuse verified capability status until its page/auth context changes. Use tools to replace eligible setup without inventing registrations or duplicating the UI setup path.
- For changed tool contracts, check the schema, valid calls, relevant invalid inputs and permissions, error handling and registration lifecycle. A tool result needs an independent outcome assertion.
- For changed user interactions, run the actual control through e2e and check its result. Add current visual proof when appearance matters. A successful tool call cannot clear a failed UI test.
- Preserve required backend/persistence, security, lint and type checks. Tool discovery does not satisfy them.
- Separate required failures from optional acceleration fallback. Do not suppress a tool error, timeout or failed assertion by rerunning through the UI and reporting only its success.
- Reuse existing tests, verified preflight and healthy owned sessions with isolated test state. Do not require a standalone WebMCP contract suite for an unrelated UI change. Keep that suite when the contract is in scope or required coverage is missing.
- Apply [fast QA](../../qa/references/fast-qa.md) without weakening evidence: verify readiness before direct comparisons, choose state-transition or stability assertions to match the requirement, verify failure screenshots when traces are disabled, and prove data/account isolation before increasing workers. Balance file/target units before adding workers, and run the WebMCP target through the bundled launcher with `--workers` so each worker gets its own browser. Native e2e reports normally provide the required completion evidence without a custom normalizer.
- Confirm the case matrix covers every requested requirement at each relevant viewport before accepting a compact report. Batching setup must not batch away UI acceptance actions. On a partial batch failure, inspect state and preserve the failing call evidence rather than repeating all writes.

The completion report identifies tool-contract and UI coverage, unsupported or skipped scope, versions, commands and evidence. Make speed claims only from matched case/viewport/timeout matrices and repeated measurements; separate agent time from runner time. Reading this guide or adding a config entry is not proof of a live WebMCP run.
