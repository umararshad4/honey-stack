# Feature map contract

The canonical harness's `features/README.md` indexes one file per user-facing feature. A feature may contain several entry points; record them rather than letting one easy route stand in for all routes.

## Index

Write these fields with actual project values:

- **App and revision:** repository, app and source revision inspected.
- **Harness:** canonical skill path and the supported control adapter.
- **Launch model:** shared long-running instance, owned isolated instance, or isolated process per drive.
- **Evidence:** location independent of temporary profiles, data directories and process cleanup.
- **Features:** a linked file per mapped feature, with its entry points and coverage status.
- **Uncovered:** known features that this seed map does not yet cover.

Keep live run results in a separate evidence/run directory. The map describes how to prove behavior; it is not a permanent claim that today's build passes.

## Per-feature file

Use these four headings, filling them from source and an actual drive. Replace the adapter name with the project's real adapter, such as Playwright, the CLI test runner or HTTP.

### Sub-features

List the user-visible operations and their expected results, including relevant failure/empty states. State the observable side effect for each operation, such as an exported file containing the selected rows. Name the source entry points so later maintenance can trace them.

### How to get to it (user POV)

Give every supported user entry point: navigation from the app, a deep link, command or public request. List prerequisites such as roles, data, platform or entitlement and how to check them read-only. Secrets are referenced by environment variable or existing credential mechanism, not copied into the file.

### Driving it with the adapter

Write the exact steps and stable selectors/commands, then assertions on the visible result and side effects. Name evidence to retain for each step. A failing assertion must return failure or remain an explicit failure in the run report; an unavailable prerequisite must not be treated as success.

A repeated-click test uses real clicks; a persistence test reloads/reopens the real app; an export test reads the produced artifact. Directly assigning internal state proves only that assignment.

### Gotchas

Document observed prerequisites, state coupling, unsupported platforms, cleanup restrictions and known product regressions. If seed data does not permit a journey, name the missing data; do not rewrite the journey to skip the assertion.

## Coverage and maintenance

Maintain one row per mapped feature and entry point in the run evidence:

| Feature / entry point | Source traced | Live result | Evidence | Correction / blocker |
|---|---|---|---|---|

Use `pass`, `fail`, `verified-unreachable` or `unverified`. For `verified-unreachable`, record the attempted route and the evidenced prerequisite that prevents it. Use `unverified` when the attempt or evidence is missing. Only `pass` establishes that the journey worked.

Creation proves one mapped feature and names all unexercised features. Maintenance traces and drives every mapped feature, including re-driving journeys affected by harness changes. Neither claim covers features still listed as uncovered.
