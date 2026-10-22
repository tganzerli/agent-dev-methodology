#!/usr/bin/env python3
"""Decide whether the local dev_<app> can be reset to its remote -- and, on request, reset it.

PRINCIPLE: the criterion is "NO LOCAL-ONLY CONTENT", never "0 commits ahead".

/promote-knowledge does not carry commits: it copies the END STATE of files to a
docs/<id>__knowledge branch cut from main. The content reaches main and comes back
through the broadcast, but the authoring commits stay only on dev_<app>, with other
hashes, and git counts them "ahead" forever (measured in one installation: 27 commits
ahead, none with code, a tree IDENTICAL to the remote's). So "ahead" is the SYMPTOM;
resetting is the goal, not the condition. Using it as the condition would be circular.

The condition is about what only the local branch has. For every file the local-only
commits touched (merge-base..HEAD), the remote's version must be IDENTICAL -- including
"absent on both sides" for a deletion. This:

  - accepts a branch BEHIND the remote (the broadcast arrived, fully or partly);
    requiring `git diff --quiet origin HEAD` would refuse almost always;
  - refuses an unpromoted new file, an unpromoted edit, and a local deletion the
    remote does not have yet (None != blob).

Conservative on purpose: if a file was promoted and then changed by someone else on
the remote, the blobs differ and the script REFUSES (accepted false negative). It costs
an inspection; it is the safe side.

Without --apply it WRITES NOTHING (only `git fetch`, unless --no-fetch). With --apply it
re-decides, demands --expect-head (the short sha the report printed: the human
confirmed THAT state), creates a backup branch, and only then runs
`git reset --hard <remote>/<branch>`.

Exit: 0 safe (or applied) · 1 refused · 2 usage/environment error.
A measurement is not a permission: the human confirms, at step 4 of /reset-dev-branch.
"""

import argparse
import datetime
import json
import os
import re
import subprocess
import sys

DEV = re.compile(r"^dev_[a-z0-9_]+$")
# dev_packages is the package trunk (another regime); the others are not dev_<app>.
NOT_APP = re.compile(r"^(main|staging_.*|demo_.*|dev_packages)$")
WIKI = "{{project}}_wiki/"


class Error(Exception):
    pass


def git(root, *args, check=True, stdin=None):
    p = subprocess.run(["git", "-C", root, *args], input=stdin,
                       capture_output=True, text=True, errors="replace")
    if check and p.returncode != 0:
        raise Error("git %s failed: %s" % (" ".join(args), p.stderr.strip()))
    return p


def out(root, *args):
    return git(root, *args).stdout.strip()


def ref_exists(root, ref):
    return git(root, "rev-parse", "--verify", "-q", ref, check=False).returncode == 0


def current_branch(root):
    p = git(root, "symbolic-ref", "--short", "-q", "HEAD", check=False)
    return p.stdout.strip() if p.returncode == 0 else ""


def in_progress(root):
    """merge/rebase/cherry-pick/revert half-way: reset --hard would destroy it."""
    found = []
    for name, path in (("merge", "MERGE_HEAD"), ("rebase", "rebase-merge"), ("rebase", "rebase-apply"),
                       ("cherry-pick", "CHERRY_PICK_HEAD"), ("revert", "REVERT_HEAD")):
        p = out(root, "rev-parse", "--git-path", path)
        if os.path.exists(p if os.path.isabs(p) else os.path.join(root, p)):
            found.append(name)
    return sorted(set(found))


def local_changes(root, base):
    """(status, path) of what the local-only commits changed. --no-renames: a rename
    becomes D+A, and each path is compared on its own."""
    raw = git(root, "diff", "--name-status", "-z", "--no-renames", base, "HEAD").stdout
    t = raw.split("\0")
    return [(t[i], t[i + 1]) for i in range(0, len(t) - 1, 2) if t[i]]


def blobs(root, ref, paths):
    """{path: sha|None} in one batch (cat-file --batch-check), not N calls."""
    if not paths:
        return {}
    data = "".join("%s:%s\n" % (ref, c) for c in paths)
    lines = git(root, "cat-file", "--batch-check", stdin=data).stdout.splitlines()
    return {c: (None if line.endswith(" missing") else line.split()[0]) for c, line in zip(paths, lines)}


