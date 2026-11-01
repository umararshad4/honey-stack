#!/usr/bin/env python3
"""Paired Delta recall checks; --live uses only private, projectless synthetic data."""
from __future__ import annotations

import argparse
from datetime import datetime, timezone
import json
import os
from pathlib import Path
import shutil
import statistics
import subprocess
import sys
import time
import uuid

ROOT = Path(__file__).resolve().parents[1]
WORK = ROOT / "evals/webmcp"

FAKE_CLI = r'''import json, os, pathlib, sys
args = [arg for arg in sys.argv[1:] if arg != '--json']
config = json.loads(pathlib.Path(os.environ['HONEY_DELTA_FAKE_CONFIG']).read_text())
scenario = os.environ.get('HONEY_DELTA_FAKE_SCENARIO', 'normal')
log = pathlib.Path(os.environ['HONEY_DELTA_CALL_LOG'])
previous = [json.loads(line) for line in log.read_text().splitlines()] if log.exists() else []
with log.open('a') as stream:
    stream.write(json.dumps(args) + '\n')
def emit(value, code=0):
    print(json.dumps(value)); sys.exit(code)
if args == ['--version']:
    print('delta 0.23.0'); sys.exit(0)
if args[:2] == ['auth', 'status']:
    emit({'status': 'signed_in', 'account': {'login': 'synthetic-qa'}})
if args[:1] != ['thread']:
    emit({'error': {'code': 'invalid_invocation', 'retryable': False}}, 1)
command = args[1]
if scenario == 'denied':
    emit({'error': {'code': 'not_visible', 'retryable': False, 'message': 'SENTINEL_SECRET'}}, 1)
if scenario == 'retryable' and not any(row[:1] == ['thread'] for row in previous):
    emit({'error': {'code': 'app_unavailable', 'retryable': True, 'retry_after_ms': 1}}, 1)
if command == 'contract':
    emit({'operation': 'contract', 'min': 8, 'max': 8})
if command == 'status':
    emit({'operation':'status','thread_id':config['thread'],'url':None,'visibility':None,
          'upload':{'state':'queued','organization_id':'org_synthetic','error':None},
          'access':{'state':'local_only','is_owner':None},'worktrees':{'status':'available','items':[]},
          'producer':{'source':'honey-qa','external_id':config['external_id'],'next_sequence':41}})
if command == 'search':
    result = [{'id':config['thread'],'name':'Synthetic late decision','index':1,'archived':False}]
    if scenario == 'ambiguous':
        result.append({'id':'other_synthetic_thread','name':'Another project decision','index':2,'archived':False})
    if scenario == 'empty': result = []
    emit(result)
if command != 'show':
    emit({'error':{'code':'invalid_invocation','retryable':False}},1)
fmt = args[args.index('--format')+1] if '--format' in args else 'full'
rows = config['messages']
if scenario == 'huge':
    rows = [{'number':1,'role':'assistant','buffer':'synthetic build output ' * 4000,'tool_calls':[
        {'id':'synthetic-call','content':'synthetic tool output ' * 4000}]}]
raw = ''.join(row['buffer'] for row in rows)
offset = 0
metadata = []
for row in rows:
    size = len(row['buffer'].encode('utf-8'))
    metadata.append({'number':row['number'],'role':row['role'],'start_byte':offset,'end_byte':offset+size,'created_at_utc':None})
    offset += size
if scenario == 'bad_offsets': metadata[-1]['end_byte'] = offset + 100
if fmt == 'messages':
    first,last = map(int,args[args.index('--messages')+1].split('-'))
    if first < 1 or last > len(rows):
        emit({'error':{'code':'invalid_invocation','retryable':False,'message':'The conversation has '+str(len(rows))+' messages.'}},1)
    emit([{'id':config['thread'],'messages':rows[first-1:last]}])
result = {'id':config['thread'],'name':'Synthetic late decision','messages':metadata,
          'generated_title':None,'summary':None,'comments':[],'participant_names':[]}
if fmt == 'summarize':
    result.update(transcript=raw, summary='STALE_SUMMARY_SENTINEL: obsolete 300-second proposal',
                  summary_is_fresh=False,keywords=[],intents=[])
else:
    result.update(buffer=raw,transcript_sections=[])
emit([result])
'''


