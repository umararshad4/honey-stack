# Engineering review

Distilled from garrytan/gstack `plan-ceo-review` (Prime Directives) and `plan-eng-review` (review sections, required outputs; MIT, Garry Tan). Apply to every new codepath in the plan; add each test it surfaces to the task that owns the code.

## Prime directives

1. **No silent failures.** Every failure is visible to the system, the team, or the user. A failure that can happen silently is a critical defect in the plan.
2. **Every error has a name.** Not "handle errors": the specific error, what triggers it, what catches it, what the user sees, and which test covers it. A catch-all handler is a finding.
3. **Every data flow has four paths.** The happy path plus three shadow paths: nil input, empty or zero-length input, and an upstream error. Trace all four.
4. **Every interaction has edge cases.** Double submit, navigating away mid-action, slow connection, stale state, the back button.
5. **Observability is scope.** New codepaths get the logs, metrics or traces someone needs at 3am.
6. **Deferred work is written down.** Under "Not in scope" with a one-line reason, or it's lost.
7. **Diagram what isn't obvious.** A short ASCII diagram for any new data flow, state machine or pipeline.
8. **Deployments aren't atomic.** Plan for partial states, rollback, and flags where a half-shipped change can hurt.

## Review checklist

- **Architecture**: component boundaries, coupling, data flow bottlenecks, single points of failure, auth and data-access boundaries.
- **Code quality**: module fit, repetition, error handling, over- or under-engineering against the ladder.
- **Tests**: every new codepath and branch has a test at the right seam; tests assert behavior users can observe.
- **Performance**: N+1 queries, unbounded memory, missing caches, slow paths on hot routes.

## Failure modes table

For each new codepath, one realistic production failure:

| Codepath | Failure (timeout, null, race, stale data) | Test? | Handled? | User sees |
|---|---|---|---|---|

No test, no handling, and silent to the user is a **critical gap**: add the test and the handling to the owning task.

## Required sections in the plan

- **What already exists**: code that partly solves sub-problems, and whether the plan reuses it.
- **Not in scope**: considered and deferred, one line each with the reason.
- **Parallel lanes** (only with two or more independent workstreams): a table of step, modules touched, depends on. Steps sharing a module go in one lane, sequentially. `execute` reads this to decide what may run in parallel.
