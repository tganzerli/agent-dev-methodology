#!/usr/bin/env python3
"""Report repeated entry headers in {{project}}_wiki/_meta/log.md.

Context: the premise this replaces was refuted. "merge=union is not idempotent"
(knowledge_source_of_truth_rule.md section 3.6) was measured in a synthetic repo:

  - IDENTICAL append on both sides         -> git sees one change, no duplicate
  - dev append + other appends on main     -> the 3-way merge resolves, no duplicate

The real defect is smaller: a header such as

    ## [YYYY-MM-DD] wiki-sync | <work_id> | N pages touched

does not disambiguate. Two syncs of the same work_id on the same day touching the
same number of pages produce identical headers, and then neither a reader nor a
script can tell "two real entries" from "one duplicated entry".

This script reports those collisions, for two purposes:
  1. flag an ambiguous header, which needs a distinguishing suffix;
  2. if merge duplication ever DOES happen, it shows up here -- the refuted
     hypothesis is covered by a detector instead of an assumption.

REPORTS, DOES NOT FAIL (exit 0 unless the file cannot be read). A header
collision is not a reason to block a PR; it is information for whoever writes the
next entry.
"""

import collections
import os
import re
import sys

LOG = "{{project}}_wiki/_meta/log.md"
HEADER = re.compile(r"^##\s+\[.*$", re.M)


def main():
    root = sys.argv[1] if len(sys.argv) > 1 else "."
    path = os.path.join(root, LOG)
    if not os.path.exists(path):
        print(f"[log] {LOG} does not exist -- nothing to check.")
        return 0

    with open(path, encoding="utf-8") as f:
        text = f.read()

    heads = HEADER.findall(text)
    if not heads:
        print("[log] no entries found.")
        return 0

    counts = collections.Counter(h.strip() for h in heads)
    collisions = {h: n for h, n in counts.items() if n > 1}

    if not collisions:
        print(f"[log] OK -- {len(heads)} entries, no repeated header.")
        return 0

    print(f"[log] {len(collisions)} repeated header(s) in {len(heads)} entries:")
    for h, n in sorted(collisions.items()):
        print(f"  !  {n}x  {h}")
    print("[log] A repeated header is NOT duplication by itself: it may be two real syncs")
    print("     of the same work_id on the same day. Compare the BODIES -- if they differ,")
    print("     add a distinguishing suffix to the header.")
    print("[log] Report, not failure.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
