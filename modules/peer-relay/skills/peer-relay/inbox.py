#!/usr/bin/env python3
"""Inbound relay messages from one peer, in the two states delivery by PR creates.

A peer delivers by Pull Request against the line relay lands in (default
`main`), so a new message first lives in an open PR and reaches that line only
when the owner merges it. Reading the working tree sees neither state reliably:
it misses the open PR, and it reads whatever branch the session is on.

This script reads both, from the remote:

  * merged   - <vault>/work/relay/*.md on <remote>/<line>, pending only
               (`status: sent | read`) unless `--all`;
  * open PR  - every open PR against <line> whose diff touches the relay
               directory, read from `pull/<n>/head`.

A message matches when its frontmatter says `direction: inbound` and
`peer: <peer>`. Branch names are not used to filter: peers name them
differently. A relay file in an open PR stamped `direction: outbound` and
`peer: <self>` is listed apart (`misstamped`): it is the peer's own outbound
copy addressed to us, delivered without the inbound stamp, invisible to the
match - and that has happened. Intra-team messages (no `peer:`) and our own
outbound copies to other peers are not misstamped and are not listed.

<self> is our name in the peers' registries (the prefix they use for us):
`--self NAME`, else `self:` in the frontmatter of .agents/peers.md, else the
vault name without `_wiki` (`<project>_wiki` -> `<project>`).

Open PRs are read with the GitHub CLI (`gh`). On another host, replace
`list_prs()` with that host's CLI (e.g. `glab mr list`), keeping its contract;
until then the script exits 2 and says the open PRs were not checked.

Exit codes - an empty answer is an answer only with 0:
  0  both states checked
  1  usage error (peer not declared in .agents/peers.md, no vault, not a git repo)
  2  partial: open PRs NOT checked (gh missing, unauthenticated or failing),
     or `git fetch` failed and <remote>/<line> may be stale

Usage:
  python3 .claude/skills/peer-relay/inbox.py <peer> [--root .] [--vault <dir>]
          [--self <our-name>] [--remote origin] [--line main] [--all] [--pr N]

`--pr N` reads PR N in any state instead of listing open ones (to test the
positive path against an already merged delivery).
"""

import argparse
import glob
import json
import os
import re
import subprocess
import sys

PENDING = {"sent", "read"}
RELAY_BRANCH = re.compile(r"^docs/.+__relay$")


def run(cmd, root):
    return subprocess.run(cmd, cwd=root, check=True, capture_output=True, text=True).stdout


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


def frontmatter(text):
    bounds = frontmatter_bounds(text)
    if not bounds:
        return {}
    fm = {}
    for line in text[bounds[1]:bounds[2]].splitlines():
        m = re.match(r"^([A-Za-z_]+):\s*(.*)$", line)
        if m:
            fm[m.group(1)] = re.sub(r"\s+#.*$", "", m.group(2)).strip().strip("\"'")
    return fm


def matches(fm, peer):
    return fm.get("direction") == "inbound" and fm.get("peer") == peer


def misstamped(fm, self_name):
    """The peer's outbound copy addressed to us, delivered without being re-stamped
    `direction: inbound` (peer-relay SKILL: "The delivered copy is stamped for the reader").
    Not an intra-team message (no `peer:`), not our own outbound copy to another peer."""
    return fm.get("direction") == "outbound" and fm.get("peer") == self_name


def resolve_self(cli_value, peers_text, vault):
    """Our name as the peers know us: --self, else `self:` in the registry's
    frontmatter, else the vault name without `_wiki`."""
    if cli_value:
        return cli_value
    bounds = frontmatter_bounds(peers_text)
    if bounds:
        m = re.search(r"^self:[ \t]*[\"'`]?([^\s\"'`#]+)", peers_text[bounds[1]:bounds[2]], re.M)
        if m:
            return m.group(1)
    return vault[:-len("_wiki")] if vault.endswith("_wiki") else vault


def merged_messages(root, ref, relay_dir, peer, show_all):
    listing = run(["git", "ls-tree", "--name-only", ref, relay_dir], root)
    found = []
    for path in sorted(listing.split()):
        if not path.endswith(".md") or os.path.basename(path).startswith("_"):
            continue
        fm = frontmatter(run(["git", "show", f"{ref}:{path}"], root))
        if matches(fm, peer) and (show_all or fm.get("status") in PENDING):
            found.append((path, fm))
    return found


def list_prs(root, line, only_pr):
    """Host adapter. Returns dicts with `number`, `headRefName`, `files[].path`."""
    fields = "number,headRefName,files"
    if only_pr is not None:
        return [json.loads(run(["gh", "pr", "view", str(only_pr), "--json", fields], root))]
    return json.loads(run(["gh", "pr", "list", "--base", line, "--state", "open",
                           "--limit", "200", "--json", fields], root))


def pr_messages(root, remote, relay_dir, peer, self_name, pr):
    paths = [f["path"] for f in pr.get("files") or []
             if f["path"].startswith(relay_dir) and f["path"].endswith(".md")
             and not os.path.basename(f["path"]).startswith("_")]
    if not paths:
        return [], []
    run(["git", "fetch", "-q", remote, f"pull/{pr['number']}/head"], root)
    found, odd = [], []
    for path in paths:
        try:
            fm = frontmatter(run(["git", "show", f"FETCH_HEAD:{path}"], root))
        except subprocess.CalledProcessError:
            continue  # deleted by the PR
        if matches(fm, peer):
            found.append((pr, path, fm))
        elif misstamped(fm, self_name):
            odd.append((pr, path, fm))
    return found, odd


