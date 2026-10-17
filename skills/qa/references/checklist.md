# QA checklist

Read while exploring (step 3) and when sorting findings. Trimmed from garrytan/gstack 1.60.1.0 `qa/references/issue-taxonomy.md`, the Framework-Specific Guidance in `qa/SKILL.md`, and `qa/templates/qa-report-template.md` (MIT).

## Severity

| Severity | Meaning | Examples |
|---|---|---|
| critical | Blocks a core flow, loses data, or crashes the app | Submit shows an error page, checkout broken, data deleted without confirmation |
| high | A major feature is broken with no workaround | Search returns wrong results, upload fails silently, auth redirect loop |
| medium | Works, with a noticeable problem and a workaround | Load over 5 s, missing validation that submit survives, layout broken on mobile only |
| low | Cosmetic or polish | Typo, 1px misalignment, inconsistent hover state |

Fix order follows severity. Defer anything that can't be fixed from this repo (third-party widgets, infrastructure) and say why.

## What to look for

**Visual.** Overlapping or clipped elements, horizontal scroll, broken images, wrong z-index, inconsistent fonts or colors, animation jank, dark-mode or theme breaks.

**Functional.** Broken links, dead buttons, missing or bypassable validation, wrong redirects, state lost on reload or back, double-submit races, stale data.

**UX.** Dead ends, no loading feedback, interactions over 500 ms with no response, vague errors ("Something went wrong"), destructive actions without confirmation, patterns that differ between pages.

**Content.** Typos, placeholder or lorem ipsum text, truncation with no way to see the full value, wrong labels, unhelpful empty states.

**Performance.** Loads over 3 s, layout shift after load, janky scroll, oversized images, more than about 50 requests on one page. Measure with the `frontend` skill's `references/perf.md`.

**Console and network.** Uncaught exceptions, unintended 4xx or 5xx, CORS errors, mixed content, CSP violations, deprecation warnings.

**Accessibility.** Missing alt text, unlabeled inputs, controls unreachable by Tab, focus traps, missing or wrong ARIA, low contrast, content a screen reader can't reach.

## By framework

**Next.js**
- Hydration errors in the console ("Hydration failed", "Text content did not match").
- 404s on `_next/data` or RSC requests point to broken data fetching.
- Click links instead of loading URLs, so client-side routing gets exercised.
- Layout shift on pages with dynamic content.

**SPA (React, Vue, Angular)**
- Find navigation through the accessibility snapshot. A link list misses client-side routes.
- Navigate away and back: does the data refresh or go stale?
- Browser back and forward restore the right view.
- Watch the console during extended use for repeated errors or growing memory.

**Rails**
- CSRF token present in forms.
- Turbo and Stimulus transitions work, and flash messages appear and dismiss.

## Evidence per issue

- Interactive bug: a screenshot before the action, the action, a screenshot of the result, and the snapshot diff if the tool offers one.
- Static bug: one screenshot showing the problem, plus a description of expected versus actual.

## Report shape

```
## ISSUE-001: <short title>
Severity: high · Category: functional · URL: <url> · Viewport: 390x844
Expected: <what should happen>. Actual: <what happens>.
Repro: 1. <step> 2. <step> 3. Observe <symptom> (<screenshot path>)
Fix: verified | best-effort (<what wasn't checked>) | reverted | deferred (<why>)
Regression test: <path> | none (<reason>)
```

Close with a severity count table, the console errors seen with their first URL, and `QA: <n> issues, <m> fixed, <k> deferred.`
