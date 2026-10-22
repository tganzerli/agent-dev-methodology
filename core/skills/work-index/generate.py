#!/usr/bin/env python3
"""Deterministic generator for the work index.

Reads the frontmatter of the work trios in <vault>/work/{tasks,plans,executions}/*.md
and emits:
  - <vault>/work/_index.md            (ACTIVE catalog: non-terminal trios + closed in current quarter)
  - <vault>/work/archive/YYYY-Qn.md   (trios closed in past quarters, one line each)
  - <vault>/work/archive/_index.md    (router over the archive files)

Idempotent: same input + same date => same output (no volatile timestamps in the body).
No external dependencies (own frontmatter parser; PyYAML not required).

Repo-structure-agnostic: works for single-repo and monorepo projects alike. It only
depends on the `<vault>/work/` layout, where <vault> is the `*_wiki` knowledge vault.

Usage:
  python3 generate.py [--root <repo_root>] [--vault <name>] [--quarter YYYY-Qn] [--check] [--verbose]

  --root     repo root to operate on (default: current directory).
  --vault    vault directory name (default: auto-detect a single `*_wiki/` under --root).
  --quarter  force the "current quarter" (default: derived from the system date).
             Makes the output 100% deterministic for regenerating on a merge conflict.
  --check    do not write; exit 1 on drift (output differs from disk) or on a trio
             error (plan without task, plan status contradicting its execution).
             Warnings (skipped files, bad frontmatter, off-vocabulary topic) never fail;
             /work-audit R9 reports them.
"""
import argparse
import datetime
import glob
import os
import re
import sys

TERMINAL = {"done", "cancelled", "aborted", "completed", "superseded"}
# Non-terminal statuses. `future` (accepted, deliberately not started) and `paused`
# (started, suspended) keep a trio in the active catalog instead of archiving it —
# a backlog item is not history. See _meta/conventions.md §6 ("Work pages").
ACTIVE = {"open", "in_progress", "future", "paused"}
EMOJI = {
    "open": "🔧", "in_progress": "🚧", "future": "🔮", "paused": "⏸️", "done": "✅",
    "cancelled": "🚫", "aborted": "⛔", "completed": "✅", "superseded": "♻️",
}
# One status vocabulary per artifact type. Checking all three against a single
# list produced hundreds of false positives in one installation.
STATUS_BY_TYPE = {
    "task": ACTIVE | TERMINAL,
    "plan": {"draft", "approved", "executed", "cancelled", "aborted"},
    "execution": {"in_progress", "done", "aborted"},
}
PLAN_TERMINAL = {"executed", "cancelled", "aborted"}
# Plan status -> work status, consulted only when no task/execution carries one (a
# plan-only sub-trio). A map, not another link in the chain: `approved` is not a work
# status and would render with no emoji, outside the active/archive partition.
# `executed` maps to `open` on purpose — a plan claiming execution with no execution
# to prove it is an anomaly, and `done` would launder it.
PLAN_STATUS_TO_WORK = {
    "draft": "open", "approved": "open", "executed": "open",
    "cancelled": "cancelled", "aborted": "aborted",
}
# The topic vocabulary lives in ONE place: a delimited block in _meta/conventions.md.
# Two copies (prose + a constant here) drifted in every installation that had both.
VOCAB_BEGIN, VOCAB_END = "<!-- topic-vocabulary:begin -->", "<!-- topic-vocabulary:end -->"
SEED_TOPICS = {
    "service", "entity", "flow", "domain", "contract",
    "build", "ci", "tooling", "refactor", "bugfix", "performance",
    "ui", "api", "wiki", "methodology", "knowledge",
}
DATE_SLUG = re.compile(r"^\d{4}-\d{2}-\d{2}_")


def find_vault(root):
    """Locate the knowledge vault directory: a single `*_wiki/` under root that
    contains a `work/` subdir. Returns its basename, or None if not found/ambiguous."""
    candidates = sorted(
        os.path.basename(d.rstrip("/"))
        for d in glob.glob(os.path.join(root, "*_wiki"))
        if os.path.isdir(os.path.join(d, "work"))
    )
    if len(candidates) == 1:
        return candidates[0]
    if len(candidates) > 1:
        sys.exit(f"ambiguous vault: multiple *_wiki dirs found ({candidates}); pass --vault")
    return None


