"""RSI observer: turns hook payloads into a per-session event log. Deterministic, no LLM, fail-silent."""
from __future__ import annotations

import os
import re
import subprocess
import sys
import time

from honey import paths
from honey.rsi import signals, store, text

WINDOW = 3  # user turns after a skill fires during which the first signal decides its outcome
QUARANTINE_TOOLS = re.compile(r"^(?:WebFetch|WebSearch|web_search|mcp__.*)$")
SKILL_READ = re.compile(r"/skills/([\w:-]{1,60})/SKILL\.md")


def events_file(key: str) -> str:
    return paths.path("events", time.strftime("%Y-%m"), f"{key}.jsonl")


def record(ctx, e: str, **fields) -> None:
    if ctx.state.get("off") or ctx.state.get("rsi_off"):
        if e != "cmd":
            return
    row = {"v": 1, "ts": text.now(), "a": ctx.agent, "sid": paths.safe_id(ctx.sid), "t": ctx.state.get("turn", 0), "e": e}
    row.update({k: v for k, v in fields.items() if v not in (None, "", [], {})})
    store.append_jsonl(events_file(ctx.key), row)


def skill_invoked(ctx, name: str, by: str, via: str) -> None:
    name = (name or "").strip().lstrip("/$")[:80]
    if not name:
        return
    record(ctx, "skill", name=name, by=by, via=via)
    pend = ctx.state.setdefault("pending_skills", [])
    pend.append({"name": name, "t": ctx.state.get("turn", 0)})
    del pend[:-5]


def attribute(ctx, sig: list) -> None:
    """Close skill outcome windows using this user turn's signals."""
    turn = ctx.state.get("turn", 0)
    keep = []
    for p in ctx.state.get("pending_skills", []):
        age = turn - p["t"]
        if age < 1:
            keep.append(p)
            continue
        outcome = None
        if signals.NEGATIVE & set(sig):
            outcome = "neg"
        elif "accept" in sig:
            outcome = "pos"
        elif "continue" in sig:
            outcome = "cont"
        elif age >= WINDOW:
            outcome = "neutral"
        if outcome:
            record(ctx, "skill_outcome", name=p["name"], outcome=outcome, age=age)
        else:
            keep.append(p)
    ctx.state["pending_skills"] = keep


def user_prompt(ctx, prompt: str, sig: list) -> None:
    q = text.redact(prompt, 300) if sig else None
    prev = ctx.state.get("tail") if sig and set(sig) & (signals.NEGATIVE | {"error_paste"}) else None
    record(ctx, "prompt", origin="user", len=len(prompt or ""), sig=sig, q=q, prev=prev, kw=text.keywords(prompt))
    attribute(ctx, sig)
    for m in re.finditer(r"(?:^|\s)\$([a-z][\w-]{1,40})\b", prompt or ""):
        if ctx.agent == "codex":
            skill_invoked(ctx, m.group(1), "user", "mention")


def tool_used(ctx, payload: dict) -> None:
    tool = payload.get("tool_name", "") or ""
    ti = payload.get("tool_input") or {}
    if isinstance(ti, str):
        ti = {"command": ti}
    cmd = ti.get("command") if isinstance(ti, dict) else None
    if isinstance(cmd, list):
        cmd = " ".join(map(str, cmd))
    fields = {"tool": tool[:60]}
    if QUARANTINE_TOOLS.match(tool):
        ctx.state["quarantined"] = True
        fields["xc"] = True
    if tool == "Skill" and isinstance(ti, dict):
        skill_invoked(ctx, ti.get("skill") or ti.get("name") or "", "model", "Skill")
    if isinstance(cmd, str) and cmd:
        fields["cmd"] = text.redact(cmd, 160)
        m = SKILL_READ.search(cmd)
        if m and ctx.agent == "codex":
            skill_invoked(ctx, m.group(1), "model", "skill_md")
        if signals.REVERT_CMD.search(cmd) and ctx.state.get("pending_skills"):
            record(ctx, "signal", sig=["revert"])
            attribute(ctx, ["revert"])
    fp = ti.get("file_path") if isinstance(ti, dict) else None
    if fp:
        fields["ext"] = os.path.splitext(fp)[1][:10]
    record(ctx, "tool", **fields)


def spawn(args: list) -> None:
    """Fire-and-forget child in its own session so it outlives the hook (SessionEnd has a ~1.5 s budget)."""
    env = dict(os.environ, RSI_CHILD="1", HONEY_OFF="1")
    log = open(store.ensure_dir(paths.path("logs")) + "/jobs.log", "ab")
    subprocess.Popen([sys.executable, os.path.join(paths.REPO, "bin", "honey"), *args], stdin=subprocess.DEVNULL,
                     stdout=log, stderr=log, close_fds=True, start_new_session=True, env=env, cwd=paths.home())
