"""`honey rsi …` commands. The `rsi` skill runs these and renders the output."""
from __future__ import annotations

import json
import os
import time

from honey import paths
from honey.rsi import curate, review, store, text


def _print(obj, as_json):
    print(json.dumps(obj, indent=1, ensure_ascii=False) if as_json else obj)


def status(as_json=False):
    rows = curate.load()
    by = {}
    for b in rows:
        by[b.get("status")] = by.get(b.get("status"), 0) + 1
    txt, ids = curate.brief("claude", "")
    costs = store.read_jsonl(paths.path("costs.jsonl"))
    month = sum(c.get("usd") or 0 for c in costs if c.get("ts", "").startswith(time.strftime("%Y-%m")))
    ev_dir = paths.path("events")
    n_sessions = sum(len(fs) for _, _, fs in os.walk(ev_dir)) if os.path.isdir(ev_dir) else 0
    out = {"home": paths.home(), "bullets": by, "pending_review": len(review.pending()), "brief_chars": len(txt),
           "brief_ids": ids, "sessions_observed": n_sessions, "usd_this_month": round(month, 4)}
    if as_json:
        return _print(out, True)
    print(f"honey RSI · {out['home']}")
    print(f"  learnings: {by or 'none yet'}")
    print(f"  pending review: {out['pending_review']}   brief: {out['brief_chars']} chars ({len(ids)} lines)")
    print(f"  sessions observed: {n_sessions}   spend this month: ${out['usd_this_month']}")


def why(bid, as_json=False):
    b = curate.get(bid)
    if not b:
        raise SystemExit(f"no learning {bid}")
    if as_json:
        return _print(b, True)
    print(curate.line(b)[2:])
    print(f"  status={b['status']} scope={b['scope']} source={b['source']} severity={b.get('severity')}")
    print(f"  helpful={b.get('helpful',0)} harmful={b.get('harmful',0)} violations={b.get('violations',0)} sessions={len(b.get('sessions',[]))}")
    for e in b.get("evidence", [])[-5:]:
        print(f"  evidence {e.get('ts','')} {e.get('sid','')}: {e.get('q','')}")
    for p in b.get("prev", []):
        print(f"  was: WHEN {p['when']} → {p['then']}")


def list_review(as_json=False):
    review.audit()
    items = review.pending()
    proposed = [b for b in curate.load() if b.get("status") == "proposed"]
    if as_json:
        return _print({"proposals": items, "proposed_learnings": proposed}, True)
    if not items and not proposed:
        print("Nothing to review.")
    for p in items:
        print(f"[{p['id']}] tier {p['tier']} {p['type']}: {p['title']}\n    why: {p['rationale']}\n    fix: {p['fix']}")
    for b in proposed:
        print(f"[{b['id']}] learning: {curate.line(b)[2:]}  (sessions={len(b.get('sessions', []))})")


def _golden(b, action):
    store.append_jsonl(paths.path("golden.jsonl"), {"ts": text.now(), "id": b["id"], "source": b.get("source"), "decision": action,
                                                   "when": b["when"], "then": b["then"], "sessions": b.get("sessions", [])[:5]})


def decide(item_id, action, note=""):
    if item_id.startswith("b-"):
        with store.lock():
            rows = curate.load()
            b = next((r for r in rows if r["id"] == item_id), None)
            if not b:
                raise SystemExit(f"no learning {item_id}")
            if action in ("apply", "edit"):
                if action == "edit" and note:
                    b["when"], b["then"] = curate.split_when_then(text.redact(note, 400))
                    b["source"] = "user-stated"
                b["status"], b["activated"] = "active", b.get("activated") or text.now()
            elif action == "skip":
                b["status"] = "candidate"
            elif action == "never":
                b["status"] = "rejected"
                store.append_jsonl(paths.path("never.jsonl"), {"id": item_id, "text": f"{b['when']} {b['then']}"})
            curate.save(rows)
            _golden(b, action)
        print(f"{item_id} → {b['status']}")
        store.git_commit(f"rsi: {action} {item_id}")
        return
    p = store.read_json(paths.path("proposals", item_id + ".json"))
    if not p:
        raise SystemExit(f"no proposal {item_id}")
    kind, msg = p.get("type", ""), ""
    if action in ("apply", "edit"):
        if kind.startswith("instr_"):
            from honey.rsi import instructions
            if action == "edit" and note and p.get("edit"):
                p["edit"]["line" if p["edit"]["action"] == "add" else "replacement"] = text.redact(note, 400)
            msg = instructions.apply(p)
        elif kind == "skill_patch":
            from honey.rsi import patch
            msg = patch.accept(p)
        elif kind == "guard":
            from honey.rsi import guards
            guards.set_status(p["guard"], "active")
            msg = f"guard {p['guard']} active"
        elif kind == "upstream_port":
            from honey.rsi import patch
            res = patch.propose(p["skill"], "upstream", p.get("upstream", ""))
            msg = f"drafted eval-gated patch: {res}"
        else:
            msg = f"To apply: {p['fix']}"
    elif kind == "skill_patch":
        from honey.rsi import patch
        patch.discard(p)
    elif kind == "guard":
        from honey.rsi import guards
        guards.set_status(p["guard"], "rejected")
    p = review.decide(item_id, action, note)
    print(f"{item_id} → {p['status']}" + (f". {msg}" if msg else ""))
    store.git_commit(f"rsi: {action} {item_id}")


