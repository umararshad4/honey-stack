# agent-browser for agent-driven QA

[agent-browser](https://github.com/vercel-labs/agent-browser) (Vercel Labs, Apache-2.0) is a CLI that drives Chrome over CDP. It returns compact accessibility snapshots with `@eN` refs. Use it when the agent itself steps through a page: ad-hoc "check this page" QA, bug repros, or exploring before you write an e2e test.

Don't use it in place of an existing e2e suite or a requested runner. Prepared tests run with no model in the loop and stay the regression proof.

## Why

On the honey task-desk benchmark ([report](../../../evals/agent-browser/reports/2026-11-14-agent-qa.md)), the same flow tied on wall time with Playwright MCP. The agent read 4.6× less text: about 270 tokens against 1,231. The saving shows up in model turns and context, not in browser speed.

## Use

Check for it with `command -v agent-browser`. If it's missing, use Playwright MCP or e2e. Install it only with the user's approval (`npm i -g agent-browser`), and load the version-matched guide with `agent-browser skills get core`.

```sh
S=qa-$$                                  # one session per task; parallel agents need distinct sessions
agent-browser open "$URL" --session $S
agent-browser snapshot -i --session $S   # interactive elements + refs; omit -i when text content matters
agent-browser click @e2 --session $S
agent-browser fill @e5 "Ship report" --session $S
agent-browser select @e6 High --session $S
agent-browser snapshot -i --session $S   # refs change after the DOM changes: re-snapshot before the next ref
agent-browser screenshot "$ARTIFACTS/state.png" --session $S
agent-browser close --session $S
```

- Take a fresh snapshot after any action that changes the DOM. Old refs can point at the wrong element.
- `snapshot -i` lists interactive elements only. Use a full `snapshot` or `get text <sel>` to assert visible text, status messages or row content.
- Keep the evidence: screenshot paths, the snapshot lines that prove each check, and the commands you ran. A completed walk-through isn't proof unless it shows the requested behavior.
- Always `close` the session, including after a failure.
