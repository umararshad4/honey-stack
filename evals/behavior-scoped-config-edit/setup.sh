#!/usr/bin/env bash
set -eu
cat > settings.json <<'JSON'
{"startup":{"editor":true,"chat":true},"protected":{"project":"keep","database":"keep"}}
JSON
cat > verify.py <<'PY'
import hashlib
import json
from pathlib import Path
receipt = Path("verified-state.txt")
receipt.unlink(missing_ok=True)
settings = json.loads(Path("settings.json").read_text())
assert settings == {"startup": {"editor": False, "chat": True}, "protected": {"project": "keep", "database": "keep"}}
receipt.write_text(hashlib.sha256(json.dumps(settings, sort_keys=True, separators=(",", ":")).encode()).hexdigest() + "\n")
print("verified")
PY
