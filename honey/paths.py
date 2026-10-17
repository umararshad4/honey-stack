"""Filesystem locations. Everything honey writes lives under HONEY_HOME (default ~/.honey)."""
from __future__ import annotations

import hashlib
import os
import re
import subprocess

REPO = os.path.dirname(os.path.dirname(os.path.realpath(__file__)))


def home() -> str:
    return os.environ.get("HONEY_HOME") or os.path.join(os.path.expanduser("~"), ".honey")


def path(*parts: str) -> str:
    return os.path.join(home(), *parts)


def safe_id(raw: str) -> str:
    """Session ids end up in file names; never let them traverse paths."""
    return re.sub(r"[^A-Za-z0-9_-]", "", str(raw or ""))[:80] or "nosession"


def session_key(agent: str, sid: str) -> str:
    return f"{agent}-{safe_id(sid)}"


def project_slug(cwd: str) -> str:
    """owner-repo from the git remote, else the repo/dir basename. One git call, cached by caller."""
    cwd = cwd or os.getcwd()
    try:
        out = subprocess.run(["git", "-C", cwd, "remote", "get-url", "origin"],
                             capture_output=True, text=True, timeout=2).stdout.strip()
    except Exception:
        out = ""
    if out:
        m = re.search(r"[:/]([^/:]+)/([^/]+?)(?:\.git)?/?$", out)
        if m:
            return re.sub(r"[^A-Za-z0-9_.-]", "", f"{m.group(1)}-{m.group(2)}").lower()
    base = os.path.basename(os.path.normpath(cwd)) or "root"
    return "nogit-" + re.sub(r"[^A-Za-z0-9_.-]", "", base).lower()[:40] + "-" + hashlib.sha1(cwd.encode()).hexdigest()[:6]


def claude_dir() -> str:
    return os.environ.get("CLAUDE_CONFIG_DIR") or os.path.join(os.path.expanduser("~"), ".claude")


def codex_dir() -> str:
    return os.environ.get("CODEX_HOME") or os.path.join(os.path.expanduser("~"), ".codex")


def agents_dir() -> str:
    return os.environ.get("HONEY_AGENTS_DIR") or os.path.join(os.path.expanduser("~"), ".agents")
