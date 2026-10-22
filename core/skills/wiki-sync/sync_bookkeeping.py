#!/usr/bin/env python3
"""Mechanical part of /wiki-sync (steps 4-5), without spending LLM context.

Why it exists: the old step "append to `_meta/log.md`" made the agent `Read` + `Edit`
the whole log (it is append-only and only grows — hundreds of KB). Here the entry is
appended straight to the end of the file; its content is never read.

Does, in order:
  1. adds wikilinks of the touched pages to the execution's `related[]`;
  2. appends the entry to `<vault>/_meta/log.md` (pure append);
  3. marks the plan `status: executed` (anchored on `^status:` inside the
     frontmatter, never on a `# status:` comment; a trailing `# a | b` comment
     on the line is kept);
  4. runs `wiki-lint/lint.py --only index-format` on the hand-kept catalogs.

Usage:
  python3 <skills>/wiki-sync/sync_bookkeeping.py WORK_ID \
      --page '<vault>/domains/x.md|UPDATE|short note' \
      --page '<vault>/services/y.md|CREATE' [--date YYYY-MM-DD] [--root .] [--vault NAME] [--dry-run]

WORK_ID = the execution FILE NAME without `.md` (it can differ from the frontmatter work_id).
`--page` = `path|CREATE|UPDATE|APPEND[|note]`; zero `--page` is valid (a trio that creates no pages).
`CREATE` refuses a path already in HEAD. Only touches the execution, the plan and the log.
Vault: auto-detects a single `*_wiki/` under --root (pass --vault if ambiguous).
"""
import argparse
import datetime
import glob
import os
import re
import subprocess
import sys

KINDS = {"CREATE", "UPDATE", "APPEND"}

# `status: <value>` with an optional trailing YAML comment, as the kit templates write it
# (`status: approved   # draft | approved | executed`). Group 1 = `status:` + spacing,
# 2 = the value, 3 = the rest (spacing + comment), kept verbatim on rewrite.
STATUS_RE = re.compile(r"^(status:[ \t]*)([^\s#]+)([ \t]*(?:#[^\r\n]*)?\r?)$", re.M)


def read(path):
    with open(path, "r", encoding="utf-8") as fh:
        return fh.read()


def write(path, text):
    with open(path, "w", encoding="utf-8") as fh:
        fh.write(text)


# ── Frontmatter rule, shared verbatim by every parser in the kit ──────────────
# The YAML block opens with a `---` line, after an optional UTF-8 BOM, blank lines and
# `<!-- ... -->` blocks, and closes at the next line that is exactly `---`. Keep this
# function identical wherever it is copied (one fixture test runs all of them).
_FM_LEAD = re.compile(r"\ufeff?(?:[ \t]*\r?\n|[ \t]*<!--.*?-->[ \t]*\r?\n)*", re.S)
_FM_OPEN = re.compile(r"---[ \t]*\r?\n")
_FM_CLOSE = re.compile(r"^---[ \t]*(?:\r?\n|\Z)", re.M)


def frontmatter_bounds(text):
    """(lead_end, yaml_start, yaml_end, body_start) or None. text[:yaml_start] is the
    prefix plus the opening line, text[yaml_start:yaml_end] the YAML, text[yaml_end:]
    the closing line plus the body — so a rewriter keeps the prefix verbatim."""
    lead = _FM_LEAD.match(text).end()
    opening = _FM_OPEN.match(text, lead)
    if not opening:
        return None
    closing = _FM_CLOSE.search(text, opening.end())
    if not closing:
        return None
    return lead, opening.end(), closing.start(), closing.end()


def split_frontmatter(text):
    """(head, yaml, tail): head = anything before the block + the opening `---` line,
    tail = the closing `---` line + body. head + yaml + tail == text."""
    bounds = frontmatter_bounds(text)
    if not bounds:
        sys.exit("✗ frontmatter not found")
    return text[:bounds[1]], text[bounds[1]:bounds[2]], text[bounds[2]:]


def in_head(root, path):
    """True if the file is already tracked in HEAD. Outside git, does not block."""
    r = subprocess.run(["git", "-C", root, "cat-file", "-e", "HEAD:" + path],
                       capture_output=True)
    return r.returncode == 0


def wikilink(page, vault):
    pre = vault + "/"
    rel = page[len(pre):] if page.startswith(pre) else page
    return "[[" + re.sub(r"\.md$", "", rel) + "]]"


