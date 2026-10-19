"""Auto-update: a detached job started at SessionStart moves honey-stack to the newest vX.Y.Z release tag.

Only release tags reachable from origin/main ship, never raw main. A checkout with local edits, its own commits, or on
a branch other than main is left alone. Plugin-only installs (no checkout) go through the agents' own plugin CLIs.
Opt out with {"autoupdate": false} in ~/.honey/config.json. The running session keeps the code it started with; the
update loads next session.
"""
from __future__ import annotations

import os
import re
import subprocess
import time

from honey import paths
from honey.rsi import store

CHECK_EVERY = 3600       # seconds between checks; sessions starting inside the window skip the process and network
REPO_OVERRIDE = None     # tests point this at a throwaway checkout
RELEASE = re.compile(r"^v(\d+)\.(\d+)\.(\d+)$", re.ASCII)  # ASCII: \d would also accept lookalike Unicode digits
GIT_ENV = dict(os.environ, GIT_TERMINAL_PROMPT="0")        # a background fetch must never wait on a credential prompt


def _git(repo: str, *args: str, timeout: int = 60):
    return subprocess.run(["git", "-C", repo, *args], capture_output=True, text=True, timeout=timeout, env=GIT_ENV)


def _key(tag: str):
    return tuple(int(x) for x in RELEASE.match(tag).groups())


def enabled() -> bool:
    if os.environ.get("HONEY_NO_AUTOUPDATE"):
        return False
    return (store.read_json(paths.path("config.json"), {}) or {}).get("autoupdate", True) is not False


def _state_file() -> str:
    return paths.path("state", "autoupdate.json")


def due() -> bool:
    """Cheap check the hook runs before it spawns a process at all."""
    return enabled() and time.time() - (store.read_json(_state_file(), {}) or {}).get("checked", 0) >= CHECK_EVERY


def update_checkout(repo: str) -> dict:
    """Fast-forward honey's own git checkout to the newest release tag. Returns {status: updated|current|skipped, ...}."""
    top = _git(repo, "rev-parse", "--show-toplevel").stdout.strip()
    if not top or os.path.realpath(top) != os.path.realpath(repo):
        return {"status": "skipped", "reason": "not honey-stack's own git root"}  # a copy inside someone else's repo
    if _git(repo, "fetch", "--tags", "--quiet", "origin").returncode != 0:
        return {"status": "skipped", "reason": "fetch failed (offline?)"}
    releases = sorted((t for t in _git(repo, "tag", "--list", "v*").stdout.split() if RELEASE.match(t)), key=_key)
    releases = [t for t in releases if _git(repo, "merge-base", "--is-ancestor", t, "refs/remotes/origin/main").returncode == 0]
    if not releases:
        return {"status": "skipped", "reason": "no release tags on origin/main"}
    newest = releases[-1]
    if _git(repo, "merge-base", "--is-ancestor", newest, "HEAD").returncode == 0:
        return {"status": "current"}
    branch = _git(repo, "symbolic-ref", "--short", "-q", "HEAD").stdout.strip()
    at_release = RELEASE.match(_git(repo, "describe", "--tags", "--exact-match", "--match", "v[0-9]*").stdout.strip())
    if branch != "main" and not (not branch and at_release):  # main, or a detached HEAD sitting exactly on a release
        return {"status": "skipped", "reason": "not on main or a detached release tag"}
    if _git(repo, "status", "--porcelain", "--untracked-files=no").stdout.strip():
        return {"status": "skipped", "reason": "local changes"}
    behind = [t for t in releases if _git(repo, "merge-base", "--is-ancestor", t, "HEAD").returncode == 0]
    current = behind[-1].lstrip("v") if behind else "?"
    if _git(repo, "merge", "--ff-only", "--quiet", newest).returncode != 0:
        return {"status": "skipped", "reason": "checkout has its own commits (not a fast-forward)"}
    return {"status": "updated", "from": current, "to": newest.lstrip("v")}


def _plugin_result(parent: str, current: str) -> dict:
    """Plugin caches hold one directory per version. A newer one than the running version means an update landed."""
    versions = sorted((d for d in os.listdir(parent) if RELEASE.match("v" + d)), key=lambda d: _key("v" + d))
    if versions and _key("v" + versions[-1]) > _key("v" + current):
        return {"status": "updated", "from": current, "to": versions[-1]}
    return {"status": "current"}


def _update_plugins(repo: str) -> dict:
    """Plugin-only install: no checkout to pull, so ask each agent's CLI to refresh the marketplace and plugin."""
    from honey import __version__, install
    ran = False
    for agent, cmds in (("claude", [["plugin", "marketplace", "update", "honey-stack"], ["plugin", "update", install.PLUGIN]]),
                        ("codex", [["plugin", "marketplace", "upgrade", "honey-stack"], ["plugin", "add", install.PLUGIN]])):
        exe = install._cli(agent)
        if exe:
            ran = True
            for c in cmds:
                if subprocess.run([exe, *c], capture_output=True, text=True, timeout=180, env=GIT_ENV).returncode != 0:
                    break
    if not ran:
        return {"status": "skipped", "reason": "no agent CLI"}
    return _plugin_result(os.path.dirname(os.path.realpath(repo)), __version__)


def _in_plugin_cache(path: str) -> bool:
    parts = path.replace(os.sep, "/").split("/")
    return any(parts[i:i + 2] == ["plugins", "cache"] for i in range(len(parts) - 1))


def run() -> dict:
    """The detached job. Throttled, opt-out aware, and never raises into the session."""
    if not enabled():
        return {"status": "skipped", "reason": "autoupdate off"}
    state = store.read_json(_state_file(), {}) or {}
    if time.time() - state.get("checked", 0) < CHECK_EVERY:
        return {"status": "skipped", "reason": "checked recently"}
    store.write_json(_state_file(), dict(state, checked=time.time()))  # stamp first so a crash cannot loop
    try:
        repo = REPO_OVERRIDE or paths.REPO
        result = _update_plugins(repo) if _in_plugin_cache(repo) else update_checkout(repo)
    except Exception as e:  # network, git or CLI trouble must never break a session
        result = {"status": "skipped", "reason": f"{type(e).__name__}: {e}"}
    state = dict(store.read_json(_state_file(), {}) or {}, last=result)
    if result["status"] == "updated":
        state["pending_notice"] = result
    store.write_json(_state_file(), state)
    return result


def notice() -> str:
    """One line at the next SessionStart after an update, then cleared."""
    state = store.read_json(_state_file(), {}) or {}
    r = state.pop("pending_notice", None)
    if not r:
        return ""
    store.write_json(_state_file(), state)
    return f"honey-stack auto-updated {r['from']} → {r['to']}. Turn off: set \"autoupdate\": false in ~/.honey/config.json."
