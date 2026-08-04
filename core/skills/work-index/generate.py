#!/usr/bin/env python3
"""Deterministic generator for the work index.

Reads the frontmatter of the work trios in <vault>/work/{tasks,plans,executions}/*.md
and emits:
  - <vault>/work/_index.md            (ACTIVE catalog: open/in_progress + closed in current quarter)
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
  --check    do not write; exit 1 if the output diverges from what is on disk (drift).
"""
import argparse
import datetime
import glob
import os
import re
import sys

TERMINAL = {"done", "cancelled", "aborted", "completed", "superseded"}
ACTIVE = {"open", "in_progress"}
EMOJI = {
    "open": "🔧", "in_progress": "🚧", "done": "✅",
    "cancelled": "🚫", "aborted": "⛔", "completed": "✅", "superseded": "♻️",
}
# Seed vocabulary — small and generic. Extend it in _meta/conventions.md §4
# ("work frontmatter") before using a new label; the generator warns on off-vocabulary topics.
VALID_TOPICS = {
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


def load_trios(root, vault):
    """Key trios by the FILENAME stem (not the frontmatter work_id) so the generated
    index links resolve to real files on disk, and work-find keys them the same way.
    A declared work_id that disagrees with the filename is a data error, surfaced as
    a warning by build()."""
    trios, mismatches = {}, {}
    for kind in ("tasks", "plans", "executions"):
        for path in sorted(glob.glob(os.path.join(root, vault, "work", kind, "*.md"))):
            name = os.path.basename(path)
            if name.startswith("_") or not DATE_SLUG.match(name):
                continue
            fm = read_fm(path)
            stem = name[:-3]
            declared = fm.get("work_id")
            if declared and declared != stem:
                mismatches[stem] = declared
            trios.setdefault(stem, {})[kind[:-1]] = fm  # task/plan/execution
    return trios, mismatches


def trio_view(wid, arts):
    task = arts.get("task", {})
    ex = arts.get("execution", {})
    plan = arts.get("plan", {})
    status = task.get("status") or ex.get("status") or "open"
    summary = (ex.get("summary") or task.get("summary")
               or plan.get("summary") or task.get("title") or wid)
    scope = task.get("scope") or ex.get("scope") or plan.get("scope") or {}
    topics = task.get("topic") or ex.get("topic") or plan.get("topic") or []
    if isinstance(topics, str):
        topics = [topics]
    dates = [a.get("updated", "") for a in arts.values() if a.get("updated")]
    updated = max(dates) if dates else ""
    return {
        "wid": wid, "status": status, "summary": summary, "scope": scope,
        "topics": topics, "updated": updated,
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
    return (f"- {emoji} [[work/tasks/{t['wid']}]] · `{t['status']}`{when} · "
            f"`{scope_str(t['scope'])}`{topics}\n"
            f"  — {t['summary']} ↳ {' · '.join(links)}")


def sort_key(t):
    return (t["updated"] or "", t["wid"])


def build(root, vault, cur_q, verbose=False):
    trios, mismatches = load_trios(root, vault)
    views = [trio_view(w, a) for w, a in trios.items()]
    warnings = []
    known_status = ACTIVE | TERMINAL
    for stem, declared in sorted(mismatches.items()):
        warnings.append(f"{stem}: frontmatter work_id '{declared}' != filename stem; "
                        f"links use the filename (rename the file or fix work_id)")
    for t in views:
        bad = [tp for tp in t["topics"] if tp not in VALID_TOPICS]
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
    return files, warnings, (len(views), len(active), sum(len(v) for v in archive.values()))


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
        "## In progress (open / in_progress)", "",
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

    files, warnings, (total, n_active, n_arch) = build(args.root, vault, cur_q, args.verbose)

    for w in warnings:
        print(f"⚠  {w}", file=sys.stderr)
    print(f"trios={total}  active={n_active}  archive={n_arch}  quarter={qlabel(cur_q)}",
          file=sys.stderr)
    if total != n_active + n_arch:
        print("✗ count does not reconcile (trio lost in partition)", file=sys.stderr)
        sys.exit(2)

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
    if args.check and drift:
        sys.exit(1)
    print("ok" if not args.check else "in sync", file=sys.stderr)


if __name__ == "__main__":
    main()
