# Load & stress testing

**Tools:** **k6** (JS/TS scripting, web dashboard `K6_WEB_DASHBOARD=true`, `k6 run`/`k6 cloud`) — default; Gatling (strong reports); Locust (Python, distributed); wrk2 (constant-rate latency); vegeta (`vegeta attack | vegeta report`); hey/oha for quick checks.

**Types:** smoke (sanity) → load (expected peak) → stress (beyond peak, find the breakpoint) → spike → **soak/endurance** (hours — catches leaks and slow resource growth short tests miss).

**Targets:** define throughput + latency at a percentile *before* testing, e.g. "p99 < 300ms at 2k rps".

**Percentiles — averages lie:** the mean hides the tail; one slow request per thousand ruins p99 but barely moves the mean. Report p50/p95/p99 (and max). Use coordinated-omission-aware tools (wrk2, k6) so the tail isn't under-reported. Tail latency is what users feel and it amplifies under fan-out.

**Finding the knee:** ramp load until latency rises sharply / throughput plateaus / errors appear — that inflection is capacity. Record it.

**Confirm before** testing anything live or shared — load tests can take down prod and its dependencies. Use a dedicated/staging env, coordinate with on-call, respect rate limits, never stress a third-party API.
