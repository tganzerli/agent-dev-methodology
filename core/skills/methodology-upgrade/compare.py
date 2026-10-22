#!/usr/bin/env python3
"""Compare the installed methodology with a kit checkout, in both directions.

For each kit file that maps to an installed path it reads three versions — the kit at
the commit stamped in .agents/KIT_VERSION, the kit at HEAD, and the installed file —
de-templates the kit side (the project, PROJECT, KNOWLEDGE_LANG, COMMIT_LANG and repo placeholders) and
classifies:

  kit-change     kit moved since the stamp, project did not   -> apply (under a plan)
  local          project moved, kit did not                   -> candidate to upstream
  both           both moved                                   -> merge by hand
  new-in-kit     file added to the kit since the stamp        -> consider installing
  missing        core file not installed                      -> moved, or deliberately dropped
  optional-not-installed   module, agent, hook, CI, MCP or REVIEW.md file absent
                           (hidden unless --all) -> skipped by choice at install
  same           nothing to do

Read-only: it never writes to the project or the kit. De-templating is heuristic (an
installed file may have been adapted on purpose), so a `local` is a question, not a
verdict.

Usage:
  python3 compare.py --kit <path-to-kit-checkout> [--root .] [--vault NAME] [--all]
  python3 compare.py --kit <kit> --diff <installed-path> [--against stamp|head]
"""
import argparse
import difflib
import glob
import os
import re
import subprocess
import sys

# kit path (regex) -> installed path. {vault} is filled in at run time.
MAP = [
    (r"core/METHODOLOGY\.md", ".agents/METHODOLOGY.md"),
    (r"core/mcp\.md", ".agents/mcp.md"),
    (r"core/rules/(.+)", r".agents/rules/\1"),
    (r"modules/[^/]+/rules/(.+)", r".agents/rules/\1"),
    (r"core/vault/_meta/conventions\.md", "{vault}/_meta/conventions.md"),
    (r"core/templates/(task|plan|execution)\.md", r"{vault}/work/\1s/_template.md"),
    (r"core/templates/adr\.md", "{vault}/decisions/_templates/adr.md"),
    (r"core/templates/postmortem\.md", "{vault}/postmortems/_template.md"),
    (r"core/templates/wiki-page\.md", "{vault}/_meta/_page_template.md"),
    (r"core/templates/source\.md", "{vault}/sources/external/_template.md"),
    (r"core/templates/review\.md", "REVIEW.md"),
    (r"core/templates/pull_request_template\.md", ".github/pull_request_template.md"),
    (r"core/skills/(.+)", r".claude/skills/\1"),
    (r"modules/[^/]+/skills/(.+)", r".claude/skills/\1"),
    (r"core/agents/(.+)", r".claude/agents/\1"),
    (r"core/hooks/require-approved-plan\.sh", ".claude/hooks/require-approved-plan.sh"),
    (r"core/hooks/claude-settings\.json", ".claude/settings.json"),
    (r"core/hooks/agy-hooks\.json", ".agents/hooks.json"),
    (r"core/hooks/commit-msg", ".githooks/commit-msg"),
    (r"core/ci/check_commit_trailers\.py", "scripts/ci/check_commit_trailers.py"),
    (r"core/ci/methodology-checks\.yml", ".github/workflows/methodology-checks.yml"),
    (r"adapters/(claude|gemini|codex)\.md", r".agents/llm/\1.md"),
    (r"(?:core|modules/[^/]+)/gemini-commands/(.+)", r".gemini/commands/\1"),
]


# Installed only by choice (a module, an agent, an optional mechanism): absent is not "missing".
OPTIONAL = re.compile(r"modules/|.*/gemini-commands/|core/hooks/|core/ci/|core/mcp\.md$"
                      r"|core/agents/|core/templates/(review|pull_request_template)\.md$|adapters/")


def git(kit, *argv):
    r = subprocess.run(["git", "-C", kit, *argv], capture_output=True, text=True)
    return r.stdout if r.returncode == 0 else None


def read_stamp(root):
    path = os.path.join(root, ".agents", "KIT_VERSION")
    out = {}
    if os.path.exists(path):
        for line in open(path, encoding="utf-8"):
            m = re.match(r"^(\w+):\s*(.*?)\s*$", line)
            if m:
                out[m.group(1)] = m.group(2)
    return out


def kit_files(kit, rev):
    listing = git(kit, "ls-tree", "-r", "--name-only", rev)
    return set(listing.split("\n")) - {""} if listing else set()


def installed_path(kit_path, vault):
    for pattern, dst in MAP:
        m = re.fullmatch(pattern, kit_path)
        if m:
            return m.expand(dst).replace("{vault}", vault)
    return None


