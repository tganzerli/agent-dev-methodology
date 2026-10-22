#!/usr/bin/env python3
"""Generate the gate list from the 🔒 markers in the normative documents (METHODOLOGY §6.5).

Why: hand-written "consolidated gates" lists are summaries of the body, and summaries
drift — one sweep found 29 imperative sub-rules living only in the body against 26
listed. Regime: a sub-rule carries 🔒 on its own line and appears here, or it is not
a gate. The output is a router (`file:line` back to the body), not a digest.

A marker inside a code span (`🔒`) is talk ABOUT gates, not a gate, and is skipped.
Read the output: a summary that does not stand on its own means the marker sits on
the wrong line.

Usage: python3 list_gates.py [--root .] [--markdown] [extra docs...]
"""
import argparse
import glob
import os
import re

DOCS = [".agents/METHODOLOGY.md", ".agents/rules/*.md"]
MARK = "\U0001F512"


def summary(line):
    t = re.sub(r"`[^`]*`", lambda m: m.group(0).strip("`"), line.strip().replace(MARK, " "))
    t = t.lstrip("># ")
    t = re.sub(r"^[-*+]\s+", "", t)
    t = re.sub(r"^\d+(?:\.\d+)*\.?\s*", "", t)
    if t.startswith("|"):  # table row: the rule lives in the longest (descriptive) cell
        cells = [c.strip() for c in t.strip("|").split("|") if c.strip()]
        t = max(cells, key=len) if cells else ""
    t = re.sub(r"\*\*(.+?)\*\*", r"\1", t)
    t = re.sub(r"\s+", " ", t).strip(" .:—-")
    return (t[:96].rstrip() + "…") if len(t) > 97 else (t or "(no summary)")


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--root", default=".")
    ap.add_argument("--markdown", action="store_true")
    ap.add_argument("docs", nargs="*", help="extra normative docs (globs, relative to --root)")
    a = ap.parse_args()

    files = []
    for pattern in DOCS + a.docs:
        files += sorted(glob.glob(os.path.join(a.root, pattern)))
    gates = []
    for path in files:
        rel = os.path.relpath(path, a.root)
        in_fence = False
        with open(path, encoding="utf-8") as fh:
            for i, line in enumerate(fh, 1):
                if line.lstrip().startswith("```"):
                    in_fence = not in_fence
                    continue
                if in_fence or MARK not in re.sub(r"`[^`]*`", "", line):
                    continue
                gates.append((rel, i, summary(line)))

    if a.markdown:
        print("| gate | where |\n|---|---|")
        for rel, i, s in gates:
            print(f"| {s} | `{rel}:{i}` |")
    else:
        for rel, i, s in gates:
            print(f"{rel}:{i}\t{s}")
    print(f"\n{len(gates)} gate(s) marked {MARK} in {len(files)} document(s).")


if __name__ == "__main__":
    main()
