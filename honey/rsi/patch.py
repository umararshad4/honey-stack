"""Tier 2: eval-gated skill patches.

skill flagged by its scorecard → LLM drafts ≤3 exact hunks + a regression eval case from the real failure → applied in a
git worktree on branch rsi/<skill>-<date> of the honey-stack repo (never the installed copy) → `claude plugin eval`
before and after → kept only if the patch fixes the regression case and regresses nothing → proposal for /rsi review.
Validated application fast-forwards the source checkout and runs `honey sync`.
"""
from __future__ import annotations

import glob
import json
import os
import re
import shutil
import subprocess
import time

from honey import paths
from honey.rsi import curate, review, store, text
from honey.rsi.coach import skill_status

HERE = os.path.dirname(os.path.abspath(__file__))
MAX_PER_WEEK, MAX_HUNKS, MAX_LINES = 2, 3, 15
PATCH_USD, EVAL_USD = 0.50, 0.50

SCHEMA = {"type": "object", "additionalProperties": False, "required": ["hunks", "rationale", "case"], "properties": {
    "hunks": {"type": "array", "maxItems": MAX_HUNKS, "items": {"type": "object", "additionalProperties": False, "required": ["old", "new"],
              "properties": {"old": {"type": "string", "maxLength": 1500}, "new": {"type": "string", "maxLength": 1800}}}},
    "rationale": {"type": "string", "maxLength": 400},
    "case": {"type": "object", "additionalProperties": False, "required": ["prompt", "should_fire", "reply_regex"],
             "properties": {"prompt": {"type": "string", "maxLength": 800}, "should_fire": {"type": "boolean"},
                            "reply_regex": {"type": "string", "maxLength": 120}}}}}


def git(*args, cwd=None, check=True):
    cwd = paths.source_repo() if cwd is None else cwd
    r = subprocess.run(["git", "-C", cwd, *args], capture_output=True, text=True, timeout=120)
    if check and r.returncode != 0:
        raise RuntimeError(f"git {' '.join(args)}: {r.stderr.strip()[-300:]}")
    return r.stdout.strip()


def candidates() -> list:
    sc = store.read_json(paths.path("scorecards.json"), {}) or {}
    out = []
    for name, c in sc.items():
        st = skill_status(c)
        if st in ("patch-candidate", "desc-fix") and os.path.exists(os.path.join(paths.source_repo(), "skills", name, "SKILL.md")):
            if c.get("patched_at") and curate._days(c["patched_at"]) < 14:
                continue  # give the last patch time to show its effect
            out.append((name, st))
    return out


def evidence_for(skill: str, limit: int = 6) -> list:
    """Redacted user turns that followed a bad outcome of this skill."""
    out = []
    for fp in sorted(glob.glob(paths.path("events", "*", "*.jsonl")), key=os.path.getmtime, reverse=True):
        rows = store.read_jsonl(fp)
        bad = {r.get("t") for r in rows if r.get("e") == "skill_outcome" and r.get("name", "").split(":")[-1] == skill
               and r.get("outcome") in ("neg", "misfire")}
        for r in rows:
            if r.get("e") == "prompt" and r.get("q") and (r.get("t") in bad or any(t < r.get("t", 0) <= t + 3 for t in bad)):
                out.append(r["q"])
        if len(out) >= limit:
            break
    return out[:limit]


def apply_hunks(src: str, hunks: list) -> str:
    changed = 0
    for h in hunks:
        old, new = h.get("old", ""), h.get("new", "")
        if not old or src.count(old) != 1:
            raise ValueError("hunk 'old' text must occur exactly once")
        changed += max(len(old.splitlines()), len(new.splitlines()))
        src = src.replace(old, new, 1)
    if changed > MAX_LINES * 2:
        raise ValueError("patch too large")
    return src


def write_case(root: str, skill: str, case: dict) -> str:
    name = f"rsi-{skill}-{time.strftime('%Y%m%d%H%M')}"
    d = os.path.join(root, "evals", name, "graders")
    os.makedirs(d, exist_ok=True)
    with open(os.path.join(root, "evals", name, "prompt.md"), "w") as f:
        f.write(f"---\nmax_turns: 4\ntags: [rsi, {skill}]\nallowed_tools: [Read, Glob, Grep, Skill]\n---\n\n{case['prompt'].strip()}\n")
    rx = '"skill"\\s*:\\s*"(?:[\\w-]+:)?' + re.escape(skill) + '"'
    fire = f"---\ntype: tool_used\ntool: Skill\ninput_match: '{rx}'\n" + ("" if case["should_fire"] else "min: 0\nmax: 0\n") + "arm: both\n---\n"
    with open(os.path.join(d, "trigger.md"), "w") as f:
        f.write(fire)
    if case.get("reply_regex"):
        try:
            re.compile(case["reply_regex"])
            with open(os.path.join(d, "reply.md"), "w") as f:
                f.write(f"---\ntype: regex\npattern: {json.dumps(case['reply_regex'])}\nflags: i\n---\n")
        except re.error:
            pass
    return name


