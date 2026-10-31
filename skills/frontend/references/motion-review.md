# Motion review and audit

Adapted from `emilkowalski/skills` at `a81dbca07f2217b7103e510c0f13f8d5b017afc9`, `skills/review-animations/{SKILL.md,STANDARDS.md}` and `skills/improve-animations/SKILL.md` (MIT). The shared values and construction rules live in [animation](animation.md); load it before recommending a curve, duration or spring.

Review a supplied diff or component; audit the current motion surface when the user asks for a roadmap. Both produce findings without changing application code. If implementation was also requested, send the accepted work through `plan`/`execute` and the normal `qa` proof path.

## 1. Map motion before judging it

Read the actual stack and version, easing/duration tokens, component primitives and their defaults. Inventory the elements in scope with their trigger, purpose, frequency, driver, animated properties and owner. Search CSS transitions/keyframes, Motion/GSAP/React Spring calls, animation hooks and gesture handlers, then trace the call sites to the user action. Include library defaults and inherited styles.

Separate application interactions from staged demos. A ten-second explanatory scene does not use the same duration budget as a menu opened dozens of times each day. Respect an explicit product decision; challenge it only with the observed regression it causes.

Done when: every scoped motion has an identified trigger, driver and purpose, or a named unknown that limits the review.

## 2. Review the experience

Check each element against these questions:

| Area | Check |
|---|---|
| Purpose/frequency | Does motion explain state, continuity or feedback? Remove unneeded keyboard/high-frequency decoration before tuning it. |
| Timing | Is the response immediate enough for the action? Use the budgets and easing rules in [animation](animation.md); report an intentional exception with its reason. |
| Origin | Does an anchored surface open from its trigger? A centered modal remains centered. Does an entry begin at a plausible scale rather than zero? |
| Interruption | Re-trigger, reverse and dismiss before completion. Toggles, toasts and drags must continue from current state, with no jump or stuck final style. |
| Cohesion | Do neighboring components use the same tokens and interaction language? A consumer celebration and an operational menu need different emphasis. |
| Accessibility | Test reduced motion, keyboard activation, focus retention/return, and hover on a coarse pointer. Removing movement must leave state and meaning perceivable. |
| Performance | Identify expensive properties or per-frame React work, then use [motion performance](motion-performance.md). A static risk is not a measured frame drop. |

Use the `qa` browser flow for live checks. Try opening/closing rapidly, a second action during entry/exit, slow data arrival and a large realistic content set. Missing browser/device access produces an explicit unverified item, not an approval of how it feels.

Done when: each finding has a real location and a failing interaction or a clearly labeled source-only risk; exemptions were checked against the actual component.

## 3. Prioritize and hand off

Prefer removal, then reduction, then easing/origin/interruption fixes; add decorative complexity last. A review uses this compact table:

| Location / action | Finding | Proposed change | Evidence |
|---|---|---|---|
| Actual file:line and trigger | The visible defect or source-only risk | Existing token or precise new value with its reason | Browser recording, trace, or code-only |

For an audit, group repeated instances by the shared component/token that owns the fix. Each plan item names the source location, existing behavior, target behavior and values, callers affected, acceptance checks and unresolved decisions. The plan must stand alone; “use the easing above” is not an implementation instruction. Include motion deliberately kept or rejected so a later agent does not reintroduce it.

Conclude with `needs changes`, `no source findings; live feel unverified`, or `verified in <recorded environment>`. Record browser, device and reduced-motion coverage separately. Approval requires the scoped interactions to have been exercised; it is never inferred from property names alone.

Done when: the report orders user-impacting failures first, every proposed fix has a check, and the verdict states the limits of its evidence.
