"""Weekly RSI job (detached; at most once per 7 days): curate, graduate, audit instructions, propose guards and skill
patches, run the upstream radar, write the coach report. Every paid step checks the budget first."""
from __future__ import annotations

import time

from honey import paths
from honey.rsi import coach, curate, guards, instructions, patch, radar, reflect, review, store


def run() -> dict:
    out = {}
    with store.lock(blocking=False) as got:
        if not got:
            return {"skipped": "locked"}
        steps = (("maintain", curate.maintain), ("audit", lambda: len(review.audit())),
                 ("graduate", lambda: len(instructions.graduate())), ("instructions", lambda: len(instructions.llm_audit())),
                 ("guards", lambda: len(guards.propose_all())), ("patches", patch.run_weekly), ("radar", lambda: len(radar.run())))
        for name, fn in steps:
            try:
                out[name] = fn()
            except Exception as e:  # one failing step must not stop the rest
                out[name] = f"error: {str(e)[:160]}"
        coach.report()
        curate.write_brief_md()
        jobs = store.read_json(paths.path("state", "jobs.json"), {}) or {}
        store.write_json(paths.path("state", "jobs.json"), dict(jobs, weekly=time.time(), weekly_result=str(out)[:2000]))
        store.git_commit("rsi: weekly")
    reflect.run_pending()
    return out
