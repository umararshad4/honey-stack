"""Stop gate: after a turn that edited files, require the one-line receipt. Q&A turns are never nagged."""
from __future__ import annotations

import re

RECEIPT = re.compile(r"(?im)\bchecks run\b|^\s*skipped:|^\s*risk:")


def check(payload: dict, state: dict):
    """Reason to block the stop, or None. Blocks at most once per turn."""
    if payload.get("stop_hook_active") or state.get("off") or not state.get("edited") or state.get("nagged"):
        return None
    msg = (payload.get("last_assistant_message") or "").strip()
    if not msg or RECEIPT.search(msg) or msg.rstrip("*_ `").endswith("?"):
        return None
    state["nagged"] = True
    return "honey: this turn edited files. End with one line: `Checks run: … Skipped: … Risk: …` (omit empty parts)."
