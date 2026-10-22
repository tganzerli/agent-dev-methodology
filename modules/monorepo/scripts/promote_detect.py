#!/usr/bin/env python3
"""Detect what /promote-knowledge must carry from the current branch to main.

PRINCIPLE: the truth is the DIVERGENCE from main, never the commit graph.

The detection this replaces inferred "this work's files" from "files committed
together with the trio". That is a proxy, not the truth, and it failed both ways
in a controlled experiment in the installation that wrote this script:

  - BY OMISSION: knowledge committed apart from the trio was invisible. It once
    lost the CENTRAL ADR of a trio.
  - BY EXCESS: `git log -- <trio>` with no range limit walked the whole history and
    brought in a file from a commit ALREADY ON MAIN, which does not even diverge.

Comparing end states instead of paths makes omission impossible BY CONSTRUCTION:
a file is left out only if it does not diverge -- and then there is nothing to
promote. Attribution to the work_id stops FILTERING and starts ANNOTATING.

Output (blocks, one file per line) or --format=json:

  # DIVERGENT          knowledge files that differ from the base
  # ATTRIBUTED         the subset touched by commits that also touched the trio
  # ORPHAN             DIVERGENT - ATTRIBUTED  <- never drop silently
  # DIVERGENT_TRIOS    trios (task/plan/execution) that differ from the base

The mask is the skill's KL_PATHS (knowledge_source_of_truth_rule.md section 2),
passed with --mask or in the KL_PATHS environment variable: entries ending in "/"
match as prefixes, others exactly. The wiki's work/ dir is never in the mask --
trios get their own block, and the index/archive are regenerated, never copied.

Exit 0 whenever the measurement runs (2 on a usage or git error). A measurement
is not a verdict -- the human gate at step 3 of the skill decides.
"""

import argparse
import json
import os
import re
import subprocess
import sys

WIKI = "{{project}}_wiki"
TRIO_RE = re.compile(r"^" + re.escape(WIKI) + r"/work/(tasks|plans|executions)/.+\.md$")

# Gitignored or volatile: never promote. Mirrors the skill's step 2 filter.
NEVER = (
    ".claude/settings.local.json",
    ".claude/projects/",
    ".claude/todos/",
    ".claude/active_work.json",
    ".gemini/active_work.json",
    WIKI + "/.obsidian/workspace",
)


def git(*args):
    r = subprocess.run(["git", *args], capture_output=True, text=True)
    if r.returncode != 0:
        sys.stderr.write(f"ERROR: git {' '.join(args)}\n{r.stderr}")
        sys.exit(2)
    return r.stdout


def lines(s):
    return [x for x in s.splitlines() if x.strip()]


def nul(s):
    """Paths from -z output: exact bytes, no quoting of non-ASCII, spaces kept."""
    return [x for x in s.split("\0") if x]


def parse_mask(raw):
    """Newline-separated if there is a newline (paths may contain spaces), else whitespace."""
    if "\n" in raw.strip():
        return [x.strip() for x in raw.splitlines() if x.strip()]
    return raw.split()


def excluded(path):
    return any(path == n or path.startswith(n) for n in NEVER)


def in_mask(path, mask):
    return any(path.startswith(m) if m.endswith("/") else path == m for m in mask)


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("work_id", nargs="?", help="YYYY-MM-DD_slug; without it nothing is attributed")
    ap.add_argument("--mask", default=os.environ.get("KL_PATHS", ""),
                    help="knowledge-layer paths, space- or newline-separated (newlines for paths with spaces; default: $KL_PATHS)")
    ap.add_argument("--base", default="origin/main", help="target ref (default: origin/main)")
    ap.add_argument("--source", default="HEAD", help="source ref (default: HEAD)")
    ap.add_argument("--format", choices=["text", "json"], default="text")
    args = ap.parse_args()

    mask = parse_mask(args.mask)
    if not mask:
        sys.stderr.write("ERROR: empty mask. Pass --mask \"$KL_PATHS\" (the skill's step 2 list).\n")
        sys.exit(2)
    if any(m.startswith(WIKI + "/work") for m in mask):
        sys.stderr.write(f"ERROR: the mask must not contain {WIKI}/work/ -- trios have their own block.\n")
        sys.exit(2)

    for ref in (args.base, args.source):
        if subprocess.run(["git", "rev-parse", "--verify", "-q", ref], capture_output=True).returncode != 0:
            sys.stderr.write(f"ERROR: ref '{ref}' does not exist in this clone.\n"
                             f"  The skill runs `git fetch origin main` at step 1 -- check that it ran.\n")
            sys.exit(2)

    # THE TRUTH. Three dots, not two: compared against the merge-base, so the
    # result does not change when the base moves on through other people's work.
    changed = [p for p in nul(git("diff", "--name-only", "-z", "--no-renames", f"{args.base}...{args.source}"))
               if not excluded(p)]

    divergent = sorted(p for p in changed if in_mask(p, mask))
    trios = sorted(p for p in changed if TRIO_RE.match(p))

    # ATTRIBUTION -- annotates, does not filter.
    attributed = []
    if args.work_id:
        w = args.work_id
        trio_paths = [f"{WIKI}/work/{k}/{w}.md" for k in ("tasks", "plans", "executions")]
        # BOUNDED range: a commit already on the base is out. That was the excess failure.
        commits = lines(git("log", "--format=%H", f"{args.base}..{args.source}", "--", *trio_paths))
        touched = set()
        for c in commits:
            touched.update(nul(git("show", "--name-only", "-z", "--no-renames", "--format=", c)))
        # Intersect with DIVERGENT: a file that does not diverge is never copied,
        # which also removes the risk of checkout reverting something newer on the base.
        attributed = sorted(set(divergent) & touched)

    orphans = sorted(set(divergent) - set(attributed))

    if args.format == "json":
        print(json.dumps({
            "base": args.base, "source": args.source, "work_id": args.work_id,
            "divergent": divergent, "attributed": attributed,
            "orphan": orphans, "divergent_trios": trios,
        }, indent=2))
        return

    def block(title, items, note=""):
        print(f"# {title} ({len(items)}){note}")
        for i in items:
            print(i)
        if not items:
            print("  (none)")
        print()

    block("DIVERGENT", divergent)
    block("ATTRIBUTED", attributed, "" if args.work_id else "  <- no work_id: nothing to attribute")
    block("ORPHAN", orphans,
          "  <- diverge and are NOT attributable; decide at the gate, never drop silently" if orphans else "")
    block("DIVERGENT_TRIOS", trios,
          "  <- outside the mask; includes trios of OTHER work_ids" if trios else "")


if __name__ == "__main__":
    main()
