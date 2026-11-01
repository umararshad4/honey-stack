"""Verified Delta references attached to the handoff skill's existing human summary."""
from datetime import datetime, timezone
import argparse
import hashlib
import json
from pathlib import Path
import re
import subprocess

from honey import delta, paths

MARKER = re.compile(r"\n<!-- honey-delta:v1\n(.*?)\n-->\n?", re.S)


def _git(root, *args, optional=False):
    result = subprocess.run(["git", "-C", str(root), *args], capture_output=True, timeout=10)
    if result.returncode and not optional:
        raise delta.DeltaError("invalid_project", "Handoff provenance requires a readable Git checkout.")
    return result.stdout if result.returncode == 0 else b""


def _sha(path):
    digest = hashlib.sha256()
    if path.stat().st_size > 64 * 1024 * 1024:
        raise delta.DeltaError("evidence_too_large", "An evidence file exceeds 64 MiB; reference a smaller report.")
    with path.open("rb") as stream:
        for block in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def _state(root, handoff):
    names = sorted(set(_git(root, "ls-files", "--cached", "--others", "--exclude-standard", "-z").split(b"\0")) - {b""})
    if len(names) > 20000:
        raise delta.DeltaError("project_too_large", "Handoff fingerprint exceeds 20,000 source files.")
    digest = hashlib.sha256(_git(root, "ls-files", "--stage", "-z"))
    total = 0
    for name in names:
        path = root / name.decode("utf-8", errors="surrogateescape")
        if path.absolute() == handoff.absolute():
            continue
        digest.update(name + b"\0")
        if path.is_symlink():
            digest.update(b"symlink:" + str(path.readlink()).encode())
        elif path.is_file():
            total += path.stat().st_size
            if total > 64 * 1024 * 1024:
                raise delta.DeltaError("project_too_large", "Handoff fingerprint exceeds 64 MiB of source.")
            digest.update(str(path.stat().st_mode).encode() + b":" + _sha(path).encode())
        else:
            digest.update(b"deleted")
    return {"head": _git(root, "rev-parse", "--verify", "HEAD", optional=True).decode().strip() or None,
            "branch": _git(root, "symbolic-ref", "--short", "HEAD", optional=True).decode().strip() or None,
            "state_sha256": digest.hexdigest(), "repository": paths.project_slug(str(root))}


def _document(file):
    path = Path(file).absolute()
    if path.is_symlink() or not path.is_file() or path.stat().st_size > 1024 * 1024:
        raise delta.DeltaError("invalid_handoff", "Use a regular handoff file smaller than 1 MiB.")
    try:
        return path, path.read_text(encoding="utf-8")
    except UnicodeError:
        raise delta.DeltaError("invalid_handoff", "The handoff must contain UTF-8 text.") from None


def _history(reference, messages, source, external_id):
    result = {"available": False, "cloud": {"state": "unverified", "url": None}}
    try:
        read = delta.read_thread(reference, messages)
        result.update(available=True, thread=read["thread"], messages=read["messages"], transcript=read["transcript"])
        if source and external_id:
            result["cloud"] = delta.thread_status(reference, source, external_id)
    except delta.DeltaError as exc:
        if not result["available"]:
            result.update(exc.payload())
        else:
            result["cloud_error"] = exc.payload()
    return result


def attach(file, reference, project=None, source=None, external_id=None, messages="1-1", evidence=()):
    path, original = _document(file)
    if len(MARKER.findall(original)) > 1:
        raise delta.DeltaError("invalid_handoff", "The handoff contains multiple Delta metadata blocks.")
    root = delta.project_root(project)
    records = []
    for item in evidence:
        target = Path(item).absolute()
        try:
            relative = str(target.relative_to(root))
        except ValueError:
            relative = str(target)
        records.append({"path": relative, "sha256": _sha(target)})
    history = _history(reference, messages, source, external_id)
    record = {"schema": 1, "reference": reference, "source": source, "external_id": external_id,
              "thread": history.get("thread"), "messages": messages,
              "recorded_at": datetime.now(timezone.utc).isoformat(), "git": _state(root, path),
              "evidence": records, "verified_at_attach": history["available"]}
    body = MARKER.sub("", original)
    encoded = json.dumps(record, ensure_ascii=True, indent=2).replace(">", "\\u003e")
    delta.write_private(path, body + "\n<!-- honey-delta:v1\n" + encoded + "\n-->\n")
    return {"attached": True, "file": str(path), "history_available": history["available"],
            "cloud": history["cloud"], "historical_evidence": records, "git": record["git"]}


def restore(file, project=None, max_chars=12000):
    path, document = _document(file)
    blocks = MARKER.findall(document)
    if len(blocks) != 1:
        raise delta.DeltaError("invalid_handoff", "The handoff needs exactly one Delta metadata block.")
    try:
        record = json.loads(blocks[0])
        if (not isinstance(record, dict) or record.get("schema") != 1
                or not isinstance(record.get("git"), dict) or not isinstance(record.get("evidence"), list)):
            raise ValueError()
        reference = delta._reference(record["reference"])
        messages = delta._window(record["messages"])
        if bool(record.get("source")) != bool(record.get("external_id")):
            raise ValueError()
        if record.get("source"):
            delta._identity(record["source"])
            delta._identity(record["external_id"])
        for item in record["evidence"]:
            if (not isinstance(item, dict) or not isinstance(item.get("path"), str)
                    or not re.fullmatch(r"[a-f0-9]{64}", item.get("sha256", ""))):
                raise ValueError()
    except (ValueError, TypeError, KeyError, argparse.ArgumentTypeError):
        raise delta.DeltaError("invalid_handoff", "Delta handoff metadata is invalid; keep the human summary.") from None
    root = delta.project_root(project)
    current = _state(root, path)
    evidence = []
    for item in record["evidence"]:
        target = Path(item["path"])
        target = target if target.is_absolute() else root / target
        state = "missing" if not target.is_file() else "unchanged" if _sha(target) == item["sha256"] else "changed"
        evidence.append({"path": item["path"], "status": state})
    result = {"file": str(path), "local_handoff": MARKER.sub("", document),
              "recorded_at": record.get("recorded_at"), "evidence_kind": "historical_not_fresh_verification",
              "git": {"head_matches": current["head"] == record["git"].get("head"),
                      "branch_matches": current["branch"] == record["git"].get("branch"),
                      "worktree_matches": current["state_sha256"] == record["git"].get("state_sha256")},
              "evidence": evidence,
              "history": _history(reference, messages, record.get("source"), record.get("external_id"))}
    return delta.bounded(result, max_chars)
