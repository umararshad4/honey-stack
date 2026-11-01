# Skills

Back to the [README](../README.md).

**Flow:** grill → plan → execute → verify → review → ship. Bugs start at **debug**.

**Automatic** (the agent picks them): `grill` · `plan` · `execute` · `debug` · `tdd` · `verify` · `review` · `ship` · `deploy` · `test-design` · `tooling` · `database` · `perf` · `observability` · `api-design` · `upgrade` · `incident` · `frontend` · `stageshow` · `qa` · `security` · `docs`

**On demand** (you call them): `honey` · `rsi` · `unslop` · `reverse-engineer` · `handoff` · `prototype` · `architecture` · `domain` · `teach` · `write-skill` · `principles` · `opensrc` · `project-verify` · `triage` · `research` · `statechart`

Invoke with `/honey:<skill>` in Claude Code or `$<skill>` in Codex.

## Focused workflows

- **`project-verify`** creates or maintains a project-local verification skill: launch, readiness/ownership checks, feature journeys, observable side effects, retained evidence and safe cleanup. A generated harness is ready only after its recipe runs successfully. `verify` and `qa` reuse it; a small edit does not require a new harness.
- **`triage`** reads complete reports, checks duplicates and existing fixes, and produces evidence-backed states and agent briefs. Its explicit reproduce/fix branch requires before/after proof and routes delivery through `ship`. RSI backlog qualification uses this same workflow; the background publisher and its opt-in settings are unchanged. This skill does not deploy a GitHub bot or automatically close, merge or release issues.
- **`research`** answers technical and product questions from primary sources, with constraints, source dates, citations and unknowns. Uses available Exa tools for deep discovery and available search/GitHub tools as fallback. `opensrc` remains the focused option for installed dependency APIs.
- **`statechart`** optionally checks queue, retry and workflow invariants with a model checker, records assumptions and finite bounds, and explains counterexamples. A checked model is not proof of the production code; missing checker prerequisites remain explicit.
- **Frontend quality** stays in `frontend`, `qa`, `review` and `perf`: motion audit/review and frame diagnostics, realistic worst-case datasets, touch/viewport/safe-area checks and honest real-device coverage. `stageshow` owns mocked product illustrations and cursor demos, not the production application's component stack.
- **`rsi retro`** is a skill workflow for evidence-backed improvements to navigation, checks and tooling; it is not a CLI subcommand. `write-skill` carries agent-writing guidance, and `perf` uses a benchmark validity checklist before making speedup claims.

The four new entry points are explicitly invoked on both Claude Code and Codex; their descriptions do not expand the always-loaded workflow. Existing skills link to their relevant branches when needed.

## Browser QA

`qa` uses the tester-army/e2e CLI and project MCP server by default, with bundled upstream setup, test-writing, replay-cache, debugging, mobile, CI and bug-bash guidance. The runner and engine are installed in the app being tested; Honey does not bundle browser binaries. See [the QA command guide](../skills/qa/references/e2e.md).

Browser QA and verification also discover existing WebMCP tools for suitable setup, exploration and contract checks. Real user interactions, visual checks and backend assertions still prove their respective requirements. Unsupported pages fall back to ordinary e2e checks. The [WebMCP guide](../skills/qa/references/webmcp.md) includes an isolated Chromium runner and same-session e2e adapter; it does not add WebMCP to websites automatically.

WebMCP replaces eligible setup rather than adding a second walkthrough. QA reuses existing tests and verified sessions; standalone tool-contract checks run when that contract is relevant. Performance claims use repeated runs of the same cases, viewports, timeouts and assertions.

The [fast QA path](../skills/qa/references/fast-qa.md) uses native reports, avoids duplicate polling after verified readiness, and schedules independent flow files across bounded workers. It keeps failure screenshots and exact case coverage; shared accounts or data keep serial execution.
