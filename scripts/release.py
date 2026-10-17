#!/usr/bin/env python3
"""Cut a release: bump the version everywhere, roll CHANGELOG's Unreleased section, test, commit and tag.

  python3 scripts/release.py 0.3.0          # bump, test, commit "release: v0.3.0", tag v0.3.0
  python3 scripts/release.py 0.3.0 --push   # …and push the commit and tag (GitHub Actions publishes the release)
  python3 scripts/release.py --check        # versions consistent? (CI)

Semantic versioning: MAJOR for breaking changes (hook commands, data layout, CLI), MINOR for new skills or RSI
features, PATCH for fixes. Hook command strings are frozen; changing them is MAJOR (Codex re-trust).
"""
import datetime
import json
import os
import re
import subprocess
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
JSON_FILES = (".claude-plugin/plugin.json", ".codex-plugin/plugin.json")
INIT = "honey/__init__.py"
SEMVER = re.compile(r"^\d+\.\d+\.\d+$")


def read(p):
    with open(os.path.join(ROOT, p), encoding="utf-8") as f:
        return f.read()


def write(p, s):
    with open(os.path.join(ROOT, p), "w", encoding="utf-8") as f:
        f.write(s)


def versions():
    v = {p: json.loads(read(p))["version"] for p in JSON_FILES}
    v[INIT] = re.search(r'__version__ = "([^"]+)"', read(INIT)).group(1)
    return v


def check():
    v = versions()
    if len(set(v.values())) != 1:
        sys.exit(f"version mismatch: {v}")
    tag = os.environ.get("GITHUB_REF_NAME", "")
    if tag.startswith("v") and tag[1:] != next(iter(v.values())):
        sys.exit(f"tag {tag} does not match version {next(iter(v.values()))}")
    print("version", next(iter(v.values())), "consistent")


def notes(version):
    """The CHANGELOG section for one version (used as GitHub release notes)."""
    m = re.search(rf"^## \[{re.escape(version)}\][^\n]*\n(.*?)(?=^## \[|\Z)", read("CHANGELOG.md"), re.M | re.S)
    return m.group(1).strip() if m else ""


def main(argv):
    if "--check" in argv:
        return check()
    if "--notes" in argv:
        print(notes(argv[argv.index("--notes") + 1]))
        return
    new = next((a for a in argv if SEMVER.match(a)), None)
    if not new:
        sys.exit(__doc__)
    cur = next(iter(versions().values()))
    if tuple(map(int, new.split("."))) <= tuple(map(int, cur.split("."))):
        sys.exit(f"{new} must be greater than {cur}")
    if subprocess.run(["git", "-C", ROOT, "status", "--porcelain"], capture_output=True, text=True).stdout.strip():
        sys.exit("working tree not clean")
    log = read("CHANGELOG.md")
    m = re.search(r"^## \[Unreleased\]\s*\n(.*?)(?=^## \[|\Z)", log, re.M | re.S)
    if not m or not m.group(1).strip():
        sys.exit("CHANGELOG.md has nothing under ## [Unreleased]")
    today = datetime.date.today().isoformat()
    log = log.replace(m.group(0), f"## [Unreleased]\n\n## [{new}] - {today}\n{m.group(1)}", 1)
    base = "https://github.com/umararshad4/honey-stack"
    log = re.sub(r"^\[Unreleased\]: .*$", f"[Unreleased]: {base}/compare/v{new}...HEAD\n[{new}]: {base}/compare/v{cur}...v{new}", log, count=1, flags=re.M)
    write("CHANGELOG.md", log)
    for p in JSON_FILES:
        d = json.loads(read(p))
        d["version"] = new
        write(p, json.dumps(d, indent=2, ensure_ascii=False) + "\n")
    write(INIT, re.sub(r'__version__ = "[^"]+"', f'__version__ = "{new}"', read(INIT)))
    if subprocess.run([sys.executable, os.path.join(ROOT, "tests", "run.py")]).returncode:
        sys.exit("tests failed; release aborted (files are bumped but not committed: git checkout . to undo)")
    subprocess.run(["git", "-C", ROOT, "commit", "-qam", f"release: v{new}"], check=True)
    subprocess.run(["git", "-C", ROOT, "tag", "-a", f"v{new}", "-m", f"v{new}\n\n{notes(new)}"], check=True)
    print(f"tagged v{new}")
    if "--push" in argv:
        subprocess.run(["git", "-C", ROOT, "push", "--follow-tags"], check=True)
    else:
        print("push with: git push --follow-tags")


if __name__ == "__main__":
    main(sys.argv[1:])
