#!/usr/bin/env python3
"""Edit ONE row of the live lock table in <vault>/work/relay/_locks.md.

Exists so the diff is bounded by a machine, not by judgement: that is what the
named live-state exception in the branching rule promises when it drops the
per-act human gate. It knows exactly two things - append a row and remove a
row - and never touches the file's protocol prose.

The lock table is the FIRST markdown table after the frontmatter (the "How to
fill it" table comes later). Language-neutral: header text is not matched, and
the placeholder row is any row whose cells after the first are all dashes.

Standard library only.
"""
import argparse
import datetime
import os
import re
import sys

DEFAULT_EMPTY_ROW = "| _(none)_ | — | — | — | — | — |"
SEP_RE = re.compile(r"^\|[\s:|-]+\|$")
DASHES = {"—", "–", "-", ""}
# A cell cannot hold `|` (breaks the table) or a newline.
CELL_RE = re.compile(r"^[^|\n]+$")


def die(msg):
    print(f"scope-lock: {msg}", file=sys.stderr)
    sys.exit(2)


def split_row(line):
    return [c.strip() for c in line.strip().strip("|").split("|")]


def is_placeholder(line):
    cells = split_row(line)
    return len(cells) > 1 and all(c in DASHES for c in cells[1:])


def find_table(lines):
    """Return (first_row, after_last_row) of the lock table."""
    i = 0
    if lines and lines[0].strip() == "---":
        i = next((j + 1 for j in range(1, len(lines)) if lines[j].strip() == "---"), 0)
    for i in range(i, len(lines) - 1):
        if lines[i].lstrip().startswith("|") and SEP_RE.match(lines[i + 1].strip()):
            start = end = i + 2
            while end < len(lines) and lines[end].lstrip().startswith("|"):
                end += 1
            return start, end
    die("lock table not found - the file diverged from the expected format")


def bump_updated(lines):
    today = datetime.date.today().isoformat()
    for i, line in enumerate(lines[:40]):
        if line.startswith("updated:"):
            lines[i] = f"updated: {today}"
            return
    die("frontmatter has no `updated:`")


def op_take(rows, args):
    for r in rows:
        cells = split_row(r)
        if cells[0] == args.scope:
            die(f"scope `{args.scope}` already held by `{cells[1]}` ({cells[2]}) - "
                "this is a collision; resolve it through the intra-team `conflict` "
                "flow, never by overwriting the row")
    for name, value in (("scope", args.scope), ("owner", args.owner),
                        ("work-id", args.work_id), ("until", args.until),
                        ("source", args.source)):
        if not value or not CELL_RE.match(value):
            die(f"--{name} is empty or contains `|` / a newline: {value!r}")
    return rows + [f"| {args.scope} | {args.owner} | {args.work_id} | "
                   f"{args.state} | {args.until} | {args.source} |"]


def op_release(rows, args):
    kept = [r for r in rows if split_row(r)[0] != args.scope]
    if len(kept) == len(rows):
        die(f"scope `{args.scope}` is not in the table - nothing to release")
    return kept


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--file", required=True)
    ap.add_argument("--op", required=True, choices=["take", "release"])
    ap.add_argument("--scope", required=True)
    ap.add_argument("--owner")
    ap.add_argument("--work-id", dest="work_id")
    ap.add_argument("--state", default="held", choices=["held", "releasing"])
    ap.add_argument("--until")
    ap.add_argument("--source")
    args = ap.parse_args()

    if not os.path.isfile(args.file):
        die(f"{args.file} does not exist")
    with open(args.file, encoding="utf-8") as f:
        lines = f.read().split("\n")

    start, end = find_table(lines)
    placeholders = [r for r in lines[start:end] if is_placeholder(r)]
    empty_row = placeholders[0] if placeholders else DEFAULT_EMPTY_ROW
    rows = [r for r in lines[start:end] if r.strip() and not is_placeholder(r)]

    rows = op_take(rows, args) if args.op == "take" else op_release(rows, args)
    lines[start:end] = rows or [empty_row]
    bump_updated(lines)
    with open(args.file, "w", encoding="utf-8") as f:
        f.write("\n".join(lines))
    print(f"scope-lock: {args.op} ok - {len(rows)} lock(s) in the table")


if __name__ == "__main__":
    main()
