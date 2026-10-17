from helpers import REPO  # noqa: F401
from honey.guard import check
from honey import modes

assert check("git --no-pager push -f origin main")[1] == "ask"
assert check("rm -rf ~")[1] == "deny"
assert check('bash -lc "rm -rf /"')[1] == "deny"
assert check('echo "rm -rf /"') == (None, None)
assert check("git checkout -- src/app.py") == (None, None)
assert check("git checkout -- .")[1] == "ask"
assert check("ls -la") == (None, None)
assert check(None) == (None, None)
assert modes.parse_command("/honey ultra strict") == ["ultra", "strict"]
assert modes.parse_command("honey off") == ["off"]
assert modes.parse_command("stop honey.") == ["off"]
assert modes.parse_command("add a normal mode toggle") is None
assert modes.parse_command("/honey how do I debug this") is None
assert modes.parse_command("honey default lite") == ["default", "lite"]
print("guard+modes ok")
