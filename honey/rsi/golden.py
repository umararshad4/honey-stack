"""Reflector golden suite: every /rsi review decision on a learning becomes a check that a changed reflector prompt
must still pass (applied → still proposed; never → not proposed). Run before accepting changes to RSI's own prompts."""
from __future__ import annotations

import json
import os

from honey import paths
from honey.rsi import reflect, store, text

HERE = os.path.dirname(os.path.abspath(__file__))


def run(dry: bool = False) -> str:
    gold = [g for g in store.read_jsonl(paths.path("golden.jsonl")) if g.get("decision") in ("apply", "edit", "never")]
    cases = []
    for g in gold:
        for key in g.get("sessions", []):
            d = store.read_json(paths.path("digests", key + ".json"))
            if d:
                cases.append((g, d["digest"]))
                break
    if not cases:
        return "No golden cases yet (they come from /rsi review decisions on reflected sessions)."
    if dry:
        return f"{len(cases)} golden cases; a run costs about ${0.002 * len(cases):.3f}."
    with open(os.path.join(HERE, "prompts", "reflector.md"), encoding="utf-8") as f:
        system = f.read()
    with open(os.path.join(HERE, "schemas", "reflection.schema.json"), encoding="utf-8") as f:
        schema = json.load(f)
    ok = 0
    for g, digest in cases[:20]:
        res, usd, eng = reflect.call_llm(system, digest, schema, 0.05)
        store.append_jsonl(paths.path("costs.jsonl"), {"ts": text.now(), "job": "golden", "engine": eng, "usd": usd, "ok": True})
        hit = any(text.jaccard(c.get("when", "") + " " + c.get("then", ""), g["when"] + " " + g["then"]) >= 0.4 for c in res.get("candidates", []))
        ok += hit == (g["decision"] != "never")
    return f"golden: {ok}/{min(len(cases), 20)} decisions reproduced"
