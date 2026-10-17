"""/rsi bootstrap: seed RSI from what the user's agents already know. Everything lands as *proposed* for one review."""
from __future__ import annotations

import glob
import json
import os
import re
import time

from honey import paths
from honey.rsi import curate, review, signals, store, text

HERE = os.path.dirname(os.path.abspath(__file__))
MAX_USD = 0.25


def claude_memories() -> list:
    out = []
    for fp in sorted(glob.glob(os.path.join(paths.claude_dir(), "projects", "*", "memory", "*.md"))):
        if os.path.basename(fp) == "MEMORY.md":
            continue
        try:
            s = open(fp, encoding="utf-8").read()
        except OSError:
            continue
        m = re.search(r"^\s*type:\s*(\w+)", s, re.M)
        if not m or m.group(1) not in ("feedback", "user"):
            continue
        desc = re.search(r'^description:\s*"?(.*?)"?\s*$', s, re.M)
        body = s.split("---", 2)[-1].strip()
        proj = os.path.basename(os.path.dirname(os.path.dirname(fp)))
        out.append({"src": f"claude-memory:{proj}/{os.path.basename(fp)}", "project": proj, "type": m.group(1),
                    "text": text.redact((desc.group(1) if desc else "") + " — " + body, 700)})
    return out


def codex_memories() -> list:
    fp = os.path.join(paths.codex_dir(), "memories", "memory_summary.md")
    try:
        s = open(fp, encoding="utf-8").read()
    except OSError:
        return []
    m = re.search(r"^## User preferences\s*\n(.*?)(?=^## |\Z)", s, re.M | re.S)
    if not m:
        return []
    return [{"src": "codex-memory:memory_summary.md", "project": "codex", "type": "feedback", "text": text.redact(l.lstrip("- ").strip(), 500)}
            for l in m.group(1).splitlines() if l.strip().startswith("-")]


def history_baseline() -> dict:
    """Deterministic regex baseline over both prompt histories: signals per distinct week, top slash commands."""
    weeks, slash = {}, {}
    sources = [(os.path.join(paths.claude_dir(), "history.jsonl"), "display", "timestamp", 1000),
               (os.path.join(paths.codex_dir(), "history.jsonl"), "text", "ts", 1)]
    for fp, field, tsf, div in sources:
        for r in store.read_jsonl(fp):
            p = str(r.get(field) or "")
            ts = r.get(tsf) or 0
            wk = time.strftime("%G-W%V", time.gmtime(ts / div)) if ts else "unknown"
            w = weeks.setdefault(wk, {"prompts": 0, "correction": 0, "still": 0, "frustration": 0, "accept": 0})
            w["prompts"] += 1
            if p.startswith("/"):
                name = p.split()[0]
                days = slash.setdefault(name, set())
                days.add(time.strftime("%Y-%m-%d", time.gmtime(ts / div)) if ts else "?")
                continue
            for s in signals.classify(p):
                if s in w:
                    w[s] += 1
    top = sorted(((k, len(v)) for k, v in slash.items()), key=lambda x: -x[1])[:10]
    return {"weeks": dict(sorted(weeks.items())[-26:]), "slash_distinct_days": top}


def run(dry: bool = False) -> int:
    items = claude_memories() + codex_memories()
    base = history_baseline()
    found = review.audit()
    projects = {i["project"] for i in items}
    print(f"Sources: {len(items)} memory items from {len(projects)} projects, "
          f"{sum(w['prompts'] for w in base['weeks'].values())} prompts of history, {len(found)} toolkit findings.")
    if dry:
        print("Top slash commands by distinct days:", ", ".join(f"{k}×{n}" for k, n in base["slash_distinct_days"][:6]))
        print(f"Would make one consolidation call (≤${MAX_USD}) and queue up to 30 proposed learnings for /rsi review.")
        return 0
    prof = store.read_json(paths.path("profile.json"), {}) or {}
    prof["baseline"] = base
    store.write_json(paths.path("profile.json"), prof, sort=True)
    if not items:
        print("No memories to consolidate.")
        return 0
    from honey.rsi import reflect
    blocked = reflect.budget_block(reflect.engine()[0] or "")
    if blocked:
        print(f"Skipped consolidation: {blocked}.")
        return 1
    with open(os.path.join(HERE, "prompts", "consolidate.md"), encoding="utf-8") as f:
        system = f.read()
    with open(os.path.join(HERE, "schemas", "consolidate.schema.json"), encoding="utf-8") as f:
        schema = json.load(f)
    user = "\n".join(f"[{i}] ({it['src']}) {it['text']}" for i, it in enumerate(items))[:40000]
    result, usd, eng = reflect.call_llm(system, user, schema, MAX_USD, model="haiku")
    store.append_jsonl(paths.path("costs.jsonl"), {"ts": text.now(), "job": "bootstrap", "engine": eng, "usd": usd, "ok": True})
    added = 0
    with store.lock():
        rows = curate.load()
        for r in (result or {}).get("rules", [])[:30]:
            when, then = text.redact(r.get("when", ""), 120), text.redact(r.get("then", ""), 200)
            srcs = [items[i] for i in r.get("sources", []) if isinstance(i, int) and 0 <= i < len(items)]
            if not srcs or len(then) < 3 or text.injection_hit(when + " " + then) or curate.never_hit(when, then):
                continue
            if any(text.jaccard(b["when"] + " " + b["then"], when + " " + then) >= curate.MATCH for b in rows):
                continue
            scope = {"claude": "agent:claude", "codex": "agent:codex"}.get(r.get("scope"), "global")
            ev = [{"sid": s["src"], "ts": text.now(), "q": s["text"][:300], "quarantined": False} for s in srcs[:5]]
            b = curate.new_bullet(when, then, scope, "preference", "bootstrap", int(r.get("severity", 2)), ev, "proposed")
            b["projects"] = sorted({s["project"] for s in srcs})
            rows.append(b)
            added += 1
        curate.save(rows)
    store.git_commit(f"rsi: bootstrap (+{added} proposed)")
    print(f"Queued {added} proposed learnings (cost ${usd or 0:.4f} via {eng}). Next: /rsi review.")
    return 0
