"""Every skill carries a `reviewed:` date so stale version-specific facts get caught. Warns (doesn't fail) when old."""
import datetime
import glob
import os
import re

REPO = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
STALE_DAYS = 365
today = datetime.date.today()
missing, stale = [], []
for f in sorted(glob.glob(os.path.join(REPO, "skills", "*", "SKILL.md"))):
    name = os.path.basename(os.path.dirname(f))
    m = re.search(r'^\s*reviewed:\s*"?(\d{4}-\d{2}-\d{2})"?', open(f, encoding="utf-8").read(), re.M)
    if not m:
        missing.append(name)
        continue
    age = (today - datetime.date.fromisoformat(m.group(1))).days
    if age > STALE_DAYS:
        stale.append(f"{name} ({age}d)")
assert not missing, f"skills missing a reviewed: date: {missing}"
print(f"freshness ok: all skills stamped" + (f"; STALE (>1y, refresh facts): {stale}" if stale else ""))
