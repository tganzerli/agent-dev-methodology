#!/usr/bin/env python3
"""Check benchmark pages for the two declarations benchmark_protocol_rule.md requires.

  host-state        every page carries a `host_state:` block with the measured keys (rule §4.1)
  drift-declaration a page with `design: sequential-ab` declares the four keys of
                    `drift_declaration:` (rule §5.6.1)

Both read the AUTHOR'S frontmatter, not prose: detecting "sequential design" from
text errs both ways, and a check that errs teaches people to ignore it.
Pages whose name starts with `_` (template, index) are skipped.

Usage:
  python3 check_pages.py [--root .] [--vault <dir>] [--skip host-state] [page.md ...]

Exit: 0 clean, 1 findings, 2 usage error. Standard library only.
"""
import argparse
import glob
import os
import re
import sys

DRIFT_KEYS = {"order", "per_session", "internal_drift_pct", "adjacent_compared"}
HOST_KEYS = {"measured_at", "swap_pct", "mem_free_pct", "load1", "uptime_days"}


def frontmatter_lines(text):
    if not text.startswith("---"):
        return []
    end = text.find("\n---", 3)
    return text[3:end].splitlines() if end != -1 else []


def top_value(lines, key):
    for line in lines:
        m = re.match(r"^%s:\s*(.*?)\s*(#.*)?$" % re.escape(key), line)
        if m:
            return m.group(1).strip("\"'")
    return None


def block_keys(lines, parent):
    """Child keys of an indented frontmatter block; None if the block is absent."""
    out, inside = None, False
    for line in lines:
        if re.match(r"^%s:\s*(#.*)?$" % re.escape(parent), line):
            inside, out = True, set()
            continue
        if inside:
            m = re.match(r"^\s+(\w[\w.-]*):", line)
            if m:
                out.add(m.group(1))
            elif line.strip() and not line.startswith((" ", "\t", "#")):
                break
    return out


def check(path, skip):
    with open(path, encoding="utf-8") as f:
        fm = frontmatter_lines(f.read())
    found = []
    if "host-state" not in skip:
        keys = block_keys(fm, "host_state")
        if keys is None:
            found.append(("host-state", "no `host_state` block (rule §4.1)"))
        elif HOST_KEYS - keys:
            found.append(("host-state", "`host_state` without the measured keys (rule §4.1): "
                          + ", ".join(sorted(HOST_KEYS - keys))))
    if "drift-declaration" not in skip and top_value(fm, "design") == "sequential-ab":
        miss = sorted(DRIFT_KEYS - (block_keys(fm, "drift_declaration") or set()))
        if miss:
            found.append(("drift-declaration",
                          "sequential A/B without the four drift items (rule §5.6.1): " + ", ".join(miss)))
    return found


def main():
    ap = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    ap.add_argument("pages", nargs="*")
    ap.add_argument("--root", default=".")
    ap.add_argument("--vault", default=None)
    ap.add_argument("--skip", action="append", default=[], choices=["host-state", "drift-declaration"])
    args = ap.parse_args()

    pages = args.pages
    if not pages:
        vault = args.vault
        if vault is None:
            vaults = [p for p in glob.glob(os.path.join(args.root, "*_wiki")) if os.path.isdir(p)]
            if len(vaults) != 1:
                print("error: no single *_wiki vault under --root; pass --vault", file=sys.stderr)
                return 2
            vault = vaults[0]
        else:
            vault = os.path.join(args.root, vault)
        pages = sorted(glob.glob(os.path.join(vault, "benchmarks", "*.md")))
    missing = [p for p in pages if not os.path.isfile(p)]
    if missing:
        print("error: no such page: " + ", ".join(missing), file=sys.stderr)
        return 2
    pages = [p for p in pages if not os.path.basename(p).startswith("_")]

    n = 0
    for page in pages:
        for check_id, msg in check(page, set(args.skip)):
            print(f"{check_id}: {page}: {msg}")
            n += 1
    print(f"{len(pages)} page(s) checked, {n} finding(s)")
    return 1 if n else 0


if __name__ == "__main__":
    sys.exit(main())
