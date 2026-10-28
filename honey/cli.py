"""honey CLI: hook | rsi | install | uninstall | doctor | sync | statusline."""
from __future__ import annotations

import json
import os
import sys


def statusline() -> int:
    """Claude statusLine command: [HONEY] badge plus pending RSI review count."""
    from honey import paths
    from honey.rsi import review, store
    try:
        payload = json.loads(sys.stdin.read() or "{}")
    except ValueError:
        payload = {}
    st = store.read_json(paths.path("state", "sessions", paths.session_key("claude", payload.get("session_id", "")) + ".json"), {}) or {}
    if st.get("off"):
        badge = "[HONEY off]"
    else:
        extra = [x for x in (st.get("scope", "full") != "full" and st["scope"].upper(),
                             st.get("process") == "strict" and "strict", st.get("voice") == "normal" and "normal") if x]
        badge = "[HONEY" + (":" + " ".join(extra) if extra else "") + "]"
    n = len(review.pending())
    print(badge + (f" rsi:{n}" if n else ""))
    return 0


def main(argv: list) -> int:
    if not argv or argv[0] in ("-h", "--help"):
        print("usage: honey install | uninstall | update | autoupdate | doctor | task status|set|verify | sync | rsi … | statusline | --version | hook --agent claude|codex")
        return 0
    cmd, rest = argv[0], argv[1:]
    if cmd in ("--version", "-V", "version"):
        from honey import __version__
        print(f"honey-stack {__version__}")
        return 0
    if cmd == "hook":
        agent = rest[rest.index("--agent") + 1] if "--agent" in rest else ("codex" if os.environ.get("PLUGIN_DATA") else "claude")
        from honey import dispatch
        return dispatch.run(agent)
    if cmd == "rsi":
        from honey.rsi import cli as rsi_cli
        return rsi_cli.main(rest)
    if cmd == "statusline":
        return statusline()
    if cmd == "autoupdate":
        from honey import autoupdate
        print(json.dumps(autoupdate.run()))
        return 0
    if cmd in ("install", "uninstall", "sync", "update"):
        from honey import install
        return install.main(cmd, rest)
    if cmd == "doctor":
        from honey import doctor
        return doctor.main(rest)
    if cmd == "task":
        from honey import tasks
        return tasks.main(rest)
    print(f"unknown command {cmd}", file=sys.stderr)
    return 2
