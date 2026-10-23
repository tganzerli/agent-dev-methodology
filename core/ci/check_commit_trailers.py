#!/usr/bin/env python3
"""Fail on LLM co-authorship trailers — the mechanism behind the "No LLM co-authorship"
rule of the agent adapters (.agents/llm/claude.md §7).

Why it exists: the rule was text only. One project measured 16 violating commits on
`main` from at least two sessions, found by accident; another had 8 of 8 commits of one
trio violate it and cross push, CI and PR with no signal. The rule even named the string
being emitted — clarity was not missing, a mechanism was.

Two layers, one pattern list (this file):
  - `.githooks/commit-msg` calls `--message-file` — early feedback, but it only runs
    where someone ran `git config core.hooksPath .githooks`, and never on commits made
    through a host API (bots, web merges);
  - CI calls `<base>` on every PR and on every push to a permanent branch (base =
    the push's `before`) — the load-bearing layer, the only one that does not depend
    on anyone remembering a setup step.

Scope: only the commits the PR adds (merge-base(base, HEAD)..HEAD), never the whole
history. History already on a permanent branch cannot be rewritten without human
approval, so charging a PR for it would leave the check permanently red — and a red
pipeline nobody can fix is a pipeline nobody reads. Pass the PR's REAL base: a fixed
`origin/main` would put another branch's commits into a PR aimed at that branch.
A release/integration PR (`dev` -> `main`, `staging_<app>` -> `main`) carries commits
already on other permanent branches: pass each of them with `--exclude` (the CI
template excludes `main`, `dev`, `dev_*` and `staging_*`).

Fails loudly (exit 1) when it cannot verify: base that does not resolve, shallow clone,
empty range. Green by absence of cases is indistinguishable from "all good".

Usage:
  check_commit_trailers.py --message-file .git/COMMIT_EDITMSG     # commit-msg hook
  check_commit_trailers.py origin/<base> [--exclude origin/main ...] [--allow <full-sha>]

  --message-file F  check one message; everything after git's scissors line
                 (`# ---- >8 ----`, written by `git commit -v`; the `#` is git's
                 `core.commentChar`) is ignored, as git does.
  --exclude REF  also skip commits already reachable from REF (a permanent branch whose
                 history cannot be rewritten). Repeatable (`--exclude A --exclude=B`).
  --allow-empty  an empty range is ok, with a note — for push events only (a rewind
                 after a force-push, a branch created at an existing commit).
  --allow SHA    exempt one pre-existing commit, by FULL sha (exact match, printed in
                 the output). Each entry needs a recorded human decision. Repeatable.
"""
import argparse
import os
import re
import subprocess
import sys

# An attribution trailer names an agent when its e-mail is a known AGENT MAILBOX, or when
# its name is made ONLY of vocabulary words (products, filler, tiers, versions). Whole
# tokens, so "Claude Opus 4.5 (1M context)", "Gemini 2.5 Pro", "OpenAI o3" and "Cursor
# Agent" match, while "Dr. Gemini Jones", "Haider Ali" and "Max Mustermann" do not: one
# word outside the vocabulary (a real name) is enough to pass. A trailing "via ..." (a
# wrapper or host: "Claude Sonnet 4.5 via Some App") is dropped — the agent precedes it.
#
# Mailboxes, not vendor domains: a person who works at a vendor (`jane@anthropic.com`,
# `jane.gemini@google.com`) is a human co-author, and the commit-msg hook has no
# `--allow`. Each entry is a whole address (optional `<id>+` prefix for GitHub bots).
# An agent writing from an unlisted address is still caught by its name.
#
# Products that are also first names (PRODUCT_NAMELIKE: Claude, Devin, Jules, Junie,
# Kiro) count bare, with agent filler ("Claude Code", "Devin AI") or with a version
# ("Claude Max 4"); with a tier word alone they read as a person ("Claude Max", "Claude
# Pro", "Max Claude" pass). Trade-off, deliberate: a person who signs with ONLY such a
# name ("Claude <c@company.fr>", "Devin") is blocked — sign with the full name.
_GH_BOTS = ("copilot", r"copilot-swe-agent\[bot\]", r"claude\[bot\]", r"cursor\[bot\]",
            r"devin-ai-integration\[bot\]", r"gemini-code-assist\[bot\]",
            r"google-labs-jules\[bot\]", r"chatgpt-codex-connector\[bot\]")
