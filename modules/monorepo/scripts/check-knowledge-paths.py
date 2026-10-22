#!/usr/bin/env python3
"""Verify the four copies of the knowledge-layer path list.

Authoritative source: the fenced block of section 2 of
.agents/rules/knowledge_source_of_truth_rule.md. Operational copies:
  - .claude/skills/promote-knowledge/SKILL.md  (KL_PATHS)         -- equal to section 2
  - .claude/skills/sync-knowledge/SKILL.md     (KL_PATHS)         -- equal to section 2
  - scripts/broadcast-main.sh                  (KNOWLEDGE_PATHS)  -- equal to Group A of
    section 3.6, tolerating extras under the wiki (the work/ dir section 2 does not cover)

Four checks:
  1. both skill masks equal section 2;
  2. section 2 is partitioned by Groups A and B of section 3.6 -- no leftover, no overlap;
  3. no Group B path leaks into KNOWLEDGE_PATHS (a planned abort turning into blind
     adoption of main's version is the dangerous failure), and every Group A path is there;
  4. every section 2 path matches >= 1 tracked file, unless marked
     "DECLARED, not yet created".

Run from an installed repo (scripts/ next to .agents/), or from the kit, where it
detects the module layout and runs in template mode: <placeholders> are allowed and
check 4 is skipped. Installed, a leftover <placeholder> is an error.

Exit 0 with "ok", or 1 with the report. Standard library only.
"""
import re
import subprocess
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
ROOT = HERE.parent

if (ROOT / "rules/knowledge_source_of_truth_rule.md").exists():
    TEMPLATE = True
    RULE = ROOT / "rules/knowledge_source_of_truth_rule.md"
    PROMOTE = ROOT / "skills/promote-knowledge/SKILL.md"
    SYNC = ROOT / "skills/sync-knowledge/SKILL.md"
else:
    TEMPLATE = False
    RULE = ROOT / ".agents/rules/knowledge_source_of_truth_rule.md"
    PROMOTE = ROOT / ".claude/skills/promote-knowledge/SKILL.md"
    SYNC = ROOT / ".claude/skills/sync-knowledge/SKILL.md"
BROADCAST = HERE / "broadcast-main.sh"

DECLARED_MARK = "DECLARED, not yet created"
PLACEHOLDER = re.compile(r"^<[^<>\s]+>$")


def _entries(line):
    """Paths on one block line; a line may group several with commas."""
    line = line.strip()
    if not line or line.startswith("#"):
        return [], ""
    path_part, _, comment = line.partition("#")
    return [p.strip() for p in path_part.split(",") if p.strip()], comment


def source_paths():
    """(all, declared_without_file) from the first fenced block of section 2."""
    text = RULE.read_text(encoding="utf-8")
    section = text.split("## 2. Knowledge layer", 1)[1]
    block = section.split("```", 2)[1]
    paths, declared = [], set()
    for line in block.splitlines():
        entries, comment = _entries(line)
        paths += entries
        if DECLARED_MARK in comment:
            declared.update(entries)
    return paths, declared


def groups():
    """(A, B) -- the two fenced blocks of section 3.6."""
    text = RULE.read_text(encoding="utf-8")
    section = text.split("### 3.6", 1)[1].split("\n## 4.", 1)[0]
    parts = section.split("```")
    fenced = [parts[i] for i in range(1, len(parts), 2)]
    fenced = [f for f in fenced if "merge=union" not in f]
    if len(fenced) != 2:
        raise SystemExit(f"section 3.6: expected 2 fenced blocks (Group A and B), found {len(fenced)}")
    out = []
    for block in fenced:
        paths = []
        for line in block.splitlines():
            paths += _entries(line)[0]
        out.append(set(paths))
    return out[0], out[1]


def mask_paths(path, anchor="KL_PATHS="):
    """Tokens of a multi-line bash string started at `anchor`."""
    text = path.read_text(encoding="utf-8")
    chunk = text[text.index(anchor):]
    acc = []
    for line in chunk.splitlines():
        acc.append(line)
        if not line.rstrip().endswith("\\"):
            break
    raw = " ".join(acc).replace(anchor, " ").replace("\\", " ").replace('"', " ")
    return [tok for tok in raw.split() if not tok.startswith("#")]