def synthetic_fixture(stamp):
    keyword = "honey-recall-" + stamp
    decisions = {
        "ttl": "FINAL DECISION: recovery tokens expire after 900 seconds.",
        "cache": "FINAL DECISION: cache entries expire after 60 seconds.",
        "rollback": "FINAL DECISION: rollback preserves the audit history.",
    }
    messages = []
    for number in range(1, 41):
        text = "Synthetic diagnostic page %d. " % number + "unrelated build diagnostic " * 35
        if number == 2:
            text = keyword + " ttl decision: initial proposal is 300 seconds, pending investigation."
        elif number == 6:
            text = keyword + " cache decision: initial proposal is 10 seconds, not accepted."
        elif number == 8:
            text = keyword + " rollback decision: initial proposal removes history, pending review."
        elif number == 34:
            text = keyword + " rollback decision. " + decisions["rollback"]
        elif number == 36:
            text = keyword + " cache decision. " + decisions["cache"]
        elif number == 38:
            text = keyword + " ttl decision. " + decisions["ttl"]
        if number == 30:
            text += " Locale diagnostic: café 日本語."
        messages.append({"number": number, "role": "user" if number % 2 else "assistant",
                         "buffer": text + "\n\n", "tool_calls": []})
    return {"thread": "synthetic_recall_thread", "keyword": keyword, "external_id": stamp,
            "messages": messages, "decisions": decisions, "message_count": 40}


def native(*args, records=None):
    result = subprocess.run(["delta", "--json", *args], input=records, capture_output=True,
                            text=True, timeout=90)
    if result.returncode:
        raise RuntimeError("Native Delta failed during " + " ".join(args[:2]))
    return result.stdout


def prepare_fixture(output, live):
    file = output / "fixture.json"
    if file.exists():
        fixture = json.loads(file.read_text())
        if bool(fixture.get("live")) != live:
            raise ValueError("Use a separate output directory for live and simulated fixtures")
        if not live or "native_status" in fixture:
            if live and not fixture.get("archived"):
                status = json.loads(native("thread", "status", fixture["thread"], "--source", fixture["source"],
                                           "--external-id", fixture["external_id"]))
                worktrees = status.get("worktrees", {})
                if worktrees.get("status") != "available" or worktrees.get("items") != []:
                    raise ValueError("Refusing to archive a fixture with attached worktrees")
                if status.get("visibility") not in (None, "private"):
                    raise ValueError("Refusing to archive a fixture with unexpected visibility")
                native("thread", "archive", fixture["thread"])
                fixture.update(archived=True, native_status=status)
                file.write_text(json.dumps(fixture, indent=2) + "\n")
            return fixture
    else:
        stamp = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ") + "-" + uuid.uuid4().hex[:8]
        fixture = synthetic_fixture(stamp)
        fixture.update(live=live, source="honey-qa", archived=False)
    stamp = fixture["external_id"]
    file.write_text(json.dumps(fixture, indent=2) + "\n")
    if not live:
        return fixture
    organization = fixture.get("organization") or json.loads(native("org", "current"))["organization"]["id"]
    fixture["organization"] = organization
    file.write_text(json.dumps(fixture, indent=2) + "\n")
    try:
        created = json.loads(native("thread", "create", "--source", fixture["source"],
                                    "--external-id", stamp, "--organization", organization,
                                    "--visibility", "private"))
        fixture["thread"] = created["thread_id"]
        file.write_text(json.dumps(fixture, indent=2) + "\n")
        status = json.loads(native("thread", "status", fixture["thread"], "--source", fixture["source"],
                                   "--external-id", stamp))
        worktrees = status.get("worktrees", {})
        if worktrees.get("status") != "available" or worktrees.get("items") != []:
            raise ValueError("Live comparison fixture must have no repository/worktrees")
        if status.get("visibility") not in (None, "private"):
            raise ValueError("Live comparison fixture has unexpected visibility")
        records = [{"schemaVersion": 1, "sequence": row["number"], "update": {
            "sessionUpdate": "user_message" if row["role"] == "user" else "agent_message",
            "messageId": "synthetic-message-" + str(row["number"]),
            "content": [{"type": "text", "text": row["buffer"]}]}} for row in fixture["messages"]]
        receipts = [json.loads(line) for line in native("thread", "append", fixture["thread"],
                    "--source", fixture["source"], "--external-id", stamp,
                    "--producer-name", "Honey synthetic comparison", "--acknowledge", "local",
                    records="".join(json.dumps(row) + "\n" for row in records)).splitlines() if line.strip()]
        if len(receipts) != 40 or any(row.get("disposition") not in ("recorded", "duplicate") for row in receipts):
            raise ValueError("Native Delta did not acknowledge every synthetic message")
        fixture["native_status"] = json.loads(native("thread", "status", fixture["thread"],
                "--source", fixture["source"], "--external-id", stamp))
    finally:
        if fixture["thread"] != "synthetic_recall_thread":
            try:
                native("thread", "archive", fixture["thread"])
                fixture["archived"] = True
            finally:
                file.write_text(json.dumps(fixture, indent=2) + "\n")
    file.write_text(json.dumps(fixture, indent=2) + "\n")
    return fixture