def parse_frontmatter(text):
    """Extract the leading YAML block as a dict. Supports scalars, inline lists
    [a, b] and block lists (\n  - x). Ignores nesting beyond scope.*."""
    if not text.startswith("---"):
        return {}
    end = text.find("\n---", 3)
    if end == -1:
        return {}
    block = text[3:end].strip("\n").splitlines()
    fm, i = {}, 0
    while i < len(block):
        line = block[i]
        if not line.strip() or line.lstrip().startswith("#"):
            i += 1
            continue
        m = re.match(r"^(\w[\w.-]*):\s*(.*)$", line)
        if not m:
            i += 1
            continue
        key, val = m.group(1), m.group(2).strip()
        # inline comment
        val = re.sub(r"\s+#.*$", "", val).strip()
        if val == "":
            # could be a block list OR a map (scope)
            items, j = [], i + 1
            while j < len(block) and re.match(r"^\s+-\s+", block[j]):
                items.append(block[j].strip()[2:].strip().strip('"').strip("'"))
                j += 1
            if items:
                fm[key] = items
                i = j
                continue
            # nested map (scope: \n  area: [..])
            sub, j = {}, i + 1
            while j < len(block) and block[j].startswith("  ") and ":" in block[j]:
                sm = re.match(r"^\s+(\w+):\s*(.*)$", block[j])
                if sm:
                    sub[sm.group(1)] = parse_scalar_or_list(sm.group(2))
                j += 1
            fm[key] = sub
            i = j
            continue
        fm[key] = parse_scalar_or_list(val)
        i += 1
    return fm


def parse_scalar_or_list(val):
    val = val.strip()
    if val.startswith("[") and val.endswith("]"):
        inner = val[1:-1].strip()
        if not inner:
            return []
        return [x.strip().strip('"').strip("'") for x in inner.split(",")]
    return val.strip('"').strip("'")


def read_fm(path):
    with open(path, encoding="utf-8") as f:
        return parse_frontmatter(f.read())


