#!/usr/bin/env python3
"""Mechanical part of /wiki-sync (steps 4-5), without spending LLM context.

Why it exists: the old step "append to `_meta/log.md`" made the agent `Read` + `Edit`
the whole log (it is append-only and only grows — hundreds of KB). Here the entry is
appended straight to the end of the file; its content is never read.

Does, in order:
  1. adds wikilinks of the touched pages to the execution's `related[]`;
  2. appends the entry to `<vault>/_meta/log.md` (pure append);
  3. marks the plan `status: executed` (anchored on `^status:`, never on a
     `# status:` comment);
  4. runs the vault's index-format guard if the project ships one (optional).

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


def read(path):
    with open(path, "r", encoding="utf-8") as fh:
        return fh.read()


def write(path, text):
    with open(path, "w", encoding="utf-8") as fh:
        fh.write(text)


def split_frontmatter(text):
    m = re.match(r"^---\n(.*?\n)---\n", text, re.S)
    if not m:
        sys.exit("✗ frontmatter not found")
    return m.group(1), text[m.end():]


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
    """Acrescenta links a `related:` (lista em bloco ou em linha), sem duplicar."""
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
            sys.exit(f"✗ --page inválido: {raw!r} (expected path|CREATE|UPDATE|APPEND[|note])")
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
    fm, body = split_frontmatter(ex_text)
    if not re.search(r"^status:\s*done\s*$", fm, re.M):
        sys.exit("✗ execution is not `status: done` — confirm with the human first (premature sync)")
    new_fm = add_related(fm, [wikilink(p, vault) for p, _, _ in pages])

    plan_text = read(plan)
    new_plan, n = re.subn(r"^status:\s*\S+\s*$", "status: executed", plan_text, count=1, flags=re.M)
    if n != 1:
        sys.exit("✗ plan has no `status:` line in its frontmatter")

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

    write(ex, "---\n" + new_fm + "---\n" + body)
    write(plan, new_plan)
    with open(log, "a", encoding="utf-8") as fh:  # pure append: the log is never read
        fh.write(entry)

    print(f"ok  execution related[] (+{n_pages}) · plan=executed · log +{entry.count(chr(10))} lines")
    # Optional guard: runs only if the project ships one (the Condor monorepo does).
    for cand in (".claude/skills/wiki-lint/check_index_format.py", ".agents/skills/wiki-lint/check_index_format.py"):
        chk = os.path.join(a.root, cand)
        if os.path.exists(chk):
            sys.exit(subprocess.call([sys.executable, chk, "--root", a.root]))


if __name__ == "__main__":
    main()
