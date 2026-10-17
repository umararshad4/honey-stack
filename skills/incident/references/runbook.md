# Live investigation & roles

## Roles (separate them even solo)
- **Incident Commander** — owns the incident, decides, delegates; does not fix hands-on.
- **Comms Lead** — internal + external/status updates; shields responders from "any update?" pings.
- **Ops/SME** — investigates and executes mitigations.
- **Scribe** — timestamps every action and finding (invaluable for the postmortem).
- Solo: act as IC (decide + log) first, then ops; write the timeline as you go.

## Golden signals (Google SRE)
Latency (split success vs error latency), Traffic (demand), Errors (rate/ratio), Saturation (how full — CPU/mem/IO/queue/connections). RED = Rate/Errors/Duration for services; USE = Utilization/Saturation/Errors for resources.

## Safe on-prod investigation
Read-only: query replicas, logs, metrics, traces — not writes. Overlay the deploy timeline on error/latency dashboards. Don't restart/flush/mutate state on a hunch — you can destroy evidence or worsen the outage. Change one thing at a time and record it. No ad-hoc prod DB writes.

## Rollback vs forward-fix
Default rollback when a recent deploy correlates with onset and rollback is safe. Forward-fix only when rollback is impossible (irreversible DB migration, data already written in the new shape) or clearly riskier than a tiny known patch. A rollback across an incompatible schema migration can itself lose data — check first.