def decide(root, remote, fetch=True):
    branch = current_branch(root)
    checks = []

    def reg(id_, name, ok, detail=""):
        checks.append({"id": id_, "name": name, "ok": bool(ok), "detail": detail})

    r = {"branch": branch, "remote": remote, "head": "", "origin": "", "ahead": 0, "behind": 0,
         "local_merges": 0, "local_files": 0, "outside_wiki": 0, "local_only": [],
         "untracked": [], "checks": checks, "safe": False}

    # 1 -- the branch is a dev_<app>
    allowed = bool(branch) and bool(DEV.match(branch)) and not NOT_APP.match(branch)
    reg(1, "branch is a dev_<app>", allowed, branch or "detached HEAD")
    if not allowed:
        return r

    r["head"] = out(root, "rev-parse", "--short", "HEAD")

    # 2 -- clean tracked tree: reset --hard would discard uncommitted changes
    dirty = out(root, "status", "--porcelain", "--untracked-files=no")
    reg(2, "clean tracked tree", not dirty, dirty.replace("\n", "; ")[:200])

    # 3 -- no merge/rebase/cherry-pick/revert half-way
    mid = in_progress(root)
    reg(3, "no git operation in progress", not mid, ", ".join(mid))

    # 4 -- the remote branch exists (after fetch)
    if fetch:
        p = git(root, "fetch", "-q", remote, branch, check=False)
        if p.returncode != 0:
            reg(4, "%s/%s reachable" % (remote, branch), False, p.stderr.strip()[:200])
            return r
    ref = "refs/remotes/%s/%s" % (remote, branch)
    exists = ref_exists(root, ref)
    reg(4, "%s/%s exists" % (remote, branch), exists, "" if exists else "run without --no-fetch")
    if not exists:
        return r
    r["origin"] = out(root, "rev-parse", "--short", ref)

    ahead, behind = out(root, "rev-list", "--left-right", "--count", "HEAD...%s" % ref).split()
    r["ahead"], r["behind"] = int(ahead), int(behind)
    r["local_merges"] = int(out(root, "rev-list", "--count", "--merges", "%s..HEAD" % ref))

    # 5 -- no local-only content
    p = git(root, "merge-base", "HEAD", ref, check=False)
    if p.returncode != 0:
        reg(5, "no local-only content", False, "histories with no common ancestor")
        return r
    changes = local_changes(root, p.stdout.strip())
    paths = sorted({c for _, c in changes})
    r["local_files"] = len(paths)
    r["outside_wiki"] = sum(1 for c in paths if not c.startswith(WIKI))
    here, there = blobs(root, "HEAD", paths), blobs(root, ref, paths)
    label = {"A": "new", "M": "modified", "D": "deleted", "T": "type"}
    status = {c: label.get(s[:1], s) for s, c in changes}
    r["local_only"] = [{"path": c, "kind": status.get(c, "?")} for c in paths if here[c] != there[c]]
    reg(5, "no local-only content", not r["local_only"],
        "%d file(s) differ from the remote" % len(r["local_only"]) if r["local_only"] else "")

    r["untracked"] = out(root, "ls-files", "--others", "--exclude-standard").splitlines()
    r["safe"] = all(c["ok"] for c in checks)
    return r


def backup_name(root, branch, day):
    base = "backup/%s-%s" % (branch, day)
    name, n = base, 1
    while ref_exists(root, "refs/heads/%s" % name):
        n += 1
        name = "%s-%d" % (base, n)
    return name


def text(r):
    L = ["%s @ %s   (%s/%s @ %s)" % (r["branch"] or "?", r["head"] or "?", r["remote"], r["branch"], r["origin"] or "?"),
         "  ahead: %d (%d merges)   behind: %d   files touched: %d (outside %s: %d)"
         % (r["ahead"], r["local_merges"], r["behind"], r["local_files"], WIKI, r["outside_wiki"])]
    for c in r["checks"]:
        L.append("  [%s] %d. %s%s" % ("ok  " if c["ok"] else "FAIL", c["id"], c["name"],
                                       ("  -- " + c["detail"]) if c["detail"] else ""))
    for s in r["local_only"][:30]:
        L.append("         LOCAL ONLY (%s): %s" % (s["kind"], s["path"]))
    if len(r["local_only"]) > 30:
        L.append("         ... and %d more" % (len(r["local_only"]) - 30))
    if r["untracked"]:
        L.append("  note: %d untracked file(s); the reset does not touch them" % len(r["untracked"]))
    if r.get("applied"):
        L.append("VERDICT: SAFE -- nothing local-only; reset APPLIED.")
    elif r["safe"]:
        L.append("VERDICT: SAFE -- nothing local-only. To apply (with a backup):")
        L.append("  python3 scripts/dev_branch_reset.py --apply --expect-head %s" % r["head"])
    else:
        L.append("VERDICT: REFUSED -- nothing was changed.")
    return "\n".join(L)


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--root", default=".", help="repository directory (default: .)")
    ap.add_argument("--remote", default="origin")
    ap.add_argument("--no-fetch", action="store_true", help="do not run `git fetch` before deciding")
    ap.add_argument("--apply", action="store_true", help="backup + git reset --hard (only if safe)")
    ap.add_argument("--expect-head", help="short sha of HEAD the report showed (required with --apply)")
    ap.add_argument("--date", help="YYYY-MM-DD for the backup name (default: today; for tests)")
    ap.add_argument("--format", choices=["text", "json"], default="text")
    a = ap.parse_args()

    root = os.path.abspath(a.root)
    try:
        if git(root, "rev-parse", "--git-dir", check=False).returncode != 0:
            raise Error("%s is not a git repository" % root)
        r = decide(root, a.remote, fetch=not a.no_fetch)

        if a.apply and r["safe"]:
            if not a.expect_head:
                r["safe"] = False
                r["checks"].append({"id": 6, "name": "--expect-head given", "ok": False,
                                    "detail": "use the sha from the report: %s" % r["head"]})
            elif a.expect_head != r["head"]:
                r["safe"] = False
                r["checks"].append({"id": 6, "name": "--expect-head matches HEAD", "ok": False,
                                    "detail": "expected %s, current %s" % (a.expect_head, r["head"])})
            else:
                bk = backup_name(root, r["branch"], a.date or datetime.date.today().isoformat())
                git(root, "branch", bk, "HEAD")
                ref = "refs/remotes/%s/%s" % (a.remote, r["branch"])
                git(root, "reset", "-q", "--hard", ref)
                if out(root, "rev-parse", "HEAD^{tree}") != out(root, "rev-parse", ref + "^{tree}"):
                    raise Error("after reset: HEAD's tree does not match the remote's")
                r.update(applied=True, backup=bk, undo="git reset --hard %s" % bk)
        elif a.apply:
            r["applied"] = False
    except Error as e:
        print("ERROR: %s" % e, file=sys.stderr)
        sys.exit(2)

    if a.format == "json":
        print(json.dumps(r, indent=2))
    else:
        print(text(r))
        if r.get("applied"):
            print("APPLIED: backup=%s   undo: %s" % (r["backup"], r["undo"]))
    sys.exit(0 if r["safe"] else 1)


if __name__ == "__main__":
    main()
