"""PostToolUse secret scan of NEW text only (MCT's version rescanned whole files, so old fixtures re-fired forever)."""
from __future__ import annotations

import os
import re
import subprocess

PATTERNS = [
    ("anthropic/openai key", re.compile(r"\bsk-(?:ant-|proj-)?[A-Za-z0-9_-]{20,}")),
    ("private key", re.compile(r"-----BEGIN (?:RSA |EC |OPENSSH |DSA )?PRIVATE KEY-----")),
    ("aws access key", re.compile(r"\bAKIA[0-9A-Z]{16}\b")),
    ("github token", re.compile(r"\b(?:gh[pousr]_[A-Za-z0-9]{30,}|github_pat_[A-Za-z0-9_]{30,})")),
    ("slack token", re.compile(r"\bxox[baprs]-[A-Za-z0-9-]{10,}")),
    ("stripe live key", re.compile(r"\bsk_live_[A-Za-z0-9]{16,}")),
    ("hardcoded secret", re.compile(r"(?i)\b(?:api[_-]?key|secret|token|password)\s*[:=]\s*['\"][^'\"\s]{16,}['\"]")),
]
_PLACEHOLDER = re.compile(r"(?i)(x{6,}|your[_-]|example|placeholder|dummy|changeme|<[^>]+>|\$\{)")


def new_text(payload: dict) -> list:
    """[(path, text)] pairs of content this tool call added. Claude Write/Edit/MultiEdit and Codex apply_patch."""
    ti = payload.get("tool_input") or {}
    if isinstance(ti, str):
        ti = {"command": ti}
    tool = payload.get("tool_name", "")
    out = []
    fp = ti.get("file_path") or ti.get("path") or ti.get("notebook_path") or ""
    if ti.get("content"):
        out.append((fp, ti["content"]))
    if ti.get("new_string"):
        out.append((fp, ti["new_string"]))
    if ti.get("new_source"):
        out.append((fp, ti["new_source"]))
    for e in ti.get("edits") or []:
        if isinstance(e, dict) and e.get("new_string"):
            out.append((fp, e["new_string"]))
    cmd = ti.get("command") or ti.get("patch") or ""
    if isinstance(cmd, list):
        cmd = " ".join(map(str, cmd))
    if tool in ("apply_patch", "Bash", "ApplyPatch") and "*** Begin Patch" in str(cmd):
        cur = ""
        for line in str(cmd).splitlines():
            m = re.match(r"^\*\*\* (?:Add|Update) File: (.+)$", line)
            if m:
                cur = m.group(1).strip()
            elif line.startswith("+") and not line.startswith("+++"):
                out.append((cur, line[1:]))
    return out


def _ignored(path: str, cwd: str) -> bool:
    if not path:
        return False
    try:
        d = os.path.dirname(os.path.join(cwd or ".", path)) or "."
        return subprocess.run(["git", "-C", d, "check-ignore", "-q", path if os.path.isabs(path) else os.path.join(cwd or ".", path)],
                              capture_output=True, timeout=2).returncode == 0
    except Exception:
        return False


def scan(payload: dict):
    """Reason string if newly written text contains a likely secret (never echoes the secret), else None."""
    ignored = {}
    for path, text in new_text(payload):
        for lineno, line in enumerate(str(text).splitlines() or [str(text)], 1):
            for kind, rx in PATTERNS:
                m = rx.search(line)
                if m and not _PLACEHOLDER.search(m.group(0)):
                    if path not in ignored:
                        ignored[path] = _ignored(path, payload.get("cwd", ""))
                    if ignored[path]:
                        continue  # gitignored files (.env) are where secrets belong; keep scanning the others
                    where = os.path.basename(path) if path else "the edited content"
                    return (f"honey: possible {kind} written to {where} (line ~{lineno}). "
                            "Move it to an env var or a gitignored file, or confirm it is a test fixture.")
    return None
