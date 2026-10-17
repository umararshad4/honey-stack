"""honey doctor — read-only health check for both agents and RSI. Exit 1 if any check fails."""
from __future__ import annotations

import glob
import hashlib
import json
import os
import re
import subprocess
import sys
import tempfile
import time

from honey import paths
from honey.install import CLAUDE_CLASH, CODEX_CLASH, MCT_HOOKS, PLUGIN
from honey.rsi import review, store

BUDGET = 3500


class Report:
    def __init__(self):
        self.fails = 0

    def ok(self, cond, good, bad, warn=False):
        mark = "ok  " if cond else ("warn" if warn else "FAIL")
        if not cond and not warn:
            self.fails += 1
        print(f"  {mark} {good if cond else bad}")


def _tree_hash(root: str, parts=("hooks", "honey", "skills", "bin")) -> str:
    h = hashlib.sha1()
    for part in parts:
        for fp in sorted(glob.glob(os.path.join(root, part, "**", "*"), recursive=True)):
            if os.path.isfile(fp) and "__pycache__" not in fp:
                h.update(os.path.relpath(fp, root).encode())
                with open(fp, "rb") as f:
                    h.update(f.read())
    return h.hexdigest()[:12]


def skills_budget() -> tuple:
    total, users = 0, 0
    for fp in glob.glob(os.path.join(paths.REPO, "skills", "*", "SKILL.md")):
        with open(fp, encoding="utf-8") as f:
            fm = f.read().split("---")[1]
        if "disable-model-invocation: true" in fm:
            users += 1
            continue
        m = re.search(r"^description:\s*(.*)$", fm, re.M)
        total += len(m.group(1).strip().strip('"')) if m else 0
    return total, users


def smoke() -> tuple:
    with tempfile.TemporaryDirectory() as h:
        t0 = time.time()
        r = subprocess.run([sys.executable, os.path.join(paths.REPO, "bin", "honey"), "hook", "--agent", "claude"],
                           input=json.dumps({"hook_event_name": "SessionStart", "source": "startup", "session_id": "doctor", "cwd": h}),
                           capture_output=True, text=True, env=dict(os.environ, HONEY_HOME=h), timeout=10)
        ms = int((time.time() - t0) * 1000)
    try:
        ok = json.loads(r.stdout)["hookSpecificOutput"]["additionalContext"].startswith("honey-stack active")
    except Exception:
        ok = False
    return ok, ms