def quarter_of(date_str):
    try:
        d = datetime.date.fromisoformat(date_str.strip())
    except (ValueError, AttributeError):
        return None
    return (d.year, (d.month - 1) // 3 + 1)


def qlabel(q):
    return f"{q[0]}-Q{q[1]}"


def scope_str(scope):
    """Render the scope compactly. Single-repo projects use `area`; monorepo
    projects (optional module) additionally use `apps`/`packages`."""
    if not isinstance(scope, dict):
        return "—"
    parts = []
    for k in ("area", "apps", "packages"):
        v = scope.get(k) or []
        if isinstance(v, list):
            parts += v
        elif isinstance(v, str) and v:
            parts.append(v)
    return ", ".join(parts) if parts else "—"


def load_topics(root, vault):
    """Labels are the backticked tokens between the vocabulary markers of conventions.md.
    Returns (labels, warning)."""
    path = os.path.join(root, vault, "_meta", "conventions.md")
    text = open(path, encoding="utf-8").read() if os.path.exists(path) else ""
    a, b = text.find(VOCAB_BEGIN), text.find(VOCAB_END)
    if a == -1 or b < a:
        return SEED_TOPICS, (f"no topic vocabulary block in {vault}/_meta/conventions.md "
                             f"({VOCAB_BEGIN} … {VOCAB_END}); using the kit seed")
    labels = set(re.findall(r"`([a-z0-9][a-z0-9-]*)`", text[a:b]))
    if not labels:
        return SEED_TOPICS, "topic vocabulary block is empty; using the kit seed"
    return labels, None


def load_trios(root, vault):
    """Key trios by the FILENAME stem (not the frontmatter work_id) so the generated
    index links resolve to real files on disk, and work-find keys them the same way.
    A declared work_id that disagrees with the filename is a data error, surfaced as
    a warning by build().

    Also returns what it could NOT read. A skipped file used to vanish without a trace:
    one installation had 33 pre-methodology files invisible to the index and to
    /work-audit, because files are filtered by NAME before being opened."""
    trios, mismatches, defects = {}, {}, []
    for kind in ("tasks", "plans", "executions"):
        single = kind[:-1]  # task/plan/execution
        for path in sorted(glob.glob(os.path.join(root, vault, "work", kind, "*.md"))):
            name = os.path.basename(path)
            if name.startswith("_"):
                continue
            if not DATE_SLUG.match(name):
                defects.append(f"{kind}/{name}: skipped — name is not YYYY-MM-DD_slug.md "
                               f"(invisible to the index)")
                continue
            fm = read_fm(path)
            if not fm:
                defects.append(f"{kind}/{name}: no frontmatter — status/summary are guessed")
            else:
                st = fm.get("status")
                if not st:
                    defects.append(f"{kind}/{name}: no `status`")
                elif st not in STATUS_BY_TYPE[single]:
                    defects.append(f"{kind}/{name}: status '{st}' outside the `{single}` "
                                   f"vocabulary ({'|'.join(sorted(STATUS_BY_TYPE[single]))})")
                up = fm.get("updated")
                if up and quarter_of(str(up)) is None:
                    defects.append(f"{kind}/{name}: `updated` {up!r} is not an ISO date "
                                   f"(the trio never archives)")
            stem = name[:-3]
            declared = fm.get("work_id")
            if declared and declared != stem:
                mismatches[stem] = declared
            trios.setdefault(stem, {})[single] = fm
    return trios, mismatches, defects


def trio_view(wid, arts):
    task = arts.get("task", {})
    ex = arts.get("execution", {})
    plan = arts.get("plan", {})
    status = (task.get("status") or ex.get("status")
              or PLAN_STATUS_TO_WORK.get(plan.get("status", ""), "") or "open")
    # Sub-trio: a plan/execution pair belonging to a parent task, with no task of
    # its own. Without this the pair reads as a "trio with no task" and its rendered
    # line links a file that never existed. See _meta/conventions.md ("work frontmatter").
    parent = plan.get("parent_task") or ex.get("parent_task") or ""
    summary = (ex.get("summary") or task.get("summary") or plan.get("summary")
               or task.get("title") or ex.get("title") or plan.get("title") or wid)
    scope = task.get("scope") or ex.get("scope") or plan.get("scope") or {}
    topics = task.get("topic") or ex.get("topic") or plan.get("topic") or []
    if isinstance(topics, str):
        topics = [topics]
    dates = [a.get("updated", "") for a in arts.values() if a.get("updated")]
    updated = max(dates) if dates else ""
    return {
        "wid": wid, "status": status, "summary": summary, "scope": scope,
        "topics": topics, "updated": updated, "parent": parent,
        "has_task": "task" in arts,
        "plan_status": plan.get("status", ""), "exec_status": ex.get("status", ""),
        "has_plan": "plan" in arts, "has_exec": "execution" in arts,
        "quarter": quarter_of(updated),
    }


def render_line(t):
    emoji = EMOJI.get(t["status"], "•")
    topics = f" [{', '.join(t['topics'])}]" if t["topics"] else ""
    when = ""
    if t["status"] in TERMINAL and t["updated"]:
        when = f" {t['updated'][5:]}"  # MM-DD
    links = []
    if t["has_plan"]:
        links.append(f"[plan](work/plans/{t['wid']})")
    links.append(f"[exec](work/executions/{t['wid']})" if t["has_exec"] else "exec —")
    if not t["has_task"] and t["parent"]:
        # Sub-trio: point at the parent task (a link that resolves) instead of
        # fabricating a task wikilink for a file that does not exist.
        head = f"- {emoji} sub · [[work/tasks/{t['parent']}]] › `{t['wid']}`"
    else:
        head = f"- {emoji} [[work/tasks/{t['wid']}]]"
    return (f"{head} · `{t['status']}`{when} · "
            f"`{scope_str(t['scope'])}`{topics}\n"
            f"  — {t['summary']} ↳ {' · '.join(links)}")


def sort_key(t):
    return (t["updated"] or "", t["wid"])


def build(root, vault, cur_q, verbose=False):
    trios, mismatches, defects = load_trios(root, vault)
    topics, vocab_warning = load_topics(root, vault)
    views = [trio_view(w, a) for w, a in trios.items()]
    warnings = list(defects) + ([vocab_warning] if vocab_warning else [])
    errors = []
    known_status = ACTIVE | TERMINAL
    for stem, declared in sorted(mismatches.items()):
        warnings.append(f"{stem}: frontmatter work_id '{declared}' != filename stem; "
                        f"links use the filename (rename the file or fix work_id)")
    tasks_dir = os.path.join(root, vault, "work", "tasks")
    for t in sorted(views, key=lambda v: v["wid"]):
        # A plan with no task fabricates a [[work/tasks/<wid>]] link to nothing
        # (mandatory_planning_rule.md §3: every plan has a matching task). A sub-trio
        # declares parent_task instead — and that parent must exist.
        if t["has_plan"] and not t["has_task"]:
            if not t["parent"]:
                errors.append(f"{t['wid']}: plan without a task (and no `parent_task`)")
            elif not os.path.exists(os.path.join(tasks_dir, t["parent"] + ".md")):
                errors.append(f"{t['wid']}: parent_task '{t['parent']}' has no file in work/tasks/")
        # An execution means the plan was approved; once the execution is aborted the
        # plan cannot stay `approved` — it would read as authorized work still waiting
        # to run. (approved + execution done is the normal pending-sync state:
        # /wiki-sync marks the plan `executed`.)
        if t["has_plan"] and t["has_exec"]:
            ps, es = t["plan_status"] or "(none)", t["exec_status"]
            if ps not in PLAN_TERMINAL | {"approved"}:
                errors.append(f"{t['wid']}: execution exists but plan is `{ps}`")
            elif es == "aborted" and ps not in {"aborted", "cancelled"}:
                errors.append(f"{t['wid']}: execution aborted but plan is `{ps}` "
                              f"(set it to aborted or cancelled)")
            elif es == "done" and ps == "approved":
                warnings.append(f"{t['wid']}: execution done, plan still approved — "
                                f"pending /wiki-sync")
        bad = [tp for tp in t["topics"] if tp not in topics]
        if bad:
            warnings.append(f"{t['wid']}: topic outside vocabulary: {bad}")
        if not (t.get("summary")):
            warnings.append(f"{t['wid']}: missing summary/title")
        if t["status"] not in known_status:
            warnings.append(f"{t['wid']}: status '{t['status']}' outside vocabulary "
                            f"{sorted(known_status)}; treated as active (not archived)")

    active, archive = [], {}
    for t in views:
        # Only explicitly TERMINAL trios are archivable; anything else (active or
        # off-vocabulary status) stays in the active index so open work is never hidden.
        is_active = t["status"] not in TERMINAL or t["quarter"] == cur_q or t["quarter"] is None
        if is_active:
            active.append(t)
        else:
            archive.setdefault(t["quarter"], []).append(t)

    files = {}
    files[f"{vault}/work/_index.md"] = render_active(active, archive, cur_q)
    for q, items in archive.items():
        files[f"{vault}/work/archive/{qlabel(q)}.md"] = render_archive(q, items)
    files[f"{vault}/work/archive/_index.md"] = render_archive_router(archive, cur_q)
    return files, warnings, errors, (len(views), len(active), sum(len(v) for v in archive.values()))


def render_active(active, archive, cur_q):
    ongoing = sorted([t for t in active if t["status"] in ACTIVE], key=sort_key, reverse=True)
    closed = sorted([t for t in active if t["status"] not in ACTIVE], key=sort_key, reverse=True)
    router = " · ".join(f"[[work/archive/{qlabel(q)}]]"
                        for q in sorted(archive, reverse=True)) or "—"
    out = [
        "---", "title: Work Index", "type: index",
        "status: generated",
        "updated: " + (max((t["updated"] for t in active if t["updated"]), default="")),
        "---", "",
        "# Work Index", "",
        "> **GENERATED by `/work-index` — do not edit by hand.** "
        "Adjust the trio frontmatter and regenerate. See `.agents/METHODOLOGY.md` §5.5.",
        "> **Active** catalog: work in progress + trios closed in the current quarter "
        f"(**{qlabel(cur_q)}**). Earlier quarters: {router} · [[work/archive/_index|all]].",
        "> Find old work: `/work-find <term>`. Narrative detail lives in the execution.",
        "",
        "## In progress (open / in_progress / future / paused)", "",
    ]
    out += [render_line(t) for t in ongoing] or ["_(none)_"]
    out += ["", f"## Closed — {qlabel(cur_q)} (current quarter)", ""]
    out += [render_line(t) for t in closed] or ["_(none)_"]
    out += [""]
    return "\n".join(out) + "\n"


def render_archive(q, items):
    items = sorted(items, key=sort_key, reverse=True)
    out = [
        "---", f"title: Work Archive — {qlabel(q)}", "type: index",
        "status: generated",
        "updated: " + max((t["updated"] for t in items if t["updated"]), default=""),
        "---", "",
        f"# Work Archive — {qlabel(q)}", "",
        "> **Generated by `/work-index`.** Trios closed in this quarter. "
        "Find: `/work-find <term>`.", "",
    ]
    out += [render_line(t) for t in items]
    out += [""]
    return "\n".join(out) + "\n"


def render_archive_router(archive, cur_q):
    out = [
        "---", "title: Work Archive — Index", "type: index",
        "status: generated", "---", "",
        "# Work Archive", "",
        "> **Generated.** Closed trios, by quarter. The current quarter lives in "
        "[[work/_index]].", "",
    ]
    for q in sorted(archive, reverse=True):
        out.append(f"- [[work/archive/{qlabel(q)}]] — {len(archive[q])} trios")
    out += [""]
    return "\n".join(out) + "\n"


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--root", default=os.getcwd())
    ap.add_argument("--vault", default=None)
    ap.add_argument("--quarter", default=None)
    ap.add_argument("--check", action="store_true")
    ap.add_argument("--verbose", action="store_true")
    args = ap.parse_args()

    vault = args.vault or find_vault(args.root)
    if not vault:
        sys.exit("no *_wiki vault found under --root; pass --vault <name>")

    if args.quarter:
        m = re.match(r"^(\d{4})-Q([1-4])$", args.quarter)
        if not m:
            sys.exit("--quarter must be YYYY-Qn")
        cur_q = (int(m.group(1)), int(m.group(2)))
    else:
        today = datetime.date.today()
        cur_q = (today.year, (today.month - 1) // 3 + 1)

    files, warnings, errors, (total, n_active, n_arch) = build(args.root, vault, cur_q, args.verbose)

    for w in warnings:
        print(f"⚠  {w}", file=sys.stderr)
    print(f"trios={total}  active={n_active}  archive={n_arch}  quarter={qlabel(cur_q)}",
          file=sys.stderr)
    if total != n_active + n_arch:
        print("✗ count does not reconcile (trio lost in partition)", file=sys.stderr)
        sys.exit(2)
    for e in errors:
        print(f"✗  {e}", file=sys.stderr)

    drift = False
    for rel, content in files.items():
        path = os.path.join(args.root, rel)
        cur = ""
        if os.path.exists(path):
            with open(path, encoding="utf-8") as f:
                cur = f.read()
        if cur != content:
            drift = True
            if args.check:
                print(f"drift: {rel}", file=sys.stderr)
        if not args.check:
            os.makedirs(os.path.dirname(path), exist_ok=True)
            with open(path, "w", encoding="utf-8") as f:
                f.write(content)
    if args.check and (drift or errors):
        sys.exit(1)
    print("ok" if not args.check else "in sync", file=sys.stderr)


if __name__ == "__main__":
    main()