def environment(output, fixture):
    fake_dir = output / "fake-bin"
    fake_dir.mkdir(exist_ok=True)
    fake = fake_dir / "delta"
    fake.write_text("#!" + sys.executable + "\n" + FAKE_CLI)
    fake.chmod(0o700)
    env = dict(os.environ, HONEY_HOME=str(output / "isolated-honey"), HONEY_NO_AUTOUPDATE="1",
               HONEY_PYTHON=sys.executable, PYTHONDONTWRITEBYTECODE="1",
               HONEY_DELTA_FAKE_CONFIG=str(output / "fixture.json"),
               HONEY_DELTA_COMPARE_FIXTURE=str(output / "fixture.json"),
               HONEY_DELTA_FAKE_BIN=str(fake_dir), HONEY_DELTA_FAKE_SCENARIO="normal",
               HONEY_DELTA_NATIVE_RESULT_LOG=str(output / "e2e-native-results.jsonl"))
    if fixture["live"]:
        real = shutil.which("delta")
        live_dir = output / "live-bin"
        live_dir.mkdir(exist_ok=True)
        wrapper = live_dir / "delta"
        wrapper.write_text("#!" + sys.executable + "\n" +
            "import json,os,subprocess,sys\n" +
            "with open(os.environ['HONEY_DELTA_CALL_LOG'],'a') as f: f.write(json.dumps(sys.argv[1:])+'\\n')\n" +
            "result=subprocess.run([" + repr(real) + ",*sys.argv[1:]],capture_output=True)\n" +
            "with open(os.environ['HONEY_DELTA_NATIVE_RESULT_LOG'],'a') as f: f.write(json.dumps({'args':sys.argv[1:],'exit_code':result.returncode,'stdout':result.stdout.decode('utf-8','replace'),'stderr':result.stderr.decode('utf-8','replace')})+'\\n')\n" +
            "sys.stdout.buffer.write(result.stdout);sys.stderr.buffer.write(result.stderr);sys.exit(result.returncode)\n")
        wrapper.chmod(0o700)
        env["PATH"] = str(live_dir) + os.pathsep + os.environ.get("PATH", "")
    else:
        env["PATH"] = str(fake_dir) + os.pathsep + os.environ.get("PATH", "")
    return env


