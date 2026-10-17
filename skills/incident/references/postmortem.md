# Blameless postmortem

## Structure
1. **Summary** — one paragraph.
2. **Impact** — duration, users/revenue affected, SLO/error-budget burn.
3. **Timeline** — timestamped detect → mitigate → resolve, with key findings.
4. **Root cause & contributing factors** — 5 Whys; incidents are usually multi-cause, not one villain.
5. **Detection** — how it was found, how fast, alert gaps.
6. **What went well / what didn't / where we got lucky.**
7. **Action items** — each with an owner, due date, and tracking ticket; prioritized.

## Blameless culture
Focus on systems and conditions, not individuals — people acted rationally on the information they had. Blame hides the truth and kills future honesty. Ask "what made this failure possible or easy?"

## Turn it into prevention
Regression tests for the specific failure; new/better alerts (symptom-based); guardrails/validation; runbook updates; automate the manual mitigation. Tie follow-through to error budgets — repeated budget burn should pause feature work for reliability.

## Prep that pays off
Runbooks per service (how to roll back, flip flags, fail over; linked dashboards); a clear on-call rotation and escalation path; actionable symptom-based alerts (not noise); chaos/game-days to rehearse failures and rollbacks before the real one.
