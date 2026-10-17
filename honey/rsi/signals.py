"""Deterministic signal detection over user prompts and assistant tails. No LLM, bounded regexes only."""
from __future__ import annotations

import re

# Text injected by the harness (task notifications, reminders, command output) is not the user talking.
# Hooks that trigger on it misfire — the exact bug that made MCT's router inject 13 KB contracts.
SYSTEM_ORIGIN = re.compile(
    r"^\s*(?:<(?:task-notification|system-reminder|local-command-(?:stdout|stderr|caveat)|bash-(?:input|stdout|stderr)"
    r"|user-prompt-submit-hook|teammate-message|command-(?:name|message|args))\b"
    r"|Caveat: The messages below were generated|\[Request interrupted|\[SYSTEM NOTIFICATION)", re.I)

NOTE = re.compile(r"^\s*(?:rsi|remember|honey)\s*(?:\((?P<scope>project|codex|claude|skill:[\w:-]{1,60})\))?\s*:\s*(?P<text>.{3,400})", re.I | re.S)
DIRECTIVE = re.compile(r"^\s*(?:from now on|going forward|in (?:the )?future|always|never|don'?t ever|stop (?:doing|using))\b", re.I)
CORR_START = re.compile(
    r"^\s*(?:no\b(?![\s,]+(?:worries|problem|rush|need))|nope|nah|wrong|incorrect|not (?:that|this|quite|what i (?:asked|meant|wanted))"
    r"|that'?s (?:not|wrong)|undo|revert|roll ?back|don'?t|do not|stop|wait|hold on)\b", re.I)
CORR_ANY = re.compile(
    r"\b(?:i (?:already |just )?(?:said|told you|asked(?: you)?)|as i (?:said|mentioned)|like i said|i meant"
    r"|you (?:missed|forgot|ignored|skipped|broke|didn'?t (?:read|follow|check|test|run))|why (?:did|would|are) you"
    r"|you (?:were|are) supposed to|not what i)\b", re.I)
STILL = re.compile(
    r"\b(?:still (?:not|broken|failing|fails|wrong|the same|happening|there|doesn'?t|isn'?t|getting)"
    r"|(?:doesn'?t|does not|didn'?t|did not|isn'?t|is not) work(?:ing)?|same (?:error|issue|problem|bug)|broke(?:n)? again|it'?s back)\b", re.I)
FRUSTRATION = re.compile(r"\?{2,}|!{2,}|\b(?:wtf|ugh+|ffs|seriously|come on|omg)\b", re.I)
ACCEPT = re.compile(r"^\s*(?:perfect|great|nice|awesome|excellent|thanks?(?: you)?|ty|lgtm|looks (?:good|great)|works(?: now| great)?"
                    r"|that works|ship it|exactly|love it|well done)\b[\s.!]*$", re.I)
CONTINUE = re.compile(r"^\s*(?:continue|go on|keep going|proceed|carry on|next|go ahead|do it|yes(?:,? (?:do it|go|please|proceed))?"
                      r"|yep|ok(?:ay)?(?:,? (?:go|do it|continue))?)\b[\s.!]*$", re.I)
ERROR_PASTE = re.compile(r"Traceback \(most recent call last\)|\bError:|\bERR!|\bFAILED\b|exit code [1-9]|\bat [\w.<>]{1,80} \(.{1,200}:\d+:\d+\)")
REVERT_CMD = re.compile(r"\bgit\s+(?:revert|reset\s+--hard|checkout\s+--\s|restore\s)")

CLAIMS_DONE = re.compile(r"\b(?:done|fixed|completed?|all (?:tests|checks) pass(?:ed|ing)?|should (?:now )?work|works now|implemented|ready for review)\b", re.I)
ENDS_Q = re.compile(r"(?:\?\s*\**\s*$)|\b(?:would you like|should i|do you want|shall i)\b", re.I)

NEGATIVE = {"correction", "still", "frustration", "revert"}


def origin(prompt: str) -> str:
    if SYSTEM_ORIGIN.search(prompt or ""):
        return "system"
    if re.match(r"^\s*[/$][\w:-]+", prompt or ""):
        return "command"
    return "user"


def caps_shouting(s: str) -> bool:
    letters = [c for c in s if c.isalpha()]
    return len(letters) >= 12 and sum(c.isupper() for c in letters) / len(letters) > 0.5


def classify(prompt: str) -> list:
    """Signals in a user prompt, strongest first."""
    p = (prompt or "")[:2000]
    sig = []
    if NOTE.match(p):
        sig.append("note")
    if DIRECTIVE.match(p):
        sig.append("directive")
    if CORR_START.match(p) or CORR_ANY.search(p):
        sig.append("correction")
    if STILL.search(p):
        sig.append("still")
    if FRUSTRATION.search(p) or caps_shouting(p):
        sig.append("frustration")
    if ERROR_PASTE.search(p):
        sig.append("error_paste")
    if len(p) <= 60 and ACCEPT.match(p):
        sig.append("accept")
    if len(p) <= 40 and CONTINUE.match(p):
        sig.append("continue")
    return sig


def classify_stop(tail: str) -> dict:
    t = tail or ""
    return {"claims_done": bool(CLAIMS_DONE.search(t[-600:])), "ends_q": bool(ENDS_Q.search(t[-200:]))}


def parse_note(prompt: str):
    m = NOTE.match(prompt or "")
    if not m:
        return None
    return {"scope": (m.group("scope") or "global").lower(), "text": m.group("text").strip()}