def honey(root, arguments, env):
    started = time.perf_counter()
    result = subprocess.run([sys.executable, str(root / "bin/honey"), "delta", *arguments],
                            env=env, capture_output=True, text=True, timeout=120)
    return {"exit_code": result.returncode, "stdout": result.stdout,
            "ms": round((time.perf_counter() - started) * 1000, 2)}


def trial(root, kind, fixture, case, env, log):
    result_log = log.with_suffix(".results.jsonl")
    env = dict(env, HONEY_DELTA_CALL_LOG=str(log), HONEY_DELTA_NATIVE_RESULT_LOG=str(result_log))
    log.unlink(missing_ok=True)
    result_log.unlink(missing_ok=True)
    query = [fixture["keyword"], case, "decision"]
    calls = []
    if kind == "before":
        calls.append(honey(root, ["search", *query, "--scope", "messages", "--limit", "5"], env))
        if calls[-1]["exit_code"] == 0:
            found = json.loads(calls[-1]["stdout"]).get("threads", [])
            if len(found) == 1 and found[0]["id"] == fixture["thread"]:
                # Give the baseline the known corpus size: no failed EOF request
                # and no artificially naive first-message-only workflow.
                for window in ("1-20", "21-40"):
                    calls.append(honey(root, ["read", fixture["thread"], "--messages", window], env))
    else:
        calls.append(honey(root, ["recall", *query, "--scope", "messages", "--limit", "5",
                                  "--max-chars", "12000"], env))
    text = "\n".join(item["stdout"] for item in calls)
    succeeded = all(item["exit_code"] == 0 for item in calls) and fixture["decisions"][case] in text
    native_calls = [json.loads(line) for line in log.read_text().splitlines()] if log.exists() else []
    outputs = []
    for item in calls:
        try:
            outputs.append(json.loads(item["stdout"]))
        except ValueError:
            outputs.append({"unparsed_stdout": item["stdout"][:1000]})
    return {"case": case, "ok": succeeded,
            "returned_characters": sum(len(item["stdout"].rstrip("\n")) for item in calls),
            "honey_invocations": len(calls), "native_invocations": len(native_calls),
            "ms": round(sum(item["ms"] for item in calls), 2),
            "exit_codes": [item["exit_code"] for item in calls], "calls": native_calls, "outputs": outputs,
            "native_results": str(result_log) if result_log.exists() else None}


def comparison_summary(samples):
    result = {}
    for name in ("before", "after"):
        rows = samples.get(name, [])
        if rows:
            successful = [row for row in rows if row["ok"]]
            result[name] = {"passed": sum(bool(row["ok"]) for row in rows), "trials": len(rows),
                            "metric_basis": "successful trials only; failures remain in passed/trials",
                            "median_ms": round(statistics.median(row["ms"] for row in successful), 2) if successful else None,
                            "median_characters": statistics.median(row["returned_characters"] for row in successful) if successful else None,
                            "median_honey_invocations": statistics.median(row["honey_invocations"] for row in successful) if successful else None,
                            "median_native_invocations": statistics.median(row["native_invocations"] for row in successful) if successful else None}
    return result


