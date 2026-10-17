---
type: llm
---
PASS if it proposes a single consistent error envelope (ideally RFC 9457 / Problem Details, application/problem+json, or at least a stable machine-readable error `code`/`type` field clients branch on) AND warns against leaking internals (stack traces, SQL, hostnames) or enabling user-enumeration.
FAIL if it returns ad-hoc per-endpoint error shapes, tells clients to branch on human-readable message text, or says nothing about not leaking internal detail.
