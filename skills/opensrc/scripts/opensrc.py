#!/usr/bin/env python3
"""Build or refresh opensrc/ from package.json: manifest.json, packages/<name>.md stubs, .gitignore entry.

Usage: python3 opensrc.py [--root DIR] [--fetch-metadata]
Stdlib only, Python 3.9+. No network unless --fetch-metadata.
"""
import argparse, datetime, json, os, sys, urllib.parse, urllib.request

PENDING = "- Pending."
META = ("latest", "homepage", "repository", "description", "license")


def read_json(path, default):
    try:
        with open(path, encoding="utf-8") as f:
            return json.load(f)
    except (OSError, ValueError):
        return default


def fetch_meta(name):
    url = "https://registry.npmjs.org/%s/latest" % urllib.parse.quote(name, safe="@")
    try:
        with urllib.request.urlopen(url, timeout=10) as r:
            d = json.load(r)
    except Exception as exc:  # offline, 404, bad JSON: record it and keep going
        return {"metaError": str(exc)[:200]}
    repo = d.get("repository")
    repo = (repo.get("url", "") if isinstance(repo, dict) else str(repo or "")).replace("git+", "")
    repo = repo.replace("git://", "https://").replace("ssh://git@", "https://")
    return {"latest": d.get("version"), "homepage": d.get("homepage"), "description": d.get("description"),
            "license": d.get("license"), "repository": (repo[:-4] if repo.endswith(".git") else repo) or None}


def stub(it):
    lines = ["# " + it["name"], "", "- Declared range: `%s`%s" % (it["range"], " (dev)" if it["dev"] else ""),
             "- npm: " + it["npm"], "- Repository: %s" % (it.get("repository") or "unknown"),
             "- Docs: %s" % (it.get("homepage") or "unknown"), ""]
    for head in ("Key APIs used in this project", "Patterns and constraints", "Version notes"):
        lines += ["## " + head, "", PENDING, ""]
    return "\n".join(lines)


def main(argv):
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("--root", default=".")
    ap.add_argument("--fetch-metadata", action="store_true", help="query registry.npmjs.org per package")
    args = ap.parse_args(argv)
    root = os.path.abspath(args.root)
    pkg = read_json(os.path.join(root, "package.json"), None)
    if not isinstance(pkg, dict):
        print(json.dumps({"ok": False, "error": "no readable package.json in " + root}))
        return 1
    out, man_path = os.path.join(root, "opensrc"), os.path.join(root, "opensrc", "manifest.json")
    os.makedirs(os.path.join(out, "packages"), exist_ok=True)
    old = {p.get("name"): p for p in (read_json(man_path, {}) or {}).get("packages", []) if isinstance(p, dict)}
    deps = {n: (r, True) for n, r in (pkg.get("devDependencies") or {}).items()}
    deps.update({n: (r, False) for n, r in (pkg.get("dependencies") or {}).items()})  # runtime wins over dev
    items, created = [], []
    for name, (rng, dev) in sorted(deps.items()):
        it = {"name": name, "range": rng, "dev": dev, "npm": "https://www.npmjs.com/package/" + name,
              "contextFile": "packages/%s.md" % name.replace("@", "").replace("/", "__")}
        it.update({k: old[name][k] for k in META if old.get(name, {}).get(k)})  # keep metadata on offline refresh
        if args.fetch_metadata:
            it.update({k: v for k, v in fetch_meta(name).items() if v})
        path = os.path.join(out, it["contextFile"])
        if not os.path.exists(path):
            with open(path, "w", encoding="utf-8") as f:
                f.write(stub(it))
            created.append(name)
        with open(path, encoding="utf-8") as f:
            it["status"] = "stub" if PENDING in f.read() else "filled"
        items.append(it)
    now = datetime.datetime.now(datetime.timezone.utc).isoformat(timespec="seconds")
    with open(man_path, "w", encoding="utf-8") as f:
        json.dump({"generatedAt": now, "source": "package.json dependencies + devDependencies",
                   "packages": items}, f, indent=2, sort_keys=True)
        f.write("\n")
    gi = os.path.join(root, ".gitignore")
    lines = open(gi, encoding="utf-8").read().splitlines() if os.path.isfile(gi) else []
    added = not {"opensrc", "opensrc/", "/opensrc", "/opensrc/"} & {l.strip() for l in lines}
    if added:
        with open(gi, "w", encoding="utf-8") as f:
            f.write("\n".join(lines + ["opensrc/"]) + "\n")
    print(json.dumps({"ok": True, "manifest": man_path, "packages": len(items), "stubsCreated": created,
                      "pending": [i["name"] for i in items if i["status"] == "stub"],
                      "metaErrors": [i["name"] for i in items if i.get("metaError")],
                      "removed": sorted(set(old) - set(deps)), "gitignoreAdded": added}, indent=2))
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
