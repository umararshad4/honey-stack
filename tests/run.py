#!/usr/bin/env python3
"""Run every tests/test_*.py in its own interpreter with a throwaway HONEY_HOME. Usage: python3 tests/run.py"""
import glob
import os
import subprocess
import sys
import tempfile

here = os.path.dirname(os.path.abspath(__file__))
failed = 0
for t in sorted(glob.glob(os.path.join(here, "test_*.py"))):
    with tempfile.TemporaryDirectory() as h:
        none = os.path.join(h, "none-reflection.json")  # tests never make a paid reflector call
        with open(none, "w") as f:
            f.write('{"session_summary":"","candidates":[],"bullet_labels":[],"skill_feedback":[],"toolkit_misfires":[],'
                    '"progress":[],"project_facts_dropped":0,"none_reason":"test"}')
        env = dict(os.environ, HONEY_HOME=h, PYTHONDONTWRITEBYTECODE="1", HONEY_FAKE_LLM=none)
        env.pop("RSI_CHILD", None), env.pop("HONEY_DISABLE", None)
        r = subprocess.run([sys.executable, t], env=env, capture_output=True, text=True)
    ok = r.returncode == 0
    failed += not ok
    print(("ok   " if ok else "FAIL ") + os.path.basename(t))
    if not ok:
        print((r.stdout + r.stderr)[-3000:])
print(f"python {sys.version.split()[0]}: {'all passed' if not failed else f'{failed} failed'}")
sys.exit(1 if failed else 0)
