---
name: qa
description: "Use to check a change in a real browser, QA a page or user flow, or when a UI change needs visual proof."
license: MIT
metadata:
  reviewed: "2026-10-18"
  sources: "garrytan/gstack 1.60.1.0 qa/SKILL.md.tmpl (test, fix, re-verify loop; regression test per fix; self-regulation), qa/SKILL.md (Modes: diff-aware; Workflow phases 2-5; Framework-Specific Guidance; Important Rules), qa/references/issue-taxonomy.md, qa/templates/qa-report-template.md; MCT (local) ~/.claude/MCT.md (Post-Task Verification, Strict Proof And Audit), ~/.claude/policies/automation-policy.json (postTaskVerification)"
---

# QA

Use the app the way a user would, in a real browser, and trust what the browser shows. Code tells you what should happen; the browser tells you what does.

A request to check or test produces a report and no code changes. Fix only when the user asked for fixes or the task is to make the flow work.

## 1. Pick the browser tool

Take the first one available in this session:

| Tool | Best for |
|---|---|
| Playwright MCP | Local flows, screenshots, viewport resizing, console and network reads |
| Chrome DevTools MCP | Network detail, performance traces, Lighthouse |
| claude-in-chrome, or the Codex browser plugin | The user's real Chrome profile: logged-in state, extensions, profile-dependent pages |
| The repo's Playwright or Cypress suite | A flow that's already scripted; the regression test in step 4 |

honey-stack ships no browser binary or daemon, so drive the browser through these tools. If none is available, say so and record the browser check as skipped with that blocker.

Done when: the tool has loaded the target page once.

## 2. Scope the run

- **Target.** Use the URL the user gave. Otherwise find the dev server port in the `dev` script or framework config and try it (commonly 3000, 5173 or 8080). If nothing is running, start the repo's dev script in the background. If that fails, ask for a URL.
- **Diff-aware by default.** List changed files with `git diff <base>...HEAD --name-only` plus uncommitted changes, then map them to what a user sees: route and page files to their URLs, components to the pages that render them, styles to the pages that load them, API handlers to the screens that call them (and call the endpoint directly too).
- **Nothing maps.** Smoke-test instead: the home page and the top five navigation targets, with console checks.
- **Intent.** Read the request, commit messages and PR body. QA checks that the change does what it was meant to, not only that nothing crashes.
- **Auth.** Use the credentials or cookie file the user provides. Write passwords as `<REDACTED>` in every step and report. For 2FA or a CAPTCHA, ask the user to complete it in the browser.

Done when: you have a list of URLs and flows, each tied to a changed file or to the stated intent.

## 3. Explore like a user

Run every flow at **1440x900** and **390x844**. On each page:

1. Load it, take a snapshot or screenshot, and read the console and failed network requests.
2. Use every control in the changed area. Each one does what its label says.
3. Submit forms empty, invalid, with long text and unicode, and twice quickly.
4. Navigate in and out: click links (client-side navigation), back and forward, deep link, reload. State that should persist survives a reload.
5. Reach the loading, empty, error and overflow states.
6. Tab through the controls. Focus is visible, Enter and Space activate, Escape closes overlays.
7. Try it logged out and as another role where access differs.

**Console errors count as failures,** even when the page looks right: uncaught exceptions, unintended 4xx or 5xx responses, hydration warnings, CORS and CSP violations.

Retry each bug once to confirm it reproduces. Spend depth on core flows (sign-up, checkout, the main dashboard, search) over secondary pages. For severity levels, issue categories and framework-specific checks, read `references/checklist.md`.

Done when: every flow on the list ran at both viewports and each finding has repro steps plus a screenshot or snapshot.

## 4. Fix loop

When fixing, work through issues in severity order:

1. **Locate.** Grep for the error text, component name or route. A cause that isn't obvious goes through the `debug` skill.
2. **Fix minimally.** Touch only files tied to this issue.
3. **Add a regression test** at the closest seam, matching the repo's existing test style. Logic or console errors get a unit or integration test. Broken forms and API flows get an integration test on the request and response. Interactive component bugs get a component or end-to-end test. Pure CSS fixes rely on the browser re-run. Where the seam allows, watch the test fail before the fix and pass after.
4. **Re-run in the browser.** Same flow, both viewports, console clean.
5. **Classify** the fix as verified, best-effort (state what couldn't be checked) or reverted (it made things worse: undo it and defer the issue).

Stop and report when a fix gets reverted, when a fix needs more than three files, or when fixes start touching unrelated code. Each is a sign the problem is bigger than a QA fix. If the user asked for commits, commit each fix separately through the `ship` skill.

Done when: each fixed issue passes in the browser and has a regression test, or a stated reason it has none.

## 5. Evidence and report

Write one evidence line per flow, from a run after the last edit:

```
browser: <tool> <url> <viewport> "<flow>" result=pass|fail
```

```
browser: playwright-mcp http://localhost:3000/pricing 1440x900,390x844 "toggle annual, CTA visible" result=pass
```

These lines feed the receipt and the `verify` skill's UI-proof check. Keep screenshot paths when the tool saves files, and show the user the screenshots that matter (on Claude Code, Read the image file).

Report the flows tested, issues by severity with repro steps, each fix with its status and test, and what was deferred and why. End with `QA: <n> issues, <m> fixed, <k> deferred.`

Done when: every flow in scope has an evidence line with its result.
