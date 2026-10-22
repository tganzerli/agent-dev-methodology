#!/usr/bin/env bash
# Approved plan gate — mechanizes mandatory_planning_rule.md.
#
# Blocks Edit/Write on code directories unless an approved plan exists in
# {{project}}_wiki/work/plans/{work_id}.md with `status: approved`.
#
# Resolves work_id from:
#   1. Ephemeral branch name: <type>/<work_id>__<scope>
#   2. Local marker file: .claude/active_work.json or .gemini/active_work.json
#
# Escape hatch: SKIP_PLAN_GATE=1
#
# Contract: exit 0 allows; exit 2 blocks and prints stderr to the agent.
set -uo pipefail

exec python3 -c '
import json, os, re, subprocess, sys

def allow():  sys.exit(0)
def block(msg):
    sys.stderr.write(msg + "\n")
    sys.exit(2)

if os.environ.get("SKIP_PLAN_GATE") == "1":
    allow()

try:
    payload = json.load(sys.stdin)
except Exception:
    allow()   # unreadable payload should not wedge development

root = os.environ.get("CLAUDE_PROJECT_DIR") or os.getcwd()
ti = payload.get("tool_input") or {}

paths = []
for key in ("file_path", "notebook_path"):
    if ti.get(key):
        paths.append(ti[key])
for edit in (ti.get("edits") or []):
    if isinstance(edit, dict) and edit.get("file_path"):
        paths.append(edit["file_path"])

# Guarded source code prefixes. Customize per project structure (e.g. src/, lib/, apps/, packages/)
GUARDED = ("src/", "lib/", "apps/", "packages/")
guarded = []
for p in paths:
    rel = os.path.relpath(os.path.abspath(p), root)
    if rel.startswith(GUARDED):
        guarded.append(rel)

if not guarded:
    allow()   # wiki, trios, methodology, and tooling remain free

def current_branch():
    try:
        return subprocess.run(
            ["git", "rev-parse", "--abbrev-ref", "HEAD"],
            cwd=root, capture_output=True, text=True, timeout=5,
        ).stdout.strip()
    except Exception:
        return ""

work_id = None
source = None

m = re.match(r"^[a-z-]+/(\d{4}-\d{2}-\d{2}_[a-z0-9][a-z0-9-]*)__", current_branch())
if m:
    work_id, source = m.group(1), "branch name"
else:
    for candidate_rel in [os.path.join(".claude", "active_work.json"), os.path.join(".gemini", "active_work.json")]:
        marker = os.path.join(root, candidate_rel)
        if os.path.exists(marker):
            try:
                wid = (json.load(open(marker)) or {}).get("work_id")
                if wid:
                    work_id, source = wid, candidate_rel
                    break
            except Exception:
                pass

target = ", ".join(guarded)

# Permanent lines are never renamed into an ephemeral branch.
PERMANENT = re.compile(r"^(main|master|dev|dev_.+|staging_.+|demo_.+|HEAD)$")

if not work_id:
    branch = current_branch() or "?"
    if branch == "?" or PERMANENT.match(branch):
        how = ("Create the ephemeral branch <type>/<work_id>__<scope> from the approved plan "
               "(git_branching_rule.md), or record the active work_id in a marker file.")
    else:
        how = ("If a tool created this branch/worktree for the session, do not create a second one: "
               "once the plan is approved, rename it in place (announce the command):\n"
               "  git branch -m <type>/<work_id>__<scope>\n"
               "only if it sits on the right base line; otherwise create the branch from that line "
               "(git_branching_rule.md, tool-created branches). Or record the active work_id in a marker file.")
    block(
        "PLAN GATE — BLOCKED.\n"
        "Target: " + target + "\n"
        "Could not determine work_id: current branch (" + branch + ") is not "
        "ephemeral <type>/<work_id>__<scope> and no active_work.json exists in .claude/ or .gemini/.\n\n"
        "mandatory_planning_rule.md: no code changes before an approved plan.\n" + how
    )

# Search for plan under {{project}}_wiki/work/plans/{work_id}.md or any *_wiki/work/plans/{work_id}.md
plan_abs = os.path.join(root, "{{project}}_wiki", "work", "plans", work_id + ".md")
plan_rel = os.path.join("{{project}}_wiki", "work", "plans", work_id + ".md")

if not os.path.exists(plan_abs):
    # Fallback search for custom wiki directories
    found = False
    for entry in os.listdir(root):
        if entry.endswith("_wiki"):
            cand = os.path.join(root, entry, "work", "plans", work_id + ".md")
            if os.path.exists(cand):
                plan_abs = cand
                plan_rel = os.path.relpath(cand, root)
                found = True
                break
    if not found:
        block(
            "PLAN GATE — BLOCKED.\n"
            "Target: " + target + "\n"
            "work_id `" + work_id + "` (via " + source + ") has no plan at " + plan_rel + ".\n\n"
            "mandatory_planning_rule.md: no code changes before an approved plan."
        )

status = None
with open(plan_abs, encoding="utf-8") as fh:
    for line in fh:
        s = line.strip()
        if s == "---" and status is not None:
            break
        m = re.match(r"^status:\s*([a-z_]+)", s)
        if m:
            status = m.group(1)
            break

if status != "approved":
    block(
        "PLAN GATE — BLOCKED.\n"
        "Target: " + target + "\n"
        "Plan " + plan_rel + " has status: " + (status or "missing") + " (required: approved).\n\n"
        "mandatory_planning_rule.md: the plan is the source of truth for execution.\n"
        "Request human approval and set frontmatter status to approved before executing."
    )

allow()
'