def main(argv: list) -> int:
    rep = Report()
    cdir, xdir = paths.claude_dir(), paths.codex_dir()
    print("honey doctor")
    print(f"repo {paths.REPO}")

    print("Claude Code")
    s = store.read_json(os.path.join(cdir, "settings.json"), {}) or {}
    en = s.get("enabledPlugins") or {}
    rep.ok(en.get(PLUGIN) is True, f"{PLUGIN} enabled", f"{PLUGIN} not enabled (run honey install)")
    for p in CLAUDE_CLASH:
        rep.ok(not en.get(p), f"{p} disabled", f"{p} still enabled: competing always-on injector")
    cmds = [h.get("command", "") for gs in (s.get("hooks") or {}).values() for g in gs or [] for h in g.get("hooks") or []]
    left = [m for m in MCT_HOOKS if any(m in c for c in cmds)]
    rep.ok(not left, "no MCT hook handlers", f"MCT handlers still registered: {left} (mct self-update drift?)")
    rep.ok("honey" in (s.get("statusLine") or {}).get("command", ""), "statusLine → honey", "statusLine not honey's", warn=True)
    broken = [n for n in glob.glob(os.path.join(cdir, "skills", "*")) if os.path.islink(n) and not os.path.exists(n)]
    rep.ok(not broken, "no dangling skill links", f"{len(broken)} dangling skill links in {cdir}/skills")
    inst = (store.read_json(os.path.join(cdir, "plugins", "installed_plugins.json"), {}) or {}).get("plugins", {}).get(PLUGIN) or []
    where = inst[0].get("installPath", "") if inst else ""
    rep.ok(not inst or os.path.realpath(where) == os.path.realpath(paths.REPO) or _tree_hash(where) == _tree_hash(paths.REPO),
           "Claude runs the current repo code", f"Claude's copy at {where} differs from the repo (run /plugin update or reinstall)", warn=True)

    print("Codex")
    toml = ""
    try:
        with open(os.path.join(xdir, "config.toml"), encoding="utf-8") as f:
            toml = f.read()
    except FileNotFoundError:
        pass

    def enabled(p):
        m = re.search(r'\[plugins\."' + re.escape(p) + r'"\]\s*\n(?:(?!\[)[^\n]*\n)*?\s*enabled\s*=\s*(true|false)', toml)
        return m and m.group(1) == "true"

    rep.ok(enabled(PLUGIN), f"{PLUGIN} enabled", f"{PLUGIN} not enabled in config.toml")
    for p in CODEX_CLASH:
        rep.ok(not enabled(p), f"{p} disabled", f"{p} still enabled")
    trusted = re.findall(r'\[hooks\.state\."honey@honey-stack:hooks/codex-hooks\.json:(\w+):', toml)
    rep.ok(len(set(trusted)) >= 9, f"Codex trusts {len(set(trusted))} honey hooks",
           f"Codex trusts {len(set(trusted))}/9 honey hooks: open codex, run /hooks, trust the honey entries", warn=True)
    caches = glob.glob(os.path.join(xdir, "plugins", "cache", "honey-stack", "honey", "*"))
    if caches:
        rep.ok(_tree_hash(caches[-1]) == _tree_hash(paths.REPO), "Codex cache matches repo", "Codex cache is stale: run honey sync", warn=True)
    else:
        rep.ok(False, "", "honey not in Codex plugin cache (run honey install)")
    abroken = [n for n in glob.glob(os.path.join(paths.agents_dir(), "skills", "*")) if os.path.islink(n) and not os.path.exists(n)]
    rep.ok(not abroken, "no dangling ~/.agents skill links", f"{len(abroken)} dangling links in ~/.agents/skills")

    print("Hooks and skills")
    mine = {os.path.basename(os.path.dirname(f)) for f in glob.glob(os.path.join(paths.REPO, "skills", "*", "SKILL.md"))}
    dups = sorted({os.path.basename(d) for base in (os.path.join(cdir, "skills"), os.path.join(paths.agents_dir(), "skills"), os.path.join(xdir, "skills"))
                   for d in glob.glob(os.path.join(base, "*")) if os.path.basename(d) in mine and os.path.exists(d)})
    rep.ok(not dups, "no skill-name duplicates outside honey", f"same-name skills outside honey: {dups} (honey install retires absorbed ones)", warn=True)
    ok, ms = smoke()
    rep.ok(ok, f"SessionStart smoke test ({ms} ms)", f"SessionStart smoke test failed ({ms} ms)")
    rep.ok(ms < 300, "hook latency fine", f"hook took {ms} ms", warn=True)
    total, users = skills_budget()
    rep.ok(total <= BUDGET, f"model-invoked descriptions {total} chars (≤{BUDGET}); {users} user-invoked skills cost 0",
           f"model-invoked descriptions {total} chars > {BUDGET}")

    print("RSI")
    h = paths.home()
    errs = paths.path("logs", "hook-errors.log")
    rep.ok(not os.path.exists(errs), "no hook errors logged", f"hook errors logged in {errs}", warn=True)
    files = sorted(glob.glob(paths.path("events", "*", "*.jsonl")), key=os.path.getmtime)
    last = {}
    for fp in files[-20:]:
        for r in store.read_jsonl(fp):
            last[(r.get("a"), r.get("e"))] = r.get("ts")
    for agent in ("claude", "codex"):
        seen = sorted(e for (a, e) in last if a == agent)
        rep.ok(bool(seen), f"{agent}: events seen {', '.join(seen)}", f"{agent}: no events yet (start a session)", warn=True)
    remotes = subprocess.run(["git", "-C", h, "remote"], capture_output=True, text=True).stdout.strip() if os.path.isdir(os.path.join(h, ".git")) else ""
    rep.ok(not remotes, "~/.honey has no git remote (stays local)", f"~/.honey has a git remote: {remotes}")
    print(f"  info {len(review.pending())} items pending in /rsi review")
    print("all good" if not rep.fails else f"{rep.fails} problem(s)")
    return 1 if rep.fails else 0
