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

Open PRs are read through a host adapter, chosen by `--host` (default `auto`:
`bitbucket` when the remote URL is on bitbucket.org, else `github`):

  * github    - the GitHub CLI (`gh`), authenticated the usual way;
  * bitbucket - the Bitbucket Cloud REST API 2.0, with a token taken from
               PEER_RELAY_TOKEN (tests) or from the command in `host_token_cmd:`
               in the frontmatter of .agents/peers.md (run without a shell; its
               stdout is the token, which never reaches argv or the output).

Another host: add a lister with the same contract as `list_prs()` (dicts with
`number`, `headRefName`, `files[].path` and `fetchRef`); until then the script
exits 2 and says the open PRs were not checked.

Exit codes - an empty answer is an answer only with 0:
  0  both states checked
  1  usage error (peer not declared in .agents/peers.md, no vault, not a git repo)
  2  partial: open PRs NOT checked (gh missing, unauthenticated or failing;
     Bitbucket token missing or rejected; incomplete pagination; a PR from a
     fork), or `git fetch` failed and <remote>/<line> may be stale

Usage:
  python3 .claude/skills/peer-relay/inbox.py <peer> [--root .] [--vault <dir>]
          [--self <our-name>] [--remote origin] [--line main] [--all] [--pr N]
          [--host auto|github|bitbucket]