def detemplate(text, values):
    for k, v in values.items():
        if v:
            text = text.replace("{" * 2 + k + "}" * 2, v)  # spelled so install greps for leftovers stay clean
    return text


def norm(text):
    return [l.rstrip() for l in (text or "").strip("\n").splitlines()]


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--kit", required=True)
    ap.add_argument("--root", default=".")
    ap.add_argument("--vault", default=None)
    ap.add_argument("--all", action="store_true", help="also list `same` files")
    ap.add_argument("--diff", default=None, help="installed path to diff")
    ap.add_argument("--against", choices=["stamp", "head"], default="head")
    a = ap.parse_args()

    if git(a.kit, "rev-parse", "HEAD") is None:
        sys.exit(f"{a.kit} is not a git checkout of the kit")
    vaults = [os.path.basename(d) for d in glob.glob(os.path.join(a.root, "*_wiki")) if os.path.isdir(d)]
    vault = a.vault or (vaults[0] if len(vaults) == 1 else None)
    if not vault:
        sys.exit(f"cannot pick the vault ({vaults}); pass --vault")
    stamp = read_stamp(a.root)
    rev = stamp.get("kit_commit")
    if rev and git(a.kit, "cat-file", "-e", rev + "^{commit}") is None:
        sys.exit(f"stamped kit_commit {rev} not found in {a.kit} (fetch it)")
    if not rev:
        print("⚠  no .agents/KIT_VERSION kit_commit — comparing with kit HEAD only; "
              "`local` and `kit-change` cannot be told apart", file=sys.stderr)
    values = {"project": vault[:-len("_wiki")], "PROJECT": stamp.get("project", ""),
              "KNOWLEDGE_LANG": stamp.get("knowledge_lang", ""),
              "COMMIT_LANG": stamp.get("commit_lang", "English"),
              "repo": os.path.basename(os.path.abspath(a.root))}

    head_files = kit_files(a.kit, "HEAD")
    stamp_files = kit_files(a.kit, rev) if rev else set()
    best = {}
    for kp in sorted(head_files | stamp_files):
        ip = installed_path(kp, vault)
        if not ip:
            continue
        head = git(a.kit, "show", f"HEAD:{kp}") if kp in head_files else None
        old = git(a.kit, "show", f"{rev}:{kp}") if rev and kp in stamp_files else None
        ipath = os.path.join(a.root, ip)
        mine = open(ipath, encoding="utf-8", errors="replace").read() if os.path.isfile(ipath) else None
        h, o, m = (norm(detemplate(x, values)) if x is not None else None for x in (head, old, mine))
        if m is None:
            if head is None:
                continue
            if rev and old is None:
                status = "new-in-kit"
            else:
                status = "optional-not-installed" if OPTIONAL.match(kp) else "missing"
        elif h is not None and m == h:
            status = "same"
        elif h is None:
            status = "removed-in-kit"
        elif not rev:
            status = "differs"
        elif o is None:
            status = "new-in-kit"
        else:
            kit_moved, mine_moved = h != o, m != o
            status = ("both" if kit_moved and mine_moved else "kit-change" if kit_moved
                      else "local" if mine_moved else "same")
        # Several kit files can install to one path (a module overriding a core rule):
        # keep the one the installed file is closest to.
        ref = o or h or []
        score = difflib.SequenceMatcher(None, m, ref).ratio() if m is not None else -1
        if ip not in best or score > best[ip][0]:
            best[ip] = (score, status, kp, h, o, m)

    rows = [(st, kp, ip) for ip, (_, st, kp, *_rest) in best.items()]
    if a.diff:
        if a.diff not in best:
            sys.exit(f"{a.diff} is not a mapped installed path")
        _, _, kp, h, o, m = best[a.diff]
        base = o if a.against == "stamp" else h
        sys.stdout.writelines(l + "\n" for l in difflib.unified_diff(
            base or [], m or [], f"kit:{kp}@{a.against}", a.diff, lineterm=""))
        return 0
    order = ["kit-change", "both", "local", "differs", "new-in-kit", "removed-in-kit", "missing", "optional-not-installed", "same"]
    print(f"kit HEAD {git(a.kit, 'rev-parse', '--short', 'HEAD').strip()} · stamp {rev or '—'} · vault {vault}")
    for st in order:
        group = [r for r in rows if r[0] == st]
        if not group or (st in ("same", "optional-not-installed") and not a.all):
            continue
        print(f"\n## {st} ({len(group)})")
        for _, kp, ip in group:
            print(f"  {ip}  <-  {kp}")
    print("\n" + " · ".join(f"{st}={sum(1 for r in rows if r[0] == st)}" for st in order))
    return 0


if __name__ == "__main__":
    sys.exit(main())
