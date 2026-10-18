# End-to-end tests

How to author durable e2e tests, distilled from the e2e framework's guidance (tester.army/e2e). The principles are tool-neutral; apply them whether you drive Playwright, Cypress, or an agentic e2e runner.

## Split each test by how brittle the step is

Pick the mode per step, not per test:

- **Deterministic (code: locators + `expect`)** for anything with an exact answer — a value, a count, a visible control, a URL. These need no model and never flake on intent.
- **Agent / natural-language goals** only for the parts that break most under scripting: multi-step wizards, flows whose copy changes, exploratory paths. If a test has no such part, it needs no agent at all.
- Keep exact checks in code with `expect`. Don't ask an agent to assert a value it can read deterministically — it's slower, costs tokens, and can take a different path each run.

## Selectors

- Match by **role, then accessible name, then test id** — in that order of preference. Query the rendered screen (`screen.getByRole`, `getByText`, `getByTestId`), not brittle CSS/XPath paths.
- Names match **exactly** by default: `Save` must not also match `Save as draft`. Scope or use the full name.
- React Native `testID` maps to `getByTestId` on both platforms.
- Verify a locator resolves to exactly one element **before** writing the assertion around it. A test built on an ambiguous or absent locator is a false green waiting to happen.
- Prefer user-facing queries (role/name/text) over test ids; reach for a test id only when there's no accessible handle.

## Caching agent steps (if the runner supports it)

- A passing agent action is recorded only **after a later check verifies it produced the intended effect** — never cache an unverified step.
- Replays use the recorded actions with no model call, re-matching controls by role/name/test id/context, and re-confirm the same effect. If the app changed, the agent resumes from the current screen rather than failing blindly.
- Assertions, wait-fors and extractions always run **live** and are never replayed.
- Commit the cache dir so CI replays the same recordings; CI treats the cache as read-only and records nothing new.

## Explore, then pin as regression tests

- Scout a new feature by exploring it (one run per area/persona); run several in parallel for a bug bash.
- Turn the flows that matter into regression tests — exploration finds, regression tests hold the line.
- **Reproduce every finding with a repro test.** Count it a confirmed bug only when that test fails for the reported reason. A finding without a failing test is a hypothesis, not a bug.

## Secrets

- Fill credentials by name at run time; never hard-code them in the test. Write them as `<REDACTED>` in steps and reports, and redact them from any model input.

## CI

- Run with one retry; a test that only passes on retry is flaky — fix it, don't accept it.
- Post a single summary per run (replayed / handed-off / missed / failed counts).

## Debugging a failure

- Start from the structured report (failing step, screenshots, trace, console/network), not from re-running blind.
- A cause that isn't obvious from the report goes through the `debug` skill — root cause before the fix, same as any bug.

## Scope

e2e covers whole user flows in a real browser/app. It does **not** replace component tests (those live at the unit/integration seam the `test-design` and `tdd` skills own) or static checks. Use the right level for the thing under test.
