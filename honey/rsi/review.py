"""Proposal queue for /rsi review, the pending notice, and the deterministic toolkit audit (misfire detectors)."""
from __future__ import annotations

import hashlib
import json
import os
import re
import time

from honey import paths
from honey.rsi import store, text

NOTICE_HOURS = 24


def _dir() -> str:
    return paths.path("proposals")


def all_proposals() -> list:
    d = _dir()
    try:
        names = sorted(n for n in os.listdir(d) if n.endswith(".json"))
    except FileNotFoundError:
        return []
    return [p for p in (store.read_json(os.path.join(d, n)) for n in names) if p]


def pending() -> list:
    return [p for p in all_proposals() if p.get("status") == "pending"]


def add(tier: int, kind: str, title: str, rationale: str, fix: str, evidence: list, fingerprint: str) -> dict:
    """Queue a proposal unless the same finding is already queued, skipped or refused."""
    fp = hashlib.sha1(fingerprint.encode()).hexdigest()[:12]
    for p in all_proposals():
        if p.get("fp") == fp and p.get("status") != "applied":
            return p
    pid = "p-" + time.strftime("%Y%m%d") + "-" + fp[:6]
    p = {"id": pid, "fp": fp, "tier": tier, "type": kind, "status": "pending", "title": title[:100],
         "rationale": rationale[:400], "fix": fix[:400], "evidence": evidence[:5], "created": text.now(), "decided": None, "note": ""}
    store.write_json(os.path.join(_dir(), pid + ".json"), p)
    return p


def decide(pid: str, action: str, note: str = "") -> dict:
    fp = os.path.join(_dir(), pid + ".json")
    p = store.read_json(fp)
    if not p:
        raise SystemExit(f"no proposal {pid}")
    status = {"apply": "applied", "edit": "applied", "skip": "skipped", "never": "never"}.get(action)
    if not status:
        raise SystemExit("action must be apply|edit|skip|never")
    p.update(status=status, decided=text.now(), note=text.redact(note, 400))
    store.write_json(fp, p)
    if status == "never":
        store.append_jsonl(paths.path("never.jsonl"), {"ts": text.now(), "id": pid, "text": p["title"]})
    return p


def notice() -> str:
    """One line at SessionStart, at most once per NOTICE_HOURS, only when something is pending."""
    n = len(pending())
    if not n:
        return ""
    sf = paths.path("state", "notice.json")
    last = (store.read_json(sf, {}) or {}).get("ts", 0)
    if time.time() - last < NOTICE_HOURS * 3600:
        return ""
    store.write_json(sf, {"ts": time.time()})
    return (f"honey RSI: {n} item{'s' if n > 1 else ''} waiting in /rsi review. Mention this once, in one line, "
            "at a natural point; don't interrupt the task for it.")


# ---- deterministic toolkit audit -------------------------------------------------------------------------------

def _hook_commands(settings: dict) -> list:
    cmds = []
    for event, groups in (settings.get("hooks") or {}).items():
        for g in groups or []:
            for h in g.get("hooks") or []:
                cmds.append((event, h.get("command", "")))
    return cmds


def _broken_links(d: str) -> list:
    out = []
    try:
        for n in sorted(os.listdir(d)):
            fp = os.path.join(d, n)
            if os.path.islink(fp) and not os.path.exists(fp):
                out.append(n)
    except FileNotFoundError:
        pass
    return out


def audit() -> list:
    """Find toolkit misfires from config alone. Returns the proposals queued (new or existing)."""
    found = []
    cdir = paths.claude_dir()
    settings = store.read_json(os.path.join(cdir, "settings.json"), {}) or {}
    cmds = _hook_commands(settings)

    def hit(name):
        return [e for e, c in cmds if name in c]

    if hit("mct-prompt-router"):
        found.append(add(1, "toolkit_fix", "MCT prompt router fires on harness text, not just the user",
                         r"Its case-insensitive \bMCT\b regex matches background task notifications and any prose containing "
                         "'MCT', injecting a ~13 KB activation contract the user never asked for.",
                         "Remove the UserPromptSubmit handler (honey install does this); honey classifies prompt origin first.",
                         [{"q": f"settings.json UserPromptSubmit → mct-prompt-router.py"}], "mct-prompt-router"))
    if hit("session-context.py"):
        found.append(add(1, "toolkit_fix", "session-context.py re-injects CLAUDE.md and MCT.md every session",
                         "CLAUDE.md is already loaded natively, so ~4 KB is duplicated, plus ~8 KB of MCT.md; together they exceed "
                         "the 10,000-char additionalContext cap and get spilled to a file.",
                         "Remove the SessionStart handler; honey's bootstrap replaces it (~2.3 KB).",
                         [{"q": "settings.json SessionStart → session-context.py"}], "session-context"))
    if hit("completion-receipt.py"):
        found.append(add(1, "toolkit_fix", "Receipt Stop hook blocks Q&A turns that changed nothing",
                         "It tails the transcript and blocks any stop without a marker word, including pure questions; marker "
                         "words inside tool output also satisfy it.",
                         "Replace with honey's receipt gate: only after a turn that edited files, at most once per turn.",
                         [{"q": "settings.json Stop → completion-receipt.py"}], "completion-receipt"))
    sl = (settings.get("statusLine") or {}).get("command", "")
    if re.search(r"/plugins/cache/[^\"']+/\d+\.\d+\.\d+/", sl):
        found.append(add(1, "toolkit_fix", "statusLine points into a versioned plugin-cache path",
                         "The path breaks on the next plugin update.", "Point statusLine at `honey statusline` (honey install).",
                         [{"q": text.redact(sl, 200)}], "statusline-versioned:" + sl))
    enabled = settings.get("enabledPlugins") or {}
    clash = [p for p in ("superpowers@claude-plugins-official", "ponytail@ponytail") if enabled.get(p)]
    if clash:
        found.append(add(1, "toolkit_fix", "Competing always-on injectors are enabled: " + ", ".join(clash),
                         "Each injects its own top-priority rules at session start; honey-stack absorbs them into one layer.",
                         "Disable them (honey install records the change and uninstall restores it).",
                         [{"q": c} for c in clash], "clash:" + ",".join(clash)))
    for d in (os.path.join(cdir, "skills"), os.path.join(paths.agents_dir(), "skills"), os.path.join(paths.codex_dir(), "skills")):
        broken = _broken_links(d)
        if broken:
            found.append(add(1, "toolkit_fix", f"{len(broken)} broken skill symlinks in {text.redact(d, 80)}",
                             "Their targets were moved; the agent sees missing or failing skills.",
                             "Remove the dangling links (honey install records each target so uninstall can recreate them).",
                             [{"q": ", ".join(broken[:12]) + (" …" if len(broken) > 12 else "")}], "broken:" + d + ":" + ",".join(broken)))
    return found
