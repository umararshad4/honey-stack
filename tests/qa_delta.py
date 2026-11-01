#!/usr/bin/env python3
"""Run Delta's e2e CLI QA; --live creates and archives a private synthetic thread."""
import argparse
from datetime import datetime, timezone
import json
import os
from pathlib import Path
import shutil
import subprocess
import sys
import tempfile
import uuid


ROOT = Path(__file__).resolve().parents[1]
WORK = ROOT / "evals/webmcp"


def delta(*args, records=None):
    result = subprocess.run(["delta", "--json", *args], input=records, text=True, capture_output=True, timeout=60)
    if result.returncode:
        raise RuntimeError("Delta QA command failed: " + " ".join(args[:2]))
    return result.stdout


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--live", action="store_true", help="Use the signed-in Delta account for a private projectless fixture")
    args = parser.parse_args()
    runner = WORK / "node_modules/.bin/e2e"
    if not runner.exists():
        parser.error("Install the pinned QA dependencies first: cd evals/webmcp && npm ci")
    if args.live and not shutil.which("delta"):
        parser.error("Live QA requires the optional Delta CLI")

    stamp = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ") + "-" + uuid.uuid4().hex[:8]
    output = WORK / ".e2e-delta" / stamp
    thread = None
    archived = False
    observed = {}
    result = 1
    with tempfile.TemporaryDirectory(prefix="honey-delta-qa-") as directory:
        env = dict(os.environ, HONEY_HOME=str(Path(directory) / "home"), HONEY_NO_AUTOUPDATE="1", HONEY_PYTHON=sys.executable)
        env.pop("HONEY_DELTA_QA_FIXTURE", None)
        try:
            if args.live:
                readiness = subprocess.run([sys.executable, str(ROOT / "bin/honey"), "delta", "status"],
                                           env=env, capture_output=True, text=True, check=True, timeout=60)
                if not json.loads(readiness.stdout).get("ready"):
                    raise RuntimeError("Live QA requires a ready, signed-in Delta account")
                organization = json.loads(delta("org", "current"))["organization"]["id"]
                created = json.loads(delta("thread", "create", "--source", "honey-qa", "--external-id", stamp,
                                           "--organization", organization, "--visibility", "private"))
                thread = created["thread_id"]
                print("Created synthetic Delta thread: " + thread, flush=True)
                observed = json.loads(delta("thread", "status", thread, "--source", "honey-qa", "--external-id", stamp))
                if observed.get("worktrees", {}).get("status") != "available" or observed["worktrees"].get("items") != []:
                    raise RuntimeError("Synthetic QA requires a verified projectless thread")
                if observed.get("visibility") not in (None, "private"):
                    raise RuntimeError("Synthetic thread unexpectedly has non-private visibility")
                fixture = {"thread": thread, "keyword": "honey-delta-qa-" + stamp,
                           "request": "Synthetic QA request: honey-delta-qa-" + stamp,
                           "response": "Synthetic QA response: bounded history is available."}
                fixture_file = Path(directory) / "fixture.json"
                fixture_file.write_text(json.dumps(fixture))
                env["HONEY_DELTA_QA_FIXTURE"] = str(fixture_file)
                records = [
                    {"schemaVersion": 1, "sequence": 1, "update": {"sessionUpdate": "user_message", "messageId": "qa-request",
                     "content": [{"type": "text", "text": fixture["request"]}]}},
                    {"schemaVersion": 1, "sequence": 2, "update": {"sessionUpdate": "agent_message", "messageId": "qa-response",
                     "content": [{"type": "text", "text": fixture["response"]}]}},
                ]
                receipts = [json.loads(line) for line in delta("thread", "append", thread, "--source", "honey-qa",
                            "--external-id", stamp, "--producer-name", "Honey synthetic QA", "--acknowledge", "local",
                            records="".join(json.dumps(record) + "\n" for record in records)).splitlines() if line.strip()]
                if len(receipts) != 2 or any(row.get("disposition") not in ("recorded", "duplicate") for row in receipts):
                    raise RuntimeError("Delta did not acknowledge both synthetic messages")
                observed = json.loads(delta("thread", "status", thread, "--source", "honey-qa", "--external-id", stamp))
                print("Local synthetic messages recorded; upload state: " + observed.get("upload", {}).get("state", "unknown"), flush=True)

            completed = subprocess.run([str(runner), "run", "--config", "e2e.delta.config.ts", "--retries", "0",
                                        "--workers", "1", "--reporter", "list,markdown", "--output", str(output)],
                                       cwd=WORK, env=env, timeout=300)
            result = completed.returncode
            report = json.loads((output / "report.json").read_text())
            summary = report["run"]["summary"]
            print("Native e2e counts: " + json.dumps(summary), flush=True)
            if not summary["selected"] or (args.live and summary["passed"] != summary["selected"]):
                result = result or 1
        except (OSError, ValueError, KeyError, RuntimeError, subprocess.SubprocessError) as exc:
            print("Delta QA failed: " + str(exc), file=sys.stderr)
            result = 1
        finally:
            if thread:
                try:
                    delta("thread", "archive", thread)
                    archived = True
                    print("Archived synthetic thread: " + thread, flush=True)
                except (OSError, RuntimeError, subprocess.SubprocessError):
                    print("Could not archive synthetic thread: " + thread, file=sys.stderr)
                    result = 1
            output.mkdir(parents=True, exist_ok=True)
            (output / "fixture-state.json").write_text(json.dumps({"live": args.live, "thread": thread,
                "source": "honey-qa", "external_id": stamp, "requested_visibility": "private" if thread else None,
                "observed_visibility": observed.get("visibility"), "upload": observed.get("upload"),
                "repository_attached": bool(observed["worktrees"]["items"]) if "worktrees" in observed else None,
                "archived": archived}, indent=2) + "\n")
            print("QA artifacts: " + str(output), flush=True)
    return result


if __name__ == "__main__":
    sys.exit(main())
