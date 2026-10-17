"""Hard gate: the model-invoked skill-listing footprint stays within budget, and no description is truncated.

Claude truncates description+when_to_use at 1536 chars per skill, and the whole listing shares ~1% of the context
window with every other installed skill. Keeping honey lean leaves room for the user's other skills and for new honey
skills. This test fails CI if a new/edited skill blows either limit.
"""
import glob
import os
import re
import sys

REPO = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
TOTAL_BUDGET = 3500   # honey's own ceiling for all model-invoked descriptions (conservative; the hard per-skill cap is 1536)
PER_SKILL = 1536      # Claude truncates description (+when_to_use) here

total = 0
problems = []
for f in sorted(glob.glob(os.path.join(REPO, "skills", "*", "SKILL.md"))):
    fm = open(f, encoding="utf-8").read().split("---")[1]
    if "disable-model-invocation: true" in fm:
        continue
    m = re.search(r"^description:\s*(.*)$", fm, re.M)
    d = (m.group(1).strip().strip('"') if m else "")
    wtu = re.search(r"^when_to_use:\s*(.*)$", fm, re.M)
    per = len(d) + (len(wtu.group(1)) if wtu else 0)
    total += len(d)
    if per > PER_SKILL:
        problems.append(f"{os.path.basename(os.path.dirname(f))}: {per} > {PER_SKILL} (will be truncated)")

if total > TOTAL_BUDGET:
    problems.append(f"model-invoked descriptions total {total} > {TOTAL_BUDGET}. Trim a description, or convert a "
                    f"rarely-auto-triggered skill to user-invoked (disable-model-invocation: true).")
if problems:
    print("BUDGET FAIL:\n  " + "\n  ".join(problems))
    sys.exit(1)
print(f"budget ok: {total}/{TOTAL_BUDGET} chars across model-invoked skills")