def broadcast_paths():
    """Entries of the KNOWLEDGE_PATHS array, comments stripped line by line."""
    text = BROADCAST.read_text(encoding="utf-8")
    chunk = text.split("KNOWLEDGE_PATHS=(", 1)[1]
    found = []
    for line in chunk.splitlines():
        if line.strip().startswith(")"):
            break
        found += re.findall(r'"([^"]+)"', line.split("#", 1)[0])
    return found


def covers(group, path):
    return any(path == g or path.startswith(g) for g in group)


def tracked(path):
    out = subprocess.run(
        ["git", "-C", str(ROOT), "ls-files", "--", path],
        capture_output=True, text=True, check=True,
    ).stdout
    return any(ln.strip() for ln in out.splitlines())


def main():
    errors = []
    src, declared = source_paths()
    src_set = set(src)
    wiki = sorted({p.split("/", 1)[0] + "/" for p in src if p.split("/", 1)[0].endswith("_wiki")})

    for label, got in (
        ("promote-knowledge KL_PATHS", mask_paths(PROMOTE)),
        ("sync-knowledge KL_PATHS", mask_paths(SYNC)),
    ):
        got_set = set(got)
        missing, extra = sorted(src_set - got_set), sorted(got_set - src_set)
        if missing:
            errors.append(f"{label}: missing {', '.join(missing)}")
        if extra:
            errors.append(f"{label}: extra {', '.join(extra)} (not in section 2)")

    group_a, group_b = groups()

    unclassified = sorted(p for p in src_set if not covers(group_a, p) and not covers(group_b, p))
    if unclassified:
        errors.append("section 3.6: outside both groups: " + ", ".join(unclassified)
                      + " -- every section 2 path reconciles (A) or aborts (B), no third option")
    both = sorted(p for p in src_set if covers(group_a, p) and covers(group_b, p))
    if both:
        errors.append("section 3.6: in Group A and B at once: " + ", ".join(both))
    ghost = sorted(g for g in group_a | group_b if not any(p == g or p.startswith(g) for p in src_set))
    if ghost:
        errors.append("section 3.6: classifies a path section 2 does not list: " + ", ".join(ghost))

    bc_set = set(broadcast_paths())
    leaked = sorted(bc_set & group_b)
    if leaked:
        errors.append("broadcast-main.sh KNOWLEDGE_PATHS: contains Group B (" + ", ".join(leaked)
                      + ") -- that turns a planned abort into blind adoption of main's version")
    missing_a = sorted(group_a - bc_set)
    if missing_a:
        errors.append("broadcast-main.sh KNOWLEDGE_PATHS: missing Group A " + ", ".join(missing_a))
    stray = sorted(p for p in bc_set - group_a if not any(p.startswith(w) for w in wiki))
    if stray:
        errors.append("broadcast-main.sh KNOWLEDGE_PATHS: extra outside Group A and outside the wiki: "
                      + ", ".join(stray))

    placeholders = sorted(p for p in src_set if PLACEHOLDER.match(p))
    if not TEMPLATE:
        if placeholders:
            errors.append("section 2: install placeholder never adapted: " + ", ".join(placeholders))
        for p in src:
            if p in declared or PLACEHOLDER.match(p):
                continue
            if not tracked(p):
                errors.append(f'section 2: `{p}` matches no tracked file and is not marked "{DECLARED_MARK}"')

    if errors:
        print("check-knowledge-paths: FAILED\n")
        for e in errors:
            print(f"  x {e}")
        print(f"\n{len(errors)} problem(s). Source: {RULE.relative_to(ROOT)} section 2; checklist in 9.1.")
        return 1

    mode = f"template mode, {len(placeholders)} placeholder(s), tracked-file check skipped" if TEMPLATE \
        else f"{len(declared)} declared-not-created"
    print(f"ok -- section 2 has {len(src)} paths ({mode}), "
          f"partitioned A={len(group_a)}/B={len(group_b)}, 3 copies agree")
    return 0


if __name__ == "__main__":
    sys.exit(main())
