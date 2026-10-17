import json
import os
import subprocess
import sys

REPO = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, REPO)


def hook(agent, payload):
    """Run the real hook entrypoint the way the agents do; return parsed stdout (or {})."""
    r = subprocess.run([sys.executable, os.path.join(REPO, "bin", "honey"), "hook", "--agent", agent],
                       input=json.dumps(payload), capture_output=True, text=True, env=dict(os.environ))
    assert r.returncode == 0, r.stderr
    errs = os.path.join(os.environ["HONEY_HOME"], "logs", "hook-errors.log")
    assert not os.path.exists(errs), open(errs).read()
    return json.loads(r.stdout) if r.stdout.strip() else {}


def ctx_text(out):
    return (out.get("hookSpecificOutput") or {}).get("additionalContext", "")
