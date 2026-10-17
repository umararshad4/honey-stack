# SLOs & alerting

**Definitions:** SLI = a measured indicator (% requests < 300ms, success rate). SLO = a target for the SLI over a window (99.9% over 30 days). Error budget = 1 − SLO (0.1%) = allowed failure, which governs release risk.

**Alert on symptoms, not causes.** Page on user-facing SLO burn (latency/error-rate/availability), not on "CPU 90%" — high CPU with healthy latency isn't an incident; low CPU with broken requests is. Cause-metrics belong on dashboards for diagnosis.

**Burn-rate alerts:** alert when the error budget is burning too fast. Use **multi-window, multi-burn-rate** (Google SRE): fast-burn (≈14.4× over 1h → page) + slow-burn (≈3× over 6h → ticket). Catches both outages and slow degradation without flapping.

**Avoid alert fatigue:** every page must be actionable and urgent; demote the rest to tickets/dashboards; dedupe/group; auto-resolve; prune regularly. Link a runbook from each alert. Track alert volume as a health metric.
