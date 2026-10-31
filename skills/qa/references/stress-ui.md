# Stress UI with realistic data

Adapted from `emilkowalski/skills` at `a81dbca07f2217b7103e510c0f13f8d5b017afc9`, `skills/break-ui/{SKILL.md,CATALOG.md}` (MIT). This extends `qa` with adversarial data, not a redesign. Keep the QA request's edit boundary: use existing fixture controls for inspection; create a dev-only harness only when that work is authorized.

## 1. Map fields and constraints

For every value rendered by the scoped component, record its source, type, frontend/backend limit and optionality. Include names, labels, badges, counts, timestamps, images and collection length. Read validators, API types, input limits and schema columns; a mismatch between an input limit and imported data is a finding. Mark an absent limit `unbounded` instead of inventing one.

Done when: every rendered data field has a source and a real constraint or explicit unknown.

## 2. Choose plausible boundary fixtures

Keep the same data shape and use the same boundary as normal data: existing fixture, component props, API stub or test mode. Do not edit CSS/markup to manufacture a failure. Use reserved domains for synthetic addresses and URLs, not real personal data.

| Kind | Useful cases |
|---|---|
| Names | `Aleksandra Wiśniewska-Kowalczyk`, `Jo`, a single-letter name, `王秀英`, `نور الهدى عبد الرحمن`, an emoji grapheme; optional name missing |
| Identifiers | A long realistic address at `example.com`, plus-addressing, a long document filename with an extension, UUID, a URL with a query |
| Labels | A long translated label such as `Benachrichtigungseinstellungen`, multiline content when the schema allows it, empty/whitespace, multiple badges |
| Numbers | 0, 1, large allowed values, negative values where supported, locale-specific separators and a value crossing 99→100 |
| Collections | Empty, one item, exactly a page, page+1, realistic maximum; duplicate display names with distinct IDs |
| Time | Now, boundary between relative/absolute display, future time, a timezone crossing midnight; invalid/missing values only through an allowed boundary |
| Media | Missing or failed avatar, slow image, unusually wide/tall image, transparent mark in dark mode |
| States | Loading→empty, delayed success, error→retry, permission-limited data, stale data during refresh |

Use a realistic maximum from the contract, not an arbitrary 5,000-character name or million-row payload. Test a schema-invalid input as validation coverage; do not present its absence from rendered UI as a layout defect. For an unbounded field, use a believable long value and report the missing bound separately.

Done when: fixtures exercise the applicable field classes and include empty/one/many states, with a reason for each boundary.

## 3. Drive the real component

Use the existing story/test route first. When a harness is authorized, keep a normal/worst-case selector inside a development-only route or story and switch at the data boundary. It must not become a production feature or change normal user data. For a read-only review with no fixture entry point, report the harness gap instead of changing the product.

Render the same component at the scoped desktop and mobile sizes, light/dark and relevant locales/direction. Check clipped text and diacritics, missing fallbacks, pluralization, overlapping actions, overflow, correct truncation with a discoverable full value, large-list interaction and focus order. Mix different extreme fields across rows so each failure can be distinguished. Use [mobile behavior](../../frontend/references/mobile.md) for hardware-dependent checks.

Done when: every applicable fixture state was driven through the real component, or its access/setup blocker is recorded.

## 4. Report before choosing a redesign

For each defect, show the exact fixture, source location, reproduction, observed result, screenshot/snapshot and smallest suggested fix. Distinguish an observed break from a source-only risk. Product choices such as wrap versus truncate remain explicit; do not silently redesign under a QA request.

When fixes are authorized, use the QA fix loop and re-run normal as well as worst-case data. Confirm the development harness is excluded from production and any temporary user/test state is cleaned without deleting evidence.

Done when: each finding has reproducible data and evidence, and each claimed fix passes both ordinary and boundary cases.