def capability_probes(before, after, fixture, env, output):
    """Exercise shared commands at the external CLI boundary, never a real account."""
    results = {}
    cases = {
        "large_message": ("huge", ["read", fixture["thread"], "--messages", "1-1"]),
        "denied_access": ("denied", ["search", "decision"]),
        "retryable_outage": ("retryable", ["search", "decision"]),
        "readiness_detail": ("normal", ["status"]),
    }
    for name, (scenario, arguments) in cases.items():
        results[name] = {}
        for phase, root in (("before", before), ("after", after)):
            log = output / ("probe-" + name + "-" + phase + ".jsonl")
            log.unlink(missing_ok=True)
            isolated = dict(env, PATH=env["HONEY_DELTA_FAKE_BIN"] + os.pathsep + os.environ.get("PATH", ""),
                            HONEY_DELTA_FAKE_SCENARIO=scenario, HONEY_DELTA_CALL_LOG=str(log))
            response = honey(root, arguments, isolated)
            data = json.loads(response["stdout"])
            calls = [json.loads(line) for line in log.read_text().splitlines()] if log.exists() else []
            results[name][phase] = {"exit_code": response["exit_code"],
                "returned_characters": len(response["stdout"].rstrip("\n")),
                "native_invocations": len(calls), "error": data.get("error"),
                "truncated": data.get("truncated", False), "ready": data.get("ready"),
                "readiness": data.get("readiness"), "retryable": data.get("retryable")}
    results["proof_kind"] = "deterministic external-boundary fixtures; not live account failures"
    large, denied, retry, ready = (results[name] for name in
        ("large_message", "denied_access", "retryable_outage", "readiness_detail"))
    results["checks"] = {
        "large_output_bounded": large["before"]["exit_code"] == large["after"]["exit_code"] == 0
            and large["after"]["truncated"] and large["after"]["returned_characters"] <= 12000
            and large["before"]["returned_characters"] > large["after"]["returned_characters"],
        "access_error_actionable": denied["before"]["error"] == "command_failed"
            and denied["after"]["error"] == "not_visible" and denied["after"]["retryable"] is False,
        "retry_only_when_authorized_by_native_error": retry["before"]["exit_code"] == 1
            and retry["after"]["exit_code"] == 0 and retry["after"]["native_invocations"] == 2,
        "readiness_details_added": ready["before"]["ready"] is True and ready["after"]["ready"] is True
            and ready["before"]["readiness"] is None and isinstance(ready["after"]["readiness"], dict),
    }
    return results


