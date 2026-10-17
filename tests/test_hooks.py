"""End-to-end scenario through the real hook entrypoint, for both agents."""
import json
import os

from helpers import ctx_text, hook

H = os.environ["HONEY_HOME"]
C = {"session_id": "s1", "cwd": "/tmp"}

out = hook("claude", dict(C, hook_event_name="SessionStart", source="startup"))
boot = ctx_text(out)
assert boot.startswith("honey-stack active · scope=full · process=light · voice=terse"), boot[:80]
assert "honey:debug" in boot and "$debug" not in boot
assert len(boot) < 3000, len(boot)

# harness text never triggers anything (the MCT-router bug class)
assert hook("claude", dict(C, hook_event_name="UserPromptSubmit", prompt="<task-notification>MCT done remember: x</task-notification>")) == {}

# a correction, a done-claim, then an explicit note
hook("claude", dict(C, hook_event_name="UserPromptSubmit", prompt="no, don't commit, I said only push"))
hook("claude", dict(C, hook_event_name="Stop", last_assistant_message="Done, all tests pass.", stop_hook_active=False))
ack = ctx_text(hook("claude", dict(C, hook_event_name="UserPromptSubmit", prompt="remember: never commit unless asked")))
assert "saved" in ack and "never commit unless asked" in ack, ack

# mode switch, and a lookalike that must not switch
assert "scope=ultra process=strict" in ctx_text(hook("claude", dict(C, hook_event_name="UserPromptSubmit", prompt="/honey ultra strict")))
assert "HONEY MODE" not in ctx_text(hook("claude", dict(C, hook_event_name="UserPromptSubmit", prompt="add a normal mode toggle")))

# guard: ask on Claude default, deny under bypass and on Codex; quoted text passes
pre = dict(C, hook_event_name="PreToolUse", tool_name="Bash", tool_input={"command": "git push -f origin main"}, permission_mode="default")
assert hook("claude", pre)["hookSpecificOutput"]["permissionDecision"] == "ask"
assert hook("claude", dict(pre, permission_mode="bypassPermissions"))["hookSpecificOutput"]["permissionDecision"] == "deny"
assert hook("codex", pre)["hookSpecificOutput"]["permissionDecision"] == "deny"
assert hook("claude", dict(pre, tool_input={"command": 'echo "rm -rf /"'})) == {}

# receipt gate: nothing on a Q&A turn, block once after an edit turn, then not again
hook("claude", dict(C, hook_event_name="UserPromptSubmit", prompt="what does this function do"))
assert hook("claude", dict(C, hook_event_name="Stop", last_assistant_message="It parses dates.")) == {}
hook("claude", dict(C, hook_event_name="UserPromptSubmit", prompt="fix the date bug"))
hook("claude", dict(C, hook_event_name="PostToolUse", tool_name="Edit", tool_input={"file_path": "/tmp/a.py", "new_string": "x = 1"}))
assert hook("claude", dict(C, hook_event_name="Stop", last_assistant_message="Fixed it."))["decision"] == "block"
assert hook("claude", dict(C, hook_event_name="Stop", last_assistant_message="Fixed it.", stop_hook_active=True)) == {}
assert hook("claude", dict(C, hook_event_name="Stop", last_assistant_message="Fixed.\nChecks run: pytest pass.")) == {}

# secret scan on new text only
sec = hook("claude", dict(C, hook_event_name="PostToolUse", tool_name="Write",
                          tool_input={"file_path": "/tmp/cfg.py", "content": 'API_KEY = "sk-proj-abcdefghijklmnopqrstuvwxyz123456"'}))
assert sec.get("decision") == "block" and "sk-proj" not in sec["reason"], sec
assert hook("claude", dict(C, hook_event_name="PostToolUse", tool_name="Write",
                           tool_input={"file_path": "/tmp/cfg.py", "content": 'API_KEY = os.environ["API_KEY"]'})) == {}

# skill attribution: model invokes a skill, the next user turn is a correction → neg outcome
hook("claude", dict(C, hook_event_name="PostToolUse", tool_name="Skill", tool_input={"skill": "honey:ship"}))
hook("claude", dict(C, hook_event_name="UserPromptSubmit", prompt="no, that's wrong, I said don't push"))

# the note is in the next session's brief — on Codex too (one agent-neutral ledger)
nxt = ctx_text(hook("codex", {"session_id": "s2", "cwd": "/tmp", "hook_event_name": "SessionStart", "source": "startup"}))
assert "never commit unless asked" in nxt and "$debug" in nxt, nxt[-400:]
again = ctx_text(hook("codex", {"session_id": "s2", "cwd": "/tmp", "hook_event_name": "SessionStart", "source": "compact"}))
assert again.endswith(nxt.split("\n\n", 1)[1]) and again.startswith("Context was compacted"), "brief must stay frozen"

# pause
hook("claude", dict(C, hook_event_name="UserPromptSubmit", prompt="honey off"))
assert hook("claude", dict(C, hook_event_name="Stop", last_assistant_message="ok")) == {}
r = hook("claude", dict(C, hook_event_name="UserPromptSubmit", prompt="rsi off"))
assert r.get("decision") == "block"

# events recorded with redaction; outcome attributed
import glob
rows = [json.loads(l) for f in glob.glob(os.path.join(H, "events", "*", "claude-s1.jsonl")) for l in open(f)]
kinds = [r["e"] for r in rows]
assert "start" in kinds and "guard" in kinds and "receipt_nag" in kinds and "note" in kinds, kinds
assert any(r["e"] == "skill_outcome" and r["outcome"] == "neg" for r in rows), [r for r in rows if r["e"].startswith("skill")]
assert any(r["e"] == "prompt" and "correction" in r.get("sig", []) for r in rows)
assert not any("sk-proj" in json.dumps(r) for r in rows)

# SessionEnd spawns a detached job and returns fast
import time
t0 = time.time()
hook("claude", dict(C, hook_event_name="SessionEnd", reason="other"))
assert time.time() - t0 < 1.5
print("hooks ok")