def session_end(key):
    """Detached after SessionEnd. Phase 1: refresh brief.md and commit; Phase 2 adds reflection."""
    from honey.rsi import reflect
    reflect.run_pending()


def main(args) -> int:
    import argparse
    ap = argparse.ArgumentParser(prog="honey rsi")
    sub = ap.add_subparsers(dest="cmd")
    for name in ("status", "review", "brief", "audit"):
        s = sub.add_parser(name)
        s.add_argument("--json", action="store_true")
    for name in ("why", "forget"):
        s = sub.add_parser(name)
        s.add_argument("id")
        s.add_argument("--json", action="store_true")
    s = sub.add_parser("decide")
    s.add_argument("id")
    s.add_argument("action", choices=["apply", "edit", "skip", "never"])
    s.add_argument("--text", default="")
    s = sub.add_parser("note")
    s.add_argument("text", nargs="+")
    s.add_argument("--scope", default="global")
    s = sub.add_parser("session-end")
    s.add_argument("key")
    sub.add_parser("catchup")
    for name in ("coach", "weekly", "radar", "costs", "golden", "guards"):
        s = sub.add_parser(name)
        s.add_argument("--dry-run", action="store_true")
    s = sub.add_parser("revert")
    s.add_argument("id")
    s = sub.add_parser("bootstrap")
    s.add_argument("--dry-run", action="store_true")
    s = sub.add_parser("reflect")
    s.add_argument("--session", required=True)
    a = ap.parse_args(args)
    if a.cmd in (None, "status"):
        status(getattr(a, "json", False))
    elif a.cmd == "review":
        list_review(a.json)
    elif a.cmd == "brief":
        txt, _ = curate.brief("claude", "")
        print(txt or "(no active learnings yet)")
    elif a.cmd == "audit":
        found = review.audit()
        if a.json:
            _print([{"id": p["id"], "title": p["title"], "status": p["status"]} for p in found], True)
        elif not found:
            print("No toolkit misfires found.")
        for p in [] if a.json else found:
            print(f"[{p['id']}] {p['status']}: {p['title']}")
    elif a.cmd == "why":
        why(a.id, a.json)
    elif a.cmd == "forget":
        print(f"{a.id} archived and added to never-list" if curate.forget(a.id) else f"no learning {a.id}")
        store.git_commit(f"rsi: forget {a.id}")
    elif a.cmd == "decide":
        decide(a.id, a.action, a.text)
    elif a.cmd == "note":
        b, merged = curate.add_note(" ".join(a.text), a.scope, "cli", "cli", paths.project_slug(os.getcwd()))
        print(f"saved {b['id']}: {curate.line(b)[2:]}" if b else f"not saved: {merged}")
        if b:
            store.git_commit(f"rsi: note {b['id']}")
    elif a.cmd == "session-end":
        session_end(a.key)
    elif a.cmd == "bootstrap":
        from honey.rsi import bootstrap
        return bootstrap.run(a.dry_run)
    elif a.cmd == "coach":
        from honey.rsi import coach
        print(coach.report())
    elif a.cmd == "weekly":
        from honey.rsi import weekly
        print(json.dumps(weekly.run(), indent=1, default=str))
    elif a.cmd == "radar":
        from honey.rsi import radar
        for p in radar.run(a.dry_run) or []:
            print(f"[{p.get('id', '')}] {p.get('title', p.get('file', ''))}")
    elif a.cmd == "costs":
        rows = store.read_jsonl(paths.path("costs.jsonl"))
        by = {}
        for c in rows:
            k = (c.get("ts", "")[:7], c.get("job"))
            by[k] = by.get(k, 0) + (c.get("usd") or 0)
        for (m, j), v in sorted(by.items()):
            print(f"{m} {j:10} ${v:.4f}")
        print(f"total ${sum(by.values()):.4f} over {len(rows)} calls")
    elif a.cmd == "guards":
        from honey.rsi import guards
        for g in guards.load():
            print(f"[{g['id']}] {g['status']:9} {g['action']:5} /{g['regex']}/ fired={g.get('fired', 0)}  {g['message']}")
    elif a.cmd == "golden":
        from honey.rsi import golden
        print(golden.run(a.dry_run))
    elif a.cmd == "revert":
        from honey.rsi import instructions
        print(instructions.revert(a.id))
    elif a.cmd == "catchup":
        from honey.rsi import reflect
        reflect.run_pending()
    elif a.cmd == "reflect":
        from honey.rsi import digest, reflect
        with store.lock():
            print(reflect.reflect_session(a.session, digest.load_events(a.session)))
            curate.maintain()
            curate.write_brief_md()
            store.git_commit(f"rsi: reflect {a.session}")
    return 0
