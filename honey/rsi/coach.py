"""/rsi coach: evidence-only progress map, skill table and suggestions. No LLM; every claim carries n."""
from __future__ import annotations

import glob
import os
import re
import time

from honey import paths
from honey.rsi import curate, review, signals, store, text

DELEGATED_REQUEST = re.compile(
    r"^\s*(?:amcp\s+command\s+delegated\b|"
    r"(?:act(?:\s+as)?|you\s+are)\b[^\n.]{0,100}\b(?:sub-agent|subagent|worker\s+agent)\b)", re.I)

MIN_N = 5
PATCH_MIN_INV, PATCH_NEG_RATE, PATCH_MIN_NEG, DESC_FIX_MIN = 4, 0.4, 2, 2


def _weeks(n_back: int) -> list:
    return [time.strftime("%G-W%V", time.gmtime(time.time() - 7 * 86400 * i)) for i in range(n_back)]


def _sum(weekly: dict, weeks: list) -> dict:
    tot = {}
    for k, w in weekly.items():
        if k.split(":")[0] in weeks:
            for f, v in w.items():
                tot[f] = tot.get(f, 0) + v
    return tot


def _rate(tot, f, per="user_turns", scale=10):
    d = tot.get(per, 0)
    return round(scale * tot.get(f, 0) / d, 2) if d else None


def skill_status(c: dict) -> str:
    inv = c.get("inv_user", 0) + c.get("inv_model", 0)
    pos, neg = c.get("pos", 0) + c.get("worked", 0), c.get("neg", 0) + c.get("failed", 0)
    if c.get("misfire", 0) + c.get("missed", 0) >= DESC_FIX_MIN:
        return "desc-fix"
    if inv >= PATCH_MIN_INV and neg >= PATCH_MIN_NEG and neg / max(1, pos + neg) >= PATCH_NEG_RATE:
        return "patch-candidate"
    return "watch" if neg else "ok"


def request_clusters(days: int = 30) -> list:
    """Repeated asks with no skill invoked: keyword sets (Jaccard ≥ .5) seen ≥3× across ≥2 sessions."""
    cutoff = time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime(time.time() - days * 86400))
    asks = []
    for fp in glob.glob(paths.path("events", "*", "*.jsonl")):
        rows = store.read_jsonl(fp)
        skill_turns = {r.get("t") for r in rows if r.get("e") == "skill"}
        for r in rows:
            quote = r.get("q", "")
            keywords = text.keywords(quote)
            if (r.get("e") == "prompt" and r.get("origin") == "user" and not r.get("xc")
                    and r.get("ts", "") >= cutoff and r.get("t") not in skill_turns
                    and quote and signals.origin(quote) == "user" and not text.injection_hit(quote)
                    and len(keywords) >= 3 and not DELEGATED_REQUEST.search(quote)
                    and not {"continue", "accept"} & set(signals.classify(quote))
                    and not quote.strip().lower().startswith(("[attached image", "[attached file", "attached image:", "attached file:"))):
                sid = os.path.basename(fp)[:-6]
                evidence = {"sid": sid, "ts": r["ts"], "q": text.redact(r.get("q", ""), 300),
                            "event": "prompt", "origin": r.get("origin"), "quarantined": bool(r.get("xc"))}
                asks.append((sid, set(keywords), evidence))
    clusters = []
    for sess, kw, evidence in asks:
        for c in clusters:
            if len(kw & c["kw"]) / len(kw | c["kw"]) >= 0.5:
                c["n"] += 1
                if sess not in c["sessions"]:
                    c["evidence"].append(evidence)
                c["sessions"].add(sess)
                c["kw"] &= kw if len(c["kw"] & kw) >= 2 else c["kw"]
                break
        else:
            clusters.append({"kw": set(kw), "n": 1, "sessions": {sess}, "evidence": [evidence]})
    return sorted((c for c in clusters if c["n"] >= 3 and len(c["sessions"]) >= 2), key=lambda c: -c["n"])[:5]