def run_eval(root: str, glob_: str, out: str) -> dict:
    exe = shutil.which("claude") or os.path.expanduser("~/.local/bin/claude")
    env = dict(os.environ, RSI_CHILD="1")
    subprocess.run([exe, "plugin", "eval", root, "--case", glob_, "--runs", "1", "--ablation", "none", "--max-cost-usd", str(EVAL_USD),
                    "--no-publish", "--trust-plugin", "--json", out], capture_output=True, text=True, timeout=900, env=env)
    d = store.read_json(out, {}) or {}
    scores = {c["name"]: (c.get("arms", {}).get("with") or [{}])[0].get("score") for c in d.get("cases", [])}
    store.append_jsonl(paths.path("costs.jsonl"), {"ts": text.now(), "job": "eval", "engine": "claude", "usd": d.get("costUsd"), "ok": bool(scores)})
    return scores


def propose(skill: str, status: str, upstream_note: str = "") -> dict:
    from honey.rsi import reflect
    if git("status", "--porcelain", "--", "skills", check=False):
        return {"skipped": "skills/ has uncommitted changes"}
    if reflect.budget_block("claude"):
        return {"skipped": "budget"}
    fp = os.path.join(paths.source_repo(), "skills", skill, "SKILL.md")
    with open(fp, encoding="utf-8") as f:
        src = f.read()
    sc = (store.read_json(paths.path("scorecards.json"), {}) or {}).get(skill, {})
    notes = curate.skill_notes(skill)
    ev = evidence_for(skill)
    with open(os.path.join(HERE, "prompts", "patcher.md"), encoding="utf-8") as f:
        system = f.read()
    user = (f"SKILL {skill} status={status} scorecard={json.dumps(sc)}\n\nEVIDENCE (user turns after bad outcomes):\n"
            + "\n".join(f"- {q}" for q in ev) + (f"\n\nLEARNED NOTES:\n{notes}" if notes else "")
            + (f"\n\nUPSTREAM CHANGE TO CONSIDER:\n{upstream_note}" if upstream_note else "") + f"\n\nSKILL.md:\n{src}")
    result, usd, eng = reflect.call_llm(system, user, SCHEMA, PATCH_USD, model="sonnet")
    store.append_jsonl(paths.path("costs.jsonl"), {"ts": text.now(), "job": "patch", "engine": eng, "usd": usd, "sid": skill, "ok": True})
    if not result.get("hunks"):
        return {"skipped": "no skill problem: " + result.get("rationale", "")[:120]}
    new_src = apply_hunks(src, result["hunks"])
    if text.injection_hit(new_src.replace(src, "")) or text.injection_hit(json.dumps(result["hunks"])):
        return {"skipped": "patch rejected by injection scan"}
    date = time.strftime("%Y%m%d%H%M")
    branch, wt = f"rsi/{skill}-{date}", os.path.join(paths.source_repo(), ".worktrees", f"rsi-{skill}-{date}")
    git("worktree", "add", "-q", wt, "-b", branch)
    case = write_case(wt, skill, result["case"])
    glob_ = "*" + skill + "*"
    res_dir = paths.path("evals", f"{skill}-{date}")
    os.makedirs(res_dir, exist_ok=True)
    before = run_eval(wt, glob_, os.path.join(res_dir, "before.json"))
    with open(os.path.join(wt, "skills", skill, "SKILL.md"), "w", encoding="utf-8") as f:
        f.write(new_src)
    after = run_eval(wt, glob_, os.path.join(res_dir, "after.json"))
    regress = [c for c in before if (after.get(c) or 0) < (before.get(c) or 0)]
    fixed = (after.get(case) or 0) >= 1 and (before.get(case) or 0) < 1
    diff = git("diff", "--", f"skills/{skill}/SKILL.md", cwd=wt, check=False)
    if regress or not fixed:
        git("worktree", "remove", "--force", wt, check=False)
        git("branch", "-D", branch, check=False)
        why = f"regressed {regress}" if regress else ("old skill already passes the regression case" if (before.get(case) or 0) >= 1 else "patch did not fix the case")
        store.append_jsonl(paths.path("logs", "patches.jsonl"), {"ts": text.now(), "skill": skill, "result": "dropped", "why": why, "before": before, "after": after})
        return {"dropped": why}
    git("add", "-A", cwd=wt)
    git("commit", "-q", "-m", f"rsi: patch {skill} skill ({status})\n\n{result['rationale'][:300]}", cwd=wt)
    p = review.add(2, "skill_patch", f"Patch the {skill} skill ({status})", result["rationale"][:400],
                   f"Fast-forward main to {branch}, then honey sync.", [{"q": q} for q in ev[:3]], f"patch:{skill}:{date}")
    p.update(branch=branch, worktree=wt, patch_sha=git("rev-parse", "HEAD", cwd=wt), diff=diff[:6000], eval={"before": before, "after": after, "case": case})
    store.write_json(paths.path("proposals", p["id"] + ".json"), p)
    sc_all = store.read_json(paths.path("scorecards.json"), {}) or {}
    sc_all.setdefault(skill, {})["patched_at"] = text.now()
    store.write_json(paths.path("scorecards.json"), sc_all, sort=True)
    return {"proposed": p["id"]}