AGENT_EMAIL = re.compile(
    r"^<?(?:noreply@anthropic\.com|cursoragent@cursor\.com|(?:noreply|codex)@openai\.com"
    r"|(?:noreply|no-reply|gemini|gemini-cli|antigravity|bard|jules)@google\.com"
    r"|copilot@github\.com|noreply@aider(?:\.chat)?"
    r"|(?:\d+\+)?(?:" + "|".join(_GH_BOTS) + r")@users\.noreply\.github\.com)>?$", re.I)
PRODUCT = {"anthropic", "opus", "sonnet", "haiku", "cursor", "copilot", "gemini", "codex",
           "openai", "chatgpt", "gpt", "aider", "windsurf", "codeium", "antigravity", "agy",
           "bard", "cline", "qwen", "q"}
PRODUCT_NAMELIKE = {"claude", "devin", "jules", "junie", "kiro"}
FILLER = {"code", "agent", "assist", "ai", "bot", "github", "google", "cli", "context", "model",
          "amazon", "developer", "cascade", "labs"}
TIER = {"pro", "flash", "ultra", "mini", "nano", "max", "lite", "turbo", "preview", "exp",
        "experimental", "latest", "thinking"}       # model tiers / release tags
MODEL_ID = re.compile(r"o\d+")                    # OpenAI reasoning ids: o1, o3, o4 (a product word)
VERSION = re.compile(r"[\d.]+[a-z]?|v?\d[\w.]*")  # 4.5, 2.0, 4o, 1m, v2
VIA = re.compile(r"(?i)\s+via(?:\s+.*)?$")
TRAILER = re.compile(r"(?im)^\s*(Co-Authored-By|Generated-By|Assisted-By):\s*(.*?)\s*(<[^>]*>)?\s*$")
BANNED = [
    (re.compile(r"(?im)^\s*Claude-Session:"), "Claude-Session trailer"),
    (re.compile(r"(?i)Generated with \[?Claude Code"), '"Generated with Claude Code" footer'),
]


def agent_trailer(name, email):
    if email and AGENT_EMAIL.search(email):
        return True
    tokens = [w for w in re.split(r"[^a-z0-9.]+", VIA.sub("", name).lower()) if w]
    words = [w for w in tokens if not VERSION.fullmatch(w)]
    versioned = len(words) < len(tokens)
    vocab = PRODUCT | PRODUCT_NAMELIKE | FILLER | TIER
    if not words or not all(w in vocab or MODEL_ID.fullmatch(w) for w in words):
        return False
    if any(w in PRODUCT or MODEL_ID.fullmatch(w) for w in words):
        return True
    # only first-name-like products left: a tier word without a version reads as a person
    return any(w in PRODUCT_NAMELIKE for w in words) and (
        versioned or not any(w in TIER for w in words))


RULE = 'Rule: .agents/llm/<agent>.md, "No LLM co-authorship on commits (non-negotiable)".'


def hits(message, comment_chars="#"):
    body = "\n".join(l for l in message.splitlines() if not (l and l[0] in comment_chars))
    found = [label for pattern, label in BANNED if pattern.search(body)]
    for m in TRAILER.finditer(body):
        if agent_trailer(m.group(2), m.group(3) or ""):
            found.append(f"LLM attribution trailer ({m.group(1)}: {m.group(2)})")
    return found


def git(*argv):
    return subprocess.run(["git", *argv], capture_output=True, text=True)


def cannot_verify(reason):
    print(f"check_commit_trailers: CANNOT VERIFY\n  ✗ {reason}", file=sys.stderr)
    print("  Passing here would be green by absence of cases.", file=sys.stderr)
    return 1


# `git commit -v` appends the diff below this line; git drops everything after it.
# Matching the diff would block a commit that merely edits a file quoting a banned
# string (this one, for instance). The line starts with git's comment character:
# `core.commentChar` (default `#`; `auto` picks the first of these unused in the message).
AUTO_COMMENT_CHARS = "#;@!$%^&|:"


def comment_chars():
    r = git("config", "core.commentChar")
    value = r.stdout.strip() if r.returncode == 0 else ""
    if value == "auto":
        return AUTO_COMMENT_CHARS
    return value[:1] or "#"


