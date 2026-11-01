# GitHub backlog repair

Source: all 15 open issues in umararshad4/honey-stack, read on 2026-11-01; all had zero comments. No competing open PRs. Reports are RSI suggestions, not confirmed defects. Base: 138720d (v0.16.0).

## Plan and acceptance

- [x] Gate lane: #9/#11/#21/#22. Preserve inspection boundaries, accept explicit action follow-ups, block at most once per turn, and retain useful evidence through unrelated read failures. Verify with hook-level task tests.
- [x] RSI lane: #13–16/#18. Filter delegated wrappers, derive clustering keywords from source evidence, and expose actual applied changes. Verify with coach and continuous/autonomy tests.
- [x] Guidance lane: #6/#8/#10/#12/#17. Distinguish questions from action requests, explain rule provenance, document sandbox recovery, lead with answers, and avoid workflow loading for lookups. Verify packaging and hook bootstrap; stage model eval cases with explicit proof limits.
- [x] Combined verification and review: full Python suite, release consistency, diff whitespace, budget check, and model eval where available.
- [ ] Ship verified changes through a PR; merge only after GitHub checks pass.

## Rulings and limits

- #7: no reproduced runtime deletion defect. Response modes already preserve unrelated configuration. Added guidance to preserve learned preferences across style changes. Keep the report open until a deletion reproduction exists; do not alter explicit forget semantics.
- #14/#15: current code already rejects generic continuations and attachment boilerplate. Existing regression checks pass; no new skills are justified by these reports.
- #9/#21: historical reports lack enough evidence to reproduce the exact sessions. Current code does permit repeated stop blocks through separate flags and mutation resets; regression coverage targets that confirmed mechanism.
- #11: unrelated failed read commands already preserve successful verification. Added hook-level coverage; this does not promise every environment failure is harmless.
- #22: current parser accepts the historical pasted action request; explicit follow-ups such as "do it" were still misclassified. Fix that bounded case, retaining inspect mode for bare "continue".
- #6/#8/#10/#12/#17: instruction changes and fixture checks establish guidance, not guaranteed future model adherence. Browser-host sandbox policy itself is not modified.

Review: traced both gate callers and prompt resets, applied-change status consumers, and quote-derived clustering. No new dependencies or public payloads. The explanatory ship-question model baseline already passed; its new case is a regression guard, not reproduction of the historical failure.

Verification: focused gate, runner, coach, continuous, mode and packaging tests passed. Initial combined run caught oversized guidance (bootstrap and description budget); both were reduced and their checks passed. Full final run and GitHub CI are the delivery gates. Installed doctor reports Codex hook trust review required and stale cache; no installed-runtime claim is made.

No private session quotes, personal preferences or local proposal payloads are published. Runtime source fixes do not prove installed-client or live hook delivery.
