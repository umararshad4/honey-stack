# Test levels & doubles

## Levels (push each case to the lowest that still catches the bug)
- **Unit** — one function/class isolated; fast, deterministic; for logic, algorithms, pure functions.
- **Integration** — several real components (service + real DB/queue via testcontainers); catches wiring, serialization, SQL, config. Best confidence per cost — put most feature-level edge cases that cross a boundary here.
- **E2E** — whole system through the real UI/API; few, for critical journeys only; slow/flaky (overlaps `qa`).
- **Contract (Pact)** — consumer-driven: the consumer records expected request/response to a pact file; the provider replays it against its real implementation. `can-i-deploy` gates deploys; pending pacts stop new contracts breaking provider builds. Replaces slow full-stack integration for microservice API compatibility.

Shapes: the **pyramid** (wide unit base) suits logic-heavy backends; the **testing trophy** (wide integration middle) suits frontend/full-stack. Both are heuristics — integration is usually the sweet spot for feature edge cases.

## Doubles (Meszaros)
- **Dummy** — passed but unused. **Stub** — returns canned answers. **Fake** — a working lightweight impl (in-memory DB). **Spy** — a stub that records calls. **Mock** — pre-set expectations; fails if they don't happen.
- **Mock vs real**: mock slow/nondeterministic/external things (3rd-party APIs, time, randomness, network). Prefer real or fakes for code you own (testcontainers). Over-mocking tests your mocks and passes when the real integration is broken. Rule: don't mock what you don't own — wrap it in an adapter and fake the adapter.

## Determinism (non-negotiable)
No `sleep` — wait on conditions/events or use fake timers. Inject the clock (never call `now()` directly) and randomness (fixed seed in CI). Control IDs/UUIDs and ordering. Fresh test data per test — no shared mutable state — to kill order-dependence and flakiness.
