#!/usr/bin/env python3
"""Ranked search over the work trios (executions + frontmatter).

Returns POINTERS (work_id · status · summary · path:line), not content — the
agent then opens only the 2-3 relevant trios. Replaces re-reading the whole _index.md.

Repo-structure-agnostic: works for single-repo and monorepo projects alike; it only
depends on the `<vault>/work/` layout, where <vault> is the `*_wiki` knowledge vault.

Usage:
  python3 find.py <terms...> [--root <repo>] [--vault <name>] [--top N] [--topic T] [--status S]

Ranking: match in title/summary/topic (weight 3) > match in the body (weight 1);
recency (updated) breaks ties. Case-insensitive, all terms (AND) by default.
"""
import argparse
import glob
import os
import re
import sys

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "work-index"))
try:
    from generate import parse_frontmatter, find_vault, DATE_SLUG  # reuse the canonical parser
except Exception:  # minimal fallback
    def parse_frontmatter(_):  # noqa
        return {}

    def find_vault(_root):  # noqa
        return None

    DATE_SLUG = re.compile(r"^\d{4}-\d{2}-\d{2}_")


def read(path):
    with open(path, encoding="utf-8", errors="replace") as f:
        return f.read()


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("terms", nargs="+")
    ap.add_argument("--root", default=os.getcwd())
    ap.add_argument("--vault", default=None)
    ap.add_argument("--top", type=int, default=8)
    ap.add_argument("--topic", default=None)
    ap.add_argument("--status", default=None)
    args = ap.parse_args()
    terms = [t.lower() for t in args.terms]

    vault = args.vault or find_vault(args.root)
    if not vault:
        sys.exit("no *_wiki vault found under --root; pass --vault <name>")

    trios = {}
    for kind in ("tasks", "plans", "executions"):
        for path in glob.glob(os.path.join(args.root, vault, "work", kind, "*.md")):
            name = os.path.basename(path)
            if name.startswith("_") or not DATE_SLUG.match(name):
                continue
            wid = name[:-3]
            trios.setdefault(wid, {})[kind[:-1]] = path

    results = []
    for wid, arts in trios.items():
        task_fm = parse_frontmatter(read(arts["task"])) if "task" in arts else {}
        ex_path = arts.get("execution")
        ex_fm = parse_frontmatter(read(ex_path)) if ex_path else {}
        pl_path = arts.get("plan")
        pl_fm = parse_frontmatter(read(pl_path)) if pl_path else {}
        # Same chain as generate.py:trio_view. A sub-trio has no task, so without the
        # plan's/execution's own title the summary degrades to the raw work_id.
        summary = (ex_fm.get("summary") or task_fm.get("summary") or pl_fm.get("summary")
                   or task_fm.get("title") or ex_fm.get("title") or pl_fm.get("title")
                   or wid)
        status = task_fm.get("status") or ex_fm.get("status") or "?"
        topics = ex_fm.get("topic") or task_fm.get("topic") or pl_fm.get("topic") or []
        if isinstance(topics, str):
            topics = [topics]
        updated = max([task_fm.get("updated", ""), ex_fm.get("updated", ""),
                       pl_fm.get("updated", "")])

        if args.topic and args.topic.lower() not in [t.lower() for t in topics]:
            continue
        if args.status and status != args.status:
            continue

        head = f"{wid} {summary} {' '.join(topics)}".lower()
        body = read(ex_path).lower() if ex_path else ""
        body += (read(arts["task"]).lower() if "task" in arts else "")
        body += (read(pl_path).lower() if pl_path else "")

        pats = [re.compile(r"(?<!\w)" + re.escape(t) + r"(?!\w)") for t in terms]
        if not all(p.search(head) or p.search(body) for p in pats):
            continue
        score = sum(3 for p in pats if p.search(head)) + sum(1 for p in pats if p.search(body))

        # first body line that matches a term → pointer
        ptr = ""
        if ex_path:
            for i, ln in enumerate(read(ex_path).splitlines(), 1):
                if any(p.search(ln.lower()) for p in pats):
                    ptr = f"executions/{wid}.md:{i}"
                    break
        results.append((score, updated, wid, status, summary, topics, ptr))

    results.sort(key=lambda r: (r[0], r[1]), reverse=True)
    if not results:
        print("no trio matched.", file=sys.stderr)
        return
    for score, updated, wid, status, summary, topics, ptr in results[: args.top]:
        tg = f" [{', '.join(topics)}]" if topics else ""
        print(f"[{status}] {wid}{tg}")
        print(f"    {summary}")
        print(f"    ↳ work/executions/{wid}  {('· ' + ptr) if ptr else ''}")


if __name__ == "__main__":
    main()
