# Larger QA comparison — 2026-11-01

Six setup-heavy behaviors run at 1440×900 and 390×844 (12 cases): search narrowing, bulk completion, empty/one-match search, check/uncheck, dialog cancel, and case-insensitive search. Each case first creates 10–25 tasks (×1) or 40–100 tasks (×4); the acceptance actions are identical in every workflow and always use the real UI. Only fixture creation differs: older QA and e2e only use the form, while WebMCP modes use `create_task` through `webmcpBatch`.

| Workflow | ×1 median (204 records) | ×4 median (816 records) | Growth |
|---|---:|---:|---:|
| Older QA (serial, raw Playwright) | 17.28s | 58.03s | 3.4× |
| e2e only (4 workers, new browser path) | 7.04s | 21.11s | 3.0× |
| e2e + WebMCP, previous flow | 6.31s | 6.75s | 1.07× |
| **e2e + WebMCP, new flow** | **2.40s** | **2.67s** | 1.11× |

- At ×4, the new flow is **21.7× faster than older QA**, **7.9× faster than e2e only** and **2.5× faster than the previous WebMCP flow**.
- Form-based setup grows almost linearly with data; tool-based setup barely moves. This is where WebMCP pays off, unlike the original 24-case suite, which seeds only three records per viewport.
- CPU per run at ×4: older 30.9s, e2e only 57.1s, previous WebMCP 21.1s, new 11.0s.
- 40/40 measured runs qualified: 12 passing cases, every seeded row count and behavior witness checked, 0 calls in form-setup modes, and exactly 204 (×1) or 816 (×4) native tool calls per WebMCP run.

Ranges: ×1 older 17.20–17.48s, e2e 6.81–7.45s, previous 5.95–6.70s, new 2.27–2.48s; ×4 older 57.98–58.26s, e2e 20.17–21.81s, previous 6.29–6.85s, new 2.56–2.75s.

Protocol: same machine, fixture app, browser builds and launchers as the [third improvement](2026-11-01-fast-qa-v3.md). Older QA and e2e only use the new browser path; the previous flow uses the v2 launcher. One excluded warm-up and five measured rounds per tier, mode order rotated, commands sequential, 5s untimed cool-down. These cases contain no seeded defects, so this measures the passing path; defect detection was covered by the 24-case suite. Full data: [JSON](2026-11-01-fast-qa-large.json). Sources and raw runs: the `large-src/`, `large-x1/` and `large-x4/` directories under the evidence root.