`--pr N` reads PR N in any state instead of listing open ones (to test the
positive path against an already merged delivery).
"""

import argparse
import glob
import json
import os
import re
import shlex
import ssl
import subprocess
import sys
import time
import urllib.error
import urllib.parse
import urllib.request

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
            fm[m.group(1)] = yaml_scalar(m.group(2).strip())
    return fm


def yaml_scalar(val):
    """YAML scalar semantics (same as work-index's parser): in a quoted value a `#` is
    text ('' is a quote, backslash escapes in "..."); in an unquoted one ` #` starts a
    comment."""
    if val[:1] in ("'", '"'):
        q, out, i = val[0], [], 1
        while i < len(val):
            c = val[i]
            if q == "'" and c == "'" and val[i + 1:i + 2] == "'":
                out.append("'")
                i += 2
            elif q == '"' and c == "\\" and val[i + 1:i + 2] in ('"', "\\"):
                out.append(val[i + 1])
                i += 2
            elif c == q:
                return "".join(out)
            else:
                out.append(c)
                i += 1
    return re.sub(r"\s+#.*$", "", val).strip().strip("\"'")


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


# ── Host adapters ─────────────────────────────────────────────────────────────
# Every lister returns dicts with `number`, `headRefName`, `files[].path` and
# `fetchRef` (the ref `git fetch <remote> <fetchRef>` reads the PR head from).

class HostError(Exception):
    """The open PRs could not be read honestly. Becomes exit 2, never 'empty'."""


def detect_host(root, remote, forced):
    if forced != "auto":
        return forced
    url = run(["git", "remote", "get-url", remote], root).strip()
    return "bitbucket" if "bitbucket.org" in url else "github"


def list_prs_github(root, line, only_pr):
    fields = "number,headRefName,files"
    if only_pr is not None:
        prs = [json.loads(run(["gh", "pr", "view", str(only_pr), "--json", fields], root))]
    else:
        prs = json.loads(run(["gh", "pr", "list", "--base", line, "--state", "open",
                              "--limit", "200", "--json", fields], root))
    for pr in prs:
        pr["fetchRef"] = f"pull/{pr['number']}/head"
    return prs


# Bitbucket Cloud REST API 2.0. Four traps, each measured against the real API in the
# project this adapter came from:
#   1. auth is `Authorization: Bearer <token>` (Basic x-token-auth answers 401 on the API);
#   2. some Python builds ship without a CA bundle (cafile None): look for one;
#   3. `pagelen` defaults to 10: ask for more, follow `next`, and check `size`;
#   4. a private repository answers 404, not 401, to a bad token: say both.
BB_API = os.environ.get("PEER_RELAY_BITBUCKET_API", "https://api.bitbucket.org/2.0")
_BB_URL = re.compile(r"bitbucket\.org[:/](?P<ws>[^/:]+)/(?P<slug>[^/]+?)(?:\.git)?/?$")
_CA_CANDIDATES = ("/etc/ssl/cert.pem", "/opt/homebrew/etc/ca-certificates/cert.pem",
                  "/usr/local/etc/openssl@3/cert.pem")
_TLS = None


def bitbucket_repo(url):
    """`git@[ssh.]bitbucket.org:ws/slug(.git)` or `https://[user@]bitbucket.org/ws/slug(.git)`."""
    m = _BB_URL.search((url or "").strip())
    if not m:
        raise HostError(f"cannot read workspace/slug from remote {url!r}")
    return m.group("ws"), m.group("slug")


def tls_context():
    global _TLS
    if _TLS is None:
        if ssl.get_default_verify_paths().cafile:
            _TLS = ssl.create_default_context()
        else:
            try:
                import certifi
                _TLS = ssl.create_default_context(cafile=certifi.where())
            except ImportError:
                found = next((c for c in _CA_CANDIDATES if os.path.exists(c)), None)
                if not found:
                    raise HostError("no CA bundle for TLS (install certifi or your Python's certificates)")
                _TLS = ssl.create_default_context(cafile=found)
    return _TLS


def http_get_json(url, token, tries=3):
    """GET with backoff on 429 and on transient network errors. Returns (status, json)."""
    req = urllib.request.Request(url, headers={"Authorization": "Bearer " + token,
                                               "Accept": "application/json"})
    for n in range(tries):
        try:
            with urllib.request.urlopen(req, timeout=30, context=tls_context()) as r:
                raw = r.read().decode("utf-8")
                return r.status, (json.loads(raw) if raw.strip() else {})
        except urllib.error.HTTPError as e:
            if e.code == 429 and n < tries - 1:
                time.sleep(min(int(e.headers.get("Retry-After", 2 ** (n + 1))), 30))
                continue
            return e.code, {}
        except (urllib.error.URLError, TimeoutError, OSError) as e:
            if n < tries - 1:
                time.sleep(2 ** n)
                continue
            raise HostError(f"network error talking to Bitbucket: {e}")
    raise HostError("Bitbucket kept answering 429")


HTTP_GET = http_get_json  # replaced in tests; never touch the network there


def bb_get(url, token):
    status, body = HTTP_GET(url, token)
    if status == 200:
        return body
    if status == 404:
        raise HostError("Bitbucket answered 404: token invalid OR repository not visible "
                        "to it (a private repository answers 404 to a bad token)")
    if status in (401, 403):
        raise HostError(f"Bitbucket answered {status}: token rejected or missing a scope")
    raise HostError(f"Bitbucket answered {status} for {url.split('?')[0]}")


def bb_paginate(url, token):
    values, size = [], None
    while url:
        page = bb_get(url, token)
        values.extend(page.get("values") or [])
        if size is None:
            size = page.get("size")
        url = page.get("next")
    if size is not None and size != len(values):
        raise HostError(f"incomplete pagination: Bitbucket said {size} items, read {len(values)}")
    return values


def list_prs_bitbucket(root, remote, line, only_pr, token):
    ws, slug = bitbucket_repo(run(["git", "remote", "get-url", remote], root).strip())
    base = f"{BB_API}/repositories/{ws}/{slug}"
    if only_pr is not None:
        prs = [bb_get(f"{base}/pullrequests/{only_pr}", token)]
    else:
        q = urllib.parse.quote(f'destination.branch.name="{line}" AND state="OPEN"', safe="")
        prs = [p for p in bb_paginate(f"{base}/pullrequests?q={q}&pagelen=50", token)
               if p.get("state") == "OPEN"]  # `q` has been seen ignoring state: filter here too
    out = []
    for p in prs:
        src = p.get("source") or {}
        full = ((src.get("repository") or {}).get("full_name") or f"{ws}/{slug}").lower()
        if full != f"{ws}/{slug}".lower():
            raise HostError(f"PR #{p.get('id')} comes from a fork ({full}); "
                            f"its branch is not readable from {remote}")
        files = []
        for d in bb_paginate(f"{base}/pullrequests/{p['id']}/diffstat?pagelen=100", token):
            if d.get("status") == "removed":
                continue
            path = ((d.get("new") or d.get("old")) or {}).get("path")
            if path:
                files.append({"path": path})
        branch = (src.get("branch") or {}).get("name", "")
        out.append({"number": p["id"], "headRefName": branch, "files": files,
                    "fetchRef": f"refs/heads/{branch}"})
    return out


def token_from_registry(peers_text):
    """PEER_RELAY_TOKEN, else the stdout of `host_token_cmd:` (frontmatter of .agents/peers.md),
    run without a shell. None when neither is configured."""
    env = os.environ.get("PEER_RELAY_TOKEN", "").strip()
    if env:
        return env
    bounds = frontmatter_bounds(peers_text)
    if not bounds:
        return None
    cmd = frontmatter(peers_text).get("host_token_cmd", "").strip()
    if not cmd:
        return None
    try:
        r = subprocess.run(shlex.split(cmd), capture_output=True, text=True, timeout=15)
    except (OSError, subprocess.TimeoutExpired, ValueError) as e:
        raise HostError(f"host_token_cmd failed to run: {type(e).__name__}")
    if r.returncode != 0 or not r.stdout.strip():
        raise HostError(f"host_token_cmd exited {r.returncode} without a token")
    return r.stdout.strip()


def list_prs(root, remote, line, only_pr, host, peers_text):
    """Host adapter entry point. Same contract for every host."""
    if host == "github":
        return list_prs_github(root, line, only_pr)
    if host == "bitbucket":
        token = token_from_registry(peers_text)
        if not token:
            raise HostError("Bitbucket token not configured (PEER_RELAY_TOKEN or "
                            "`host_token_cmd:` in .agents/peers.md)")
        return list_prs_bitbucket(root, remote, line, only_pr, token)
    raise HostError(f"unknown host {host!r}")


def pr_messages(root, remote, relay_dir, peer, self_name, pr):
    paths = [f["path"] for f in pr.get("files") or []
             if f["path"].startswith(relay_dir) and f["path"].endswith(".md")
             and not os.path.basename(f["path"]).startswith("_")]
    if not paths:
        return [], []
    run(["git", "fetch", "-q", remote, pr.get("fetchRef", f"pull/{pr['number']}/head")], root)
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


def open_pr_messages(root, remote, line, relay_dir, peer, self_name, only_pr,
                     host="github", peers_text=""):
    """Returns (found, odd, None) or (None, None, reason) - never [] for 'not checked'."""
    try:
        found, odd = [], []
        for pr in list_prs(root, remote, line, only_pr, host, peers_text):
            f, o = pr_messages(root, remote, relay_dir, peer, self_name, pr)
            found.extend(f)
            odd.extend(o)
        return found, odd, None
    except HostError as e:
        return None, None, f"{host}: {e}"
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
    ap.add_argument("--host", choices=("auto", "github", "bitbucket"), default="auto",
                    help="where open PRs are read (default: bitbucket for a bitbucket.org remote, else github)")
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

    try:
        host = detect_host(root, args.remote, args.host)
    except subprocess.CalledProcessError:
        print(f"error: remote `{args.remote}` not found", file=sys.stderr)
        return 1
    in_prs, odd, reason = open_pr_messages(root, args.remote, args.line, relay_dir, args.peer,
                                           self_name, args.pr, host, peers)
    checked = "checked" if reason is None else "NOT checked"
    print(f"peer {args.peer} · {ref} @ {head} · host {host} · PRs: {checked}")

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