def _validate_eval(p: dict) -> None:
    evidence = p.get("eval")
    if not isinstance(evidence, dict):
        raise ValueError("patch has no stored eval evidence")
    before, after, case = evidence.get("before"), evidence.get("after"), evidence.get("case")
    if not isinstance(before, dict) or not isinstance(after, dict) or not isinstance(case, str) or case not in before or case not in after:
        raise ValueError("patch regression case is absent from eval evidence")
    if not before or not set(before).issubset(after):
        raise ValueError("patch eval omits prior cases")
    for scores in (before, after):
        if any(type(v) not in (int, float) or not 0 <= v <= 1 for v in scores.values()):
            raise ValueError("patch eval contains missing or invalid scores")
    if before[case] >= 1 or after[case] < 1 or any(after[c] < v for c, v in before.items()):
        raise ValueError("patch eval did not fix the regression without regressing prior cases")


def accept(p: dict) -> str:
    _validate_eval(p)
    if not isinstance(p.get("branch"), str) or not p["branch"].startswith("rsi/"):
        raise ValueError("patch has no supported RSI branch")
    if git("status", "--porcelain", check=False):
        raise ValueError("honey-stack repo has uncommitted changes; commit or stash them, then decide again")
    head = git("rev-parse", "HEAD")
    patch_sha = git("rev-parse", "--verify", p["branch"] + "^{commit}")
    if p.get("patch_sha") and p["patch_sha"] != patch_sha:
        raise ValueError("patch branch changed since evaluation")
    state = p.get("application") or {}
    if state.get("state") == "sync_pending":
        if head != state.get("merged_sha") or patch_sha != head:
            raise ValueError("source checkout changed after the partial application; inspect it before retrying sync")
    else:
        if git("merge-base", "HEAD", p["branch"]) != head:
            raise ValueError("source checkout diverged from the evaluated patch")
        git("merge", "--ff-only", "-q", p["branch"])
        p["application"] = {"state": "sync_pending", "merged_sha": git("rev-parse", "HEAD"), "updated": text.now()}
        store.write_json(paths.path("proposals", p["id"] + ".json"), p)
    from honey import install
    try:
        rc = install.sync(install.Env())
        if rc != 0:
            raise RuntimeError(f"honey sync failed with exit status {rc}")
    except Exception as exc:
        p["application"].update(state="sync_pending", updated=text.now(), error=str(exc)[:300])
        store.write_json(paths.path("proposals", p["id"] + ".json"), p)
        raise RuntimeError("patch merged locally but sync failed; retry application to sync: " + str(exc)) from exc
    p["application"].update(state="applied", updated=text.now())
    p["application"].pop("error", None)
    store.write_json(paths.path("proposals", p["id"] + ".json"), p)
    if p.get("worktree"):
        git("worktree", "remove", p["worktree"], check=False)
    return f"merged {p['branch']} and synced Codex; Claude picks it up next session or after /reload-plugins"


def discard(p: dict) -> None:
    if p.get("worktree"):
        git("worktree", "remove", "--force", p["worktree"], check=False)
    if p.get("branch"):
        git("branch", "-D", p["branch"], check=False)


def run_weekly() -> list:
    done = []
    for skill, status in candidates()[:MAX_PER_WEEK]:
        try:
            done.append((skill, propose(skill, status)))
        except Exception as e:
            done.append((skill, {"error": str(e)[:200]}))
    return done