def open_pr_messages(root, remote, line, relay_dir, peer, self_name, only_pr):
    """Returns (found, odd, None) or (None, None, reason) - never [] for 'not checked'."""
    try:
        found, odd = [], []
        for pr in list_prs(root, line, only_pr):
            f, o = pr_messages(root, remote, relay_dir, peer, self_name, pr)
            found.extend(f)
            odd.extend(o)
        return found, odd, None
    except FileNotFoundError:
        return None, None, "gh not found on PATH"
    except (subprocess.CalledProcessError, json.JSONDecodeError) as e:
        detail = (getattr(e, "stderr", "") or "").strip().splitlines()
        cmd = " ".join(getattr(e, "cmd", ["gh"])[:3])
        return None, None, f"{cmd} failed: {detail[-1] if detail else e}"


def summary_line(fm):
    s = fm.get("summary", "")
    return s if len(s) <= 110 else s[:107] + "..."


def main():
    ap = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    ap.add_argument("peer")
    ap.add_argument("--root", default=".")
    ap.add_argument("--vault", default=None, help="vault dir (default: the single *_wiki/ under --root)")
    ap.add_argument("--self", dest="self_name", default=None,
                    help="our name in the peers' registries (default: `self:` in .agents/peers.md, "
                         "else the vault name without _wiki)")
    ap.add_argument("--remote", default="origin")
    ap.add_argument("--line", default="main", help="the line relay deliveries land in")
    ap.add_argument("--all", action="store_true", help="merged: show every status")
    ap.add_argument("--pr", type=int, help="read this PR (any state) instead of listing open ones")
    args = ap.parse_args()
    root = args.root

    try:
        with open(os.path.join(root, ".agents/peers.md"), encoding="utf-8") as f:
            peers = f.read()
    except OSError as e:
        print(f"error: .agents/peers.md unreadable: {e}", file=sys.stderr)
        return 1
    # Any heading level; the registry may be written in another language.
    if not re.search(rf"^#+\s*`?{re.escape(args.peer)}`?\s*$", peers, re.M):
        print(f"error: peer `{args.peer}` not declared in .agents/peers.md", file=sys.stderr)
        return 1

    vault = args.vault
    if vault is None:
        vaults = [os.path.basename(p) for p in glob.glob(os.path.join(root, "*_wiki")) if os.path.isdir(p)]
        if len(vaults) != 1:
            print("error: no single *_wiki vault under --root; pass --vault", file=sys.stderr)
            return 1
        vault = vaults[0]
    relay_dir = f"{vault}/work/relay/"
    self_name = resolve_self(args.self_name, peers, vault)
    ref = f"{args.remote}/{args.line}"

    code = 0
    try:
        run(["git", "fetch", "-q", args.remote], root)
    except FileNotFoundError:
        print("error: git not found", file=sys.stderr)
        return 1
    except subprocess.CalledProcessError:
        print(f"⚠ git fetch failed: local {ref} may be stale")
        code = 2

    try:
        head = run(["git", "rev-parse", "--short", ref], root).strip()
        merged = merged_messages(root, ref, relay_dir, args.peer, args.all)
    except subprocess.CalledProcessError as e:
        print(f"error: cannot read {ref}: {(e.stderr or '').strip()}", file=sys.stderr)
        return 1

    in_prs, odd, reason = open_pr_messages(root, args.remote, args.line, relay_dir, args.peer,
                                           self_name, args.pr)
    checked = "checked" if reason is None else "NOT checked"
    print(f"peer {args.peer} · {ref} @ {head} · PRs: {checked}")

    if reason is not None:
        print(f"⚠ open PRs NOT checked: {reason}")
        print("  A delivered message that is not merged yet does not appear below. Do not conclude absence.")
        code = 2
    else:
        label = f"PR #{args.pr}" if args.pr is not None else "in open PRs"
        print(f"{label} ({len(in_prs)}):")
        for pr, path, fm in in_prs:
            note = "" if RELAY_BRANCH.match(pr.get("headRefName", "")) else "  [branch outside docs/*__relay]"
            print(f"  #{pr['number']}  {pr.get('headRefName', '?')}  {os.path.basename(path)}"
                  f"  status={fm.get('status', '?')}{note}")
            print(f"        {summary_line(fm)}")
        if odd:
            print(f"⚠ relay files in PRs stamped outbound/{self_name} ({len(odd)}) - "
                  "a delivery with the sender's outbound frontmatter. Read before dismissing:")
            for pr, path, fm in odd:
                print(f"  #{pr['number']}  {os.path.basename(path)}"
                      f"  direction={fm.get('direction', '?')} peer={fm.get('peer', '?')}")

    label = "merged" if args.all else "merged, pending (status sent|read)"
    print(f"{label} ({len(merged)}):")
    for path, fm in merged:
        print(f"  {os.path.basename(path)}  status={fm.get('status', '?')}")
        print(f"        {summary_line(fm)}")
    return code


if __name__ == "__main__":
    sys.exit(main())
