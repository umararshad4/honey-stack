"""Stop gate: after a turn that edited files, require the one-line receipt. Q&A turns are never nagged."""
from __future__ import annotations

import re

from honey import tasks

RECEIPT = re.compile(r"(?im)\bchecks run\b|^\s*skipped:|^\s*risk:")
DONE = re.compile(r'\b(done|fixed|completed?|implemented|removed|uninstalled|disabled|enabled|configured|all (?:tests|checks) pass(?:ed)?)\b', re.I)
UNRESOLVED = re.compile(r"\b(not (?:yet )?(?:done|fixed|complete)|(?:remains?|still) unverified|unable to|could not|couldn't|verification (?:failed|pending))\b", re.I)


def check(payload: dict, state: dict):
    """Reason to block the stop, or None. Blocks at most once per turn."""
    if payload.get("stop_hook_active") or state.get("off") or state.get("nagged"):
        return None
    msg = (payload.get("last_assistant_message") or "").strip()
    missing = tasks.missing(state)
    if msg and DONE.search(msg) and not UNRESOLVED.search(msg) and missing:
        state['nagged'] = True
        return ('honey: completion lacks fresh observed evidence for: ' + ', '.join(missing)
                + '. Run the checks and link their results with `honey task verify`, or state what remains unverified. '
                'A receipt sentence alone is not evidence. Briefly explain this verification gap to the user before continuing.')
    if not state.get("edited"):
        return None
    if not msg or RECEIPT.search(msg) or msg.rstrip("*_ `").endswith("?"):
        return None
    state["nagged"] = True
    return "honey: this turn edited files. End with one line: `Checks run: … Skipped: … Risk: …` (omit empty parts)."
