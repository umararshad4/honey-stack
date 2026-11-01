# e2e command guide

For page-provided WebMCP tools, use [WebMCP with e2e](webmcp.md). Its Chromium wrapper runs normal e2e test files through the same engine. `npx e2e mcp` remains the separate app-control server; it does not enable WebMCP or expose a WebMCP call command.

For an established project, reuse its matching test and command. Read [fast QA](fast-qa.md) for the worker, reporting and evidence choices. Read the [upstream skill](tester-army/e2e/GUIDE.md) for initial setup or an unfamiliar flow, then only the matching topic. These examples match upstream commit `1d671f6786b1eff4b43718ddc413b0bfa21abbcb`, e2e 0.22.0. Use the installed package's `guide` and `--help` when versions differ. Replace sample filenames, line numbers, targets and goals with the app's real values.

## Install and inspect

```bash
node --version
npx e2e --version
npx e2e init --help
npx e2e init
# Noninteractive deterministic setup, when project edits are authorized:
npx e2e init --yes --gateway none --skills none --mcp none --no-install
npx e2e guide setup
npx e2e guide running
npx e2e list
npx e2e list --reporter json
```

Node must be >=24.8, or >=22.22.3 on the Node 22 line. `init` is interactive; in an agent shell use its explicit flags from `--help`. `--yes` defaults to web plus Vercel AI Gateway and skips dependency installation; do not select that provider accidentally. Manual deterministic web setup uses `npm install --save-dev e2e @e2e-dev/web`. Add `ai@^7` and the selected provider only for agent steps. Preserve the project's package manager. Use `pnpm exec e2e` for an installed pnpm project.

Install browser binaries before CI rather than during an attempt:

```bash
npx @e2e-dev/web install chromium --with-deps
```

For provider/subscription authentication, use upstream `setup` and `agent`. Commands include `npx e2e login openai`, `npx e2e models`, and `npx e2e models github-copilot`; these are alternatives, not steps every project must run. Never print tokens or choose an account on the user's behalf.

## Focused test loop

```bash
npx e2e list tests/checkout.e2e.ts
npx e2e run tests/checkout.e2e.ts:12 --action-timeout 5000 --retries 0
npx e2e run tests/checkout.e2e.ts:12 --no-cache --retries 0
npx e2e run --last-failed
npx e2e run --target chromium --reporter list,junit
```

Recheck the `test(` line after editing above it. Keep cache on during repair; the no-cache run above is the final live proof for an agent test. Do not set a 5-second action timeout for a screen known to need longer. `--last-failed` reads the prior report, so preserve it before a different run.

## Live app and exploration

```bash
npx e2e mcp --help
npx e2e mcp
npx e2e guide mcp
npx e2e explore --help
npx e2e explore 'Check the account settings save flow' --max-steps 3 --output .e2e/proof/settings
npx e2e guide bug-bash
```

`mcp` is a persistent stdio server, not a shell command that returns a screenshot. Register it in the target project's client configuration, then use its `open_session`, `tools`, `call`, and `close_session` tools. `call` exposes the session catalog, including `observe`, `locate`, `run_code`, interaction verbs, screenshot and recording. Read the actual catalog; do not invent direct tool names or arguments.

Exploration requires a configured model. Set budgets, target and persona from upstream `explore`/`bug-bash`; three steps are only a bounded smoke, not comprehensive QA. Use disposable per-charter accounts and app instances. A finding remains a hypothesis until its repro test fails for that reason.

## Evidence, cache and CI

```bash
# Normal report, using the project's trace policy:
npx e2e run tests/checkout.e2e.ts --reporter list,markdown
# Detailed diagnostic capture when needed:
npx e2e run tests/checkout.e2e.ts --trace on --video --output .e2e/proof/checkout
npx e2e cache stats
npx e2e cache ls
npx e2e list --changed-since origin/main
CI=1 npx e2e run --reporter list,junit
```

`--changed-since` applies configured filters; it is not automatic dependency inference. Inspect the selected pairs. CI defaults to one worker, one retry and a read-only replay cache. A retry outside strict-cache mode runs goals live. Commit `.e2e/cache/` if the project's policy permits; `init` initially ignores it. Never commit auth sessions, private artifacts or secrets.

Results are in `<output>/report.json` and `<output>/results/`; output overrides do not relocate the replay cache or app log. Normal runs clear the results directory. An exit of 0 allows flaky/skipped outcomes; inspect report counts. Exit 1 is a test/setup failure, 2 is a config/usage/credential/policy error, 3 is infrastructure, 4 is internal, and 130 is interruption. Do not blindly retry config errors.

Use the native report rather than writing another JSON converter for a normal QA response. Full video and traces are diagnostic choices, not prerequisites for every audit. For an isolated fast audit, follow `fast-qa.md` and verify failure screenshots exist before using `--trace off`.

`npx e2e cache clear` destroys recordings; use only when invalidation is intended. `npx e2e@latest upgrade --dry-run` previews an upgrade. Use the project's supported upgrade command before adopting newer APIs.

## Full upstream references

All eight primary topics are bundled under `tester-army/e2e/references/`: setup, mcp, writing-tests, agent, running, debugging, explore and bug-bash. The generator and migration workflows are bundled alongside them. Apache-2.0 license, notice and source revision are in `tester-army/`.

Upstream feedback is optional external communication. Never send `e2e feedback` automatically; prepare a redacted dry-run and obtain explicit permission to send it.