def report(weeks: int = 4) -> str:
    prof = store.read_json(paths.path("profile.json"), {}) or {}
    weekly = prof.get("weekly", {})
    cur, prev = _sum(weekly, _weeks(weeks)), _sum(weekly, _weeks(2 * weeks)[weeks:])
    out = [f"# honey RSI coach — last {weeks} weeks vs the {weeks} before"]
    n = cur.get("sessions", 0)
    out.append(f"\n## Headline (sessions n={n}, previous n={prev.get('sessions', 0)})")
    if n < MIN_N:
        out.append(f"Insufficient data: {n} observed sessions (need {MIN_N}). Keep working normally; RSI is still collecting.")
    else:
        for f, label in (("correction", "corrections"), ("still", "'still broken'"), ("frustration", "frustration"),
                         ("false_done", "done-claims followed by behavior feedback"), ("unneeded_q", "questions answered with just 'continue'")):
            a, b = _rate(cur, f), _rate(prev, f)
            trend = "" if b is None or a is None else (" ↓ lower" if a < b * 0.7 else " ↑ higher" if a > b * 1.3 else " → flat")
            out.append(f"- {label}: {a} per 10 turns (was {b}){trend}")
        out.append(f"- tool failures: {_rate(cur, 'tool_fail', 'sessions', 1)} per session; compactions: {_rate(cur, 'compact', 'sessions', 1)} per session")
        out.append(f"- acceptance ('perfect', 'lgtm'…): {_rate(cur, 'accept')} per 10 turns. Read corrections together with this: fewer corrections and fewer acceptances can mean you stopped bothering.")
    out.append("\n## Tool observations")
    calls, completed = cur.get("eff_tool_calls", 0), cur.get("eff_completed_calls", 0)
    if calls:
        out.append(f"- completed tool calls: {completed}/{calls}; unknown results: {max(0, calls - completed)}/{calls}")
        out.append(f"- failed calls: {cur.get('eff_failed_calls', 0)}/{completed} completed calls")
        out.append(f"- repeated reads: {cur.get('eff_repeated_reads', 0)}/{cur.get('eff_read_calls', 0)} completed reads; "
                   f"repeated checks: {cur.get('eff_repeated_checks', 0)}/{cur.get('eff_check_calls', 0)} completed checks")
        out.append(f"- reported duration: {cur.get('eff_duration_ms', 0):g} ms across {cur.get('eff_duration_samples', 0)} "
                   f"of {completed} completed calls")
    else:
        out.append("- No tool result metrics observed yet.")
    out.append("These are observations, not a speedup measurement. Repeated reads/checks can be necessary; "
               "fingerprints reset after mutations and task changes. Missing durations and hook events are not estimated.")
    doms = prof.get("domains", {})
    grow = sorted((k for k, d in doms.items() if d.get("growing", 0) >= 2 and d.get("growing", 0) > d.get("repeating", 0)), key=lambda k: -doms[k]["growing"])
    rep = sorted((k for k, d in doms.items() if d.get("repeating", 0) >= 3), key=lambda k: -doms[k]["repeating"])
    out.append("\n## Where you're growing")
    out += [f"- {k}: improving in {doms[k]['growing']} sessions (repeating in {doms[k].get('repeating', 0)})" for k in grow[:5]] or ["- Not enough evidence yet."]
    out.append("\n## Where mistakes repeat")
    out += [f"- {k}: the same class came up in {doms[k]['repeating']} sessions" for k in rep[:5]] or ["- Nothing repeated ≥3 times."]
    led = curate.load()
    viol = sorted((b for b in led if b.get("status") == "active" and b.get("violations", 0) >= 2), key=lambda b: -b["violations"])
    for b in viol[:3]:
        out.append(f"- rule {b['id']} keeps being violated ({b['violations']}× of {b.get('relevant', 0)} relevant): \"{b['then'][:90]}\" → candidate for an enforced guard (Tier 3)")
    sc = store.read_json(paths.path("scorecards.json"), {}) or {}
    out.append("\n## Skills")
    if sc:
        out.append("| skill | uses | ✓ | ✗ | uncertain | misfire/missed | status |\n|---|---|---|---|---|---|---|")
        for name, c in sorted(sc.items(), key=lambda kv: -(kv[1].get("inv_user", 0) + kv[1].get("inv_model", 0))):
            out.append(f"| {name} | {c.get('inv_user', 0) + c.get('inv_model', 0)} | {c.get('pos', 0) + c.get('worked', 0)} | "
                       f"{c.get('neg', 0) + c.get('failed', 0)} | {c.get('uncertain', 0)} | "
                       f"{c.get('misfire', 0)}/{c.get('missed', 0)} | {skill_status(c)} |")
        out.append("Feedback records may include both observation and reflection of one turn. Uncertain records do not count toward patch candidates.")
    else:
        out.append("- No skill use observed yet.")
    sugg = []
    for c in request_clusters():
        proposal = review.add(2, "skill_new", f"New skill for repeated ask: {' '.join(sorted(c['kw'])[:5])}",
                   f"{c['n']} asks across {len(c['sessions'])} sessions with no skill invoked.",
                   "Draft it with the write-skill skill, plus a should-fire eval from these asks.",
                   c["evidence"], "cluster:" + ",".join(sorted(c["kw"])))
        if proposal.get("status") == "pending":
            proposal["evidence"] = c["evidence"][:5]
            store.write_json(paths.path("proposals", proposal["id"] + ".json"), proposal)
            sugg.append(f"You asked for \"{' '.join(sorted(c['kw'])[:6])}\" {c['n']}× across {len(c['sessions'])} sessions with no skill helping → "
                        "a small dedicated skill could make that one step (proposal queued).")
    for name, c in sc.items():
        st = skill_status(c)
        if st in ("patch-candidate", "desc-fix"):
            sugg.append(f"`{name}` is {st} ({c.get('neg', 0) + c.get('failed', 0)} bad outcomes, {c.get('misfire', 0)} misfires, "
                        f"{c.get('missed', 0)} missed) → the weekly job drafts an eval-gated patch for /rsi review.")
    base = prof.get("baseline", {}).get("slash_distinct_days", [])
    bd = dict((k, v) for k, v in base)
    if bd.get("/model", 0) + bd.get("/effort", 0) >= 20:
        sugg.append(f"You switch /model ({bd.get('/model', 0)} days) and /effort ({bd.get('/effort', 0)} days) often → set per-task defaults "
                    "(e.g. complex investigations on opus/high, quick fixes on sonnet) instead of switching by hand.")
    if bd.get("/usage", 0) >= 10:
        sugg.append(f"You check /usage on {bd['/usage']} distinct days → a rate-limit segment in the statusline would save the round-trip.")
    if cur.get("unneeded_q", 0) >= 3:
        sugg.append(f"The agent asked {cur['unneeded_q']} questions you answered with just 'continue'. "
                    "Review whether permission was already granted; the count alone does not establish unnecessary blocking.")
    out.append("\n## Suggestions")
    out += [f"{i}. {s}" for i, s in enumerate(sugg[:3], 1)] or ["- None with enough evidence yet."]
    hold = [w for w in weekly.values() if w.get("holdout")]
    out.append("\n## RSI itself")
    by = {}
    for b in led:
        by[b.get("status")] = by.get(b.get("status"), 0) + 1
    decided = [p for p in review.all_proposals() if p.get("status") in ("applied", "skipped", "never")]
    acc = sum(p["status"] == "applied" for p in decided)
    costs = store.read_jsonl(paths.path("costs.jsonl"))
    month = sum(c.get("usd") or 0 for c in costs if c.get("ts", "").startswith(time.strftime("%Y-%m")))
    out.append(f"- learnings: {by or 'none'}; review acceptance {acc}/{len(decided)}; spend this month ${month:.3f}")
    prec = precision()
    if prec:
        out.append("- learning precision by source (applied / decided): " + ", ".join(f"{k} {v[0]}/{v[1]}" for k, v in prec.items()))
    if hold:
        out.append(f"- holdout sessions: {len(hold)}")
    txt = "\n".join(out)
    store.write_text(paths.path("coach", time.strftime("%G-W%V") + ".md"), txt + "\n")
    return txt


def precision() -> dict:
    out = {}
    for g in store.read_jsonl(paths.path("golden.jsonl")):
        s = g.get("source", "?")
        a, n = out.get(s, (0, 0))
        out[s] = (a + (g.get("decision") in ("apply", "edit")), n + 1)
    return out