def check_message_file(path):
    chars = comment_chars()
    scissors = re.compile(r"(?m)^[" + re.escape(chars) + r"] -+ >8 -+$")
    try:
        with open(path, encoding="utf-8", errors="replace") as fh:
            message = scissors.split(fh.read(), maxsplit=1)[0]
    except OSError as e:  # missing, a directory, unreadable: a traceback reads as a crash
        return cannot_verify(f"cannot read --message-file `{path}`: {e.strerror or e}.")
    found = hits(message, chars)
    if not found:
        return 0
    print("BLOCKED: LLM attribution in the commit message:", file=sys.stderr)
    for label in found:
        print(f"  ✗ {label}", file=sys.stderr)
    print(f"  {RULE} The author is the human; the local git user already says so.",
          file=sys.stderr)
    return 1


def check_range(base, excludes, allow, allow_empty=False):
    if git("rev-parse", "--verify", "-q", base).returncode != 0:
        return cannot_verify(f"base `{base}` does not resolve (in CI: fetch it, with full depth).")
    git_dir = git("rev-parse", "--git-dir").stdout.strip()
    if os.path.exists(os.path.join(git_dir, "shallow")):
        return cannot_verify("shallow clone — the scan would silently miss commits "
                             "(in CI: fetch-depth: 0).")
    mb = git("merge-base", base, "HEAD")
    if mb.returncode != 0:
        return cannot_verify(f"no merge-base between `{base}` and HEAD.")
    rng = f"{mb.stdout.strip()}..HEAD"
    total = [c for c in git("log", "--format=%H", rng).stdout.split() if c]
    if not total and allow_empty:
        print(f"ok — nothing new in {base}..HEAD (a rewind or a branch created at an "
              "existing commit); no commit to check")
        return 0
    if not total:
        return cannot_verify(f"`{base}..HEAD` is empty — the base is probably wrong.")
    shas = total
    if excludes:
        out = git("log", "--format=%H", rng, "--not", *excludes)
        if out.returncode != 0:
            return cannot_verify(f"--exclude ref does not resolve: {out.stderr.strip()}")
        shas = [c for c in out.stdout.split() if c]

    offenders, exempt = [], []
    for sha in shas:
        msg = git("log", "-1", "--format=%B", sha).stdout
        found = hits(msg)
        if not found:
            continue
        subject = msg.splitlines()[0] if msg.strip() else "(empty message)"
        (exempt if sha in allow else offenders).append((sha, subject, found))

    for sha, subject, found in exempt:
        print(f"EXEMPT {sha[:10]} {subject} — {', '.join(found)} (--allow)")
    if offenders:
        print("check_commit_trailers: FAILED", file=sys.stderr)
        for sha, subject, found in offenders:
            print(f"  ✗ {sha[:10]} {subject}\n      -> {', '.join(found)}", file=sys.stderr)
        print(f"\n{len(offenders)} of {len(shas)} new commit(s). {RULE}", file=sys.stderr)
        print("Fix: this branch is yours and ephemeral — reword the messages (amend/rebase). "
              "Rewriting a PERMANENT branch needs human approval.", file=sys.stderr)
        return 1
    skipped = len(total) - len(shas)
    print(f"ok — {len(shas)} new commit(s) in {base}..HEAD"
          + (f" ({skipped} already on {', '.join(excludes)} skipped)" if skipped else "")
          + ", no LLM attribution")
    return 0


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("base", nargs="?")
    ap.add_argument("--message-file")
    ap.add_argument("--exclude", action="append", default=[])
    ap.add_argument("--allow", action="append", default=[])
    ap.add_argument("--allow-empty", action="store_true",
                    help="an empty range is ok, with a note (push events: a rewind after a "
                         "force-push, or a new branch at an existing commit). Never on a PR.")
    a = ap.parse_args()
    if a.message_file:
        return check_message_file(a.message_file)
    if not a.base:
        return cannot_verify("missing <base>. There is no default on purpose: pass the PR's "
                             "real base (GitHub Actions: origin/$GITHUB_BASE_REF).")
    bad = [s for s in a.allow if not re.fullmatch(r"[0-9a-f]{40}", s)]
    if bad:
        return cannot_verify(f"--allow takes full 40-char SHAs only, got {bad}.")
    return check_range(a.base, a.exclude, set(a.allow), a.allow_empty)


if __name__ == "__main__":
    sys.exit(main())