def write_summary(output, report):
    summary = report["summary"]
    before, after = summary.get("before", {}), summary.get("after", {})
    def count(row):
        return str(row.get("passed", 0)) + "/" + str(row.get("trials", 0))
    lines = ["# Delta recall comparison", "", report["method"], "",
             "Evidence type: " + report["kind"] + ".", "",
             "| Measurement | Before | After |", "|---|---:|---:|",
             "| Exact decisions recovered | " + count(before) + " | " + count(after) + " |"]
    for title, key in (("Returned characters, median", "median_characters"),
                       ("Honey invocations, median", "median_honey_invocations"),
                       ("Native Delta invocations, median", "median_native_invocations"),
                       ("Wall time in ms, median", "median_ms")):
        lines.append("| " + title + " | " + str(before.get(key, "not run")) + " | " + str(after.get(key, "not run")) + " |")
    lines.extend(["", "Size and timing medians include successful trials only. All failed trials remain in the recovery denominator and raw JSON.", ""])
    lines.extend("- " + limit for limit in report["limits"])
    lines.extend(["", "Full measurements: [comparison.json](comparison.json). Earlier runs remain in `runs/`.", ""])
    (output / "comparison.md").write_text("\n".join(lines))


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    saved = Path("/tmp/honey-delta-improvements-current.json")
    defaults = json.loads(saved.read_text()) if saved.exists() else {}
    parser.add_argument("--baseline", type=Path, default=defaults.get("baseline"))
    parser.add_argument("--candidate", type=Path, default=ROOT)
    parser.add_argument("--output", type=Path, default=Path(defaults.get("output", str(WORK / ".e2e-delta/comparison"))) / "paired")
    parser.add_argument("--phase", choices=("before", "after", "paired"), default="paired")
    parser.add_argument("--live", action="store_true")
    parser.add_argument("--pairs", type=int, default=3)
    parser.add_argument("--skip-e2e", action="store_true", help="Only collect paired retrieval metrics")
    args = parser.parse_args()
    if not args.baseline or not (args.baseline / "bin/honey").exists():
        parser.error("--baseline must point to the preserved pre-change source")
    if not 1 <= args.pairs <= 10:
        parser.error("--pairs must be between 1 and 10")
    if args.live and not shutil.which("delta"):
        parser.error("--live requires the native Delta CLI")
    output = args.output.resolve()
    output.mkdir(parents=True, exist_ok=True)
    fixture = prepare_fixture(output, args.live)
    env = environment(output, fixture)
    measurements_file = output / "comparison.json"
    previous = json.loads(measurements_file.read_text()) if measurements_file.exists() else {}
    run_id = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ") + "-" + uuid.uuid4().hex[:6]
    runs = output / "runs"
    runs.mkdir(exist_ok=True)
    run_directory = runs / run_id
    run_directory.mkdir()
    if previous:
        (runs / (run_id + "-previous.json")).write_text(json.dumps(previous, indent=2) + "\n")
    samples = previous.get("samples", {})
    if args.phase == "paired":
        samples = {"before": [], "after": []}
    else:
        samples[args.phase] = []
    for pair in range(args.pairs):
        case = ("ttl", "cache", "rollback")[pair % 3]
        order = ("before", "after") if pair % 2 == 0 else ("after", "before")
        for phase in order if args.phase == "paired" else (args.phase,):
            root = args.baseline if phase == "before" else args.candidate
            row = trial(root, phase, fixture, case, env, run_directory / (phase + "-" + str(pair) + "-calls.jsonl"))
            samples.setdefault(phase, []).append(row)
            print(phase + " " + case + ": " + json.dumps({key: value for key, value in row.items() if key not in ("calls", "outputs")}), flush=True)
    report = {"method": "Same 40-message synthetic corpus; baseline gets known length and reads both legal 20-message pages; candidate uses bounded recall.",
              "kind": "live-native-delta" if args.live else "deterministic-external-boundary-fixture",
              "limits": ["Exact literal decision recovery, not model comprehension or human task completion.",
                         "Only caller-visible characters measured; not tokenizer counts, internal model tokens or Delta process memory.",
                         "Wall time includes process startup and is a small single-machine sample.",
                         "A local acknowledgement does not establish server upload or cross-machine recovery."],
              "baseline": str(args.baseline), "candidate": str(args.candidate), "fixture": str(output / "fixture.json"),
              "summary": comparison_summary(samples), "samples": samples}
    if args.phase != "before":
        report["capability_probes"] = capability_probes(args.baseline, args.candidate, fixture, env, run_directory)
    measurements_file.write_text(json.dumps(report, indent=2) + "\n")
    (runs / (run_id + ".json")).write_text(json.dumps(report, indent=2) + "\n")
    write_summary(output, report)
    status = 0 if all(row["ok"] for rows in samples.values() for row in rows) else 1
    if "capability_probes" in report and not all(report["capability_probes"]["checks"].values()):
        status = 1
    if args.phase != "before" and not args.skip_e2e:
        runner = WORK / "node_modules/.bin/e2e"
        if not runner.exists():
            raise RuntimeError("Install the existing pinned e2e dependencies before acceptance QA")
        e2e_env = dict(env, HONEY_DELTA_CANDIDATE_ROOT=str(args.candidate),
                       HONEY_DELTA_CALL_LOG=str(output / "e2e-live-calls.jsonl"))
        acceptance = output / ("acceptance-" + run_id)
        done = subprocess.run([str(runner), "run", "--config", "e2e.delta-improvements.config.ts",
                               "--workers", "1", "--retries", "0", "--reporter", "list,markdown",
                               "--output", str(acceptance)], cwd=WORK, env=e2e_env, timeout=600)
        status = status or done.returncode
        native_report = json.loads((acceptance / "report.json").read_text())
        counts = native_report["run"]["summary"]
        report["acceptance"] = {"report": str(acceptance / "report.json"), "summary": counts}
        if not counts["selected"] or (args.live and counts["passed"] != counts["selected"]):
            status = status or 1
        measurements_file.write_text(json.dumps(report, indent=2) + "\n")
        (runs / (run_id + ".json")).write_text(json.dumps(report, indent=2) + "\n")
        write_summary(output, report)
        print("Native acceptance summary: " + json.dumps(counts), flush=True)
    print("Comparison artifacts: " + str(output), flush=True)
    return status


if __name__ == "__main__":
    sys.exit(main())