def add_related(fm, links):
    """Add links to `related:` (block or inline list), without duplicates."""
    new = [l for l in links if l not in fm]
    if not new:
        return fm
    block = re.search(r"^related:\s*\n((?:[ \t]+-[^\n]*\n)+)", fm, re.M)
    if block:
        indent = re.match(r"[ \t]+", block.group(1)).group(0)
        add = "".join(f'{indent}- "{l}"\n' for l in new)
        return fm[:block.end()] + add + fm[block.end():]
    flow = re.search(r"^related:[ \t]*\[(.*?)\][ \t]*$", fm, re.M)
    if flow:
        items = flow.group(1).strip()
        joined = (items + ", " if items else "") + ", ".join(f'"{l}"' for l in new)
        return fm[:flow.start()] + f"related: [{joined}]" + fm[flow.end():]
    return fm + "related:\n" + "".join(f'  - "{l}"\n' for l in new)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("work_id")
    ap.add_argument("--page", action="append", default=[])
    ap.add_argument("--date", default=datetime.date.today().isoformat())
    ap.add_argument("--root", default=".")
    ap.add_argument("--vault", default=None)
    ap.add_argument("--dry-run", action="store_true")
    a = ap.parse_args()

    vault = a.vault
    if not vault:
        found = [os.path.basename(d) for d in glob.glob(os.path.join(a.root, "*_wiki")) if os.path.isdir(d)]
        if len(found) != 1:
            sys.exit(f"✗ expected exactly one *_wiki/ under --root, found {found}; pass --vault")
        vault = found[0]

    pages = []
    for raw in a.page:
        parts = raw.split("|", 2)
        if len(parts) < 2 or parts[1] not in KINDS:
            sys.exit(f"✗ invalid --page: {raw!r} (expected path|CREATE|UPDATE|APPEND[|note])")
        path, kind = parts[0], parts[1]
        note = parts[2] if len(parts) == 3 else ""
        if not os.path.exists(os.path.join(a.root, path)):
            sys.exit(f"✗ page does not exist: {path} (write the page before closing)")
        if kind == "CREATE" and in_head(a.root, path):
            sys.exit(f"✗ {path} is already in HEAD — that is UPDATE, not CREATE (the execution list may be stale)")
        pages.append((path, kind, note))

    # work_id = FILE NAME of the execution/plan (may differ from the frontmatter work_id)
    ex = os.path.join(a.root, vault, "work/executions", a.work_id + ".md")
    plan = os.path.join(a.root, vault, "work/plans", a.work_id + ".md")
    log = os.path.join(a.root, vault, "_meta/log.md")
    for p in (ex, plan, log):
        if not os.path.exists(p):
            sys.exit(f"✗ not found: {p}")

    ex_text = read(ex)
    ex_head, fm, ex_tail = split_frontmatter(ex_text)
    m = STATUS_RE.search(fm)
    if not m or m.group(2) != "done":
        sys.exit("✗ execution is not `status: done` — confirm with the human first (premature sync)")
    new_fm = add_related(fm, [wikilink(p, vault) for p, _, _ in pages])

    plan_text = read(plan)
    plan_head, plan_fm, plan_tail = split_frontmatter(plan_text)
    new_plan_fm, n = STATUS_RE.subn(lambda m: m.group(1) + "executed" + m.group(3), plan_fm, count=1)
    if n != 1:
        sys.exit("✗ plan has no `status:` line in its frontmatter")
    new_plan = plan_head + new_plan_fm + plan_tail

    n_pages = len(pages)
    if not pages:
        print("note: no pages — closing only execution/plan/log")
    entry = f"\n## [{a.date}] wiki-sync | {a.work_id} | {n_pages} page{'s' if n_pages != 1 else ''} touched\n\n"
    entry += "".join(f"- `{p}` ({k})" + (f" — {note}" if note else "") + "\n" for p, k, note in pages)

    if a.dry_run:
        print("[dry-run] execution related[] +", [wikilink(p, vault) for p, _, _ in pages])
        print("[dry-run] plan -> status: executed")
        print("[dry-run] log (append):" + entry)
        return

    write(ex, ex_head + new_fm + ex_tail)
    write(plan, new_plan)
    with open(log, "a", encoding="utf-8") as fh:  # pure append: the log is never read
        fh.write(entry)

    print(f"ok  execution related[] (+{n_pages}) · plan=executed · log +{entry.count(chr(10))} lines")
    # Index-format guard (wiki-lint ships it next to this skill): the step-3 index
    # edit is hand-made, so check its format right after the sync.
    lint = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "wiki-lint", "lint.py")
    if os.path.exists(lint):
        sys.stdout.flush()
        sys.exit(subprocess.call([sys.executable, lint, "--root", a.root, "--vault", vault,
                                  "--only", "index-format"]))
    print("note: wiki-lint/lint.py not found — index format not checked", file=sys.stderr)


if __name__ == "__main__":
    main()
