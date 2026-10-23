#!/usr/bin/env python3
"""Read-only health check for the knowledge vault — the mechanism behind /wiki-lint.

Why a script: as prose checks an agent ran by reading the whole wiki, the lint cost
enough that it did not run, and violations of written norms survived for months.
A convention with no verification is a suggestion (METHODOLOGY §6.6).

READ-ONLY. It never edits a page, not even to mark `status: stale`. A verifier that
edits what it verifies is the next class of bug; marking stays human-gated.

GATES vs WARNINGS. A gate has an unambiguous definition and drives the exit code;
anything that needs interpretation is a warning. A lint where everything fails is a
lint nobody runs; one where nothing fails is a suggestion.

GATES RATCHET AGAINST A BASELINE (<vault>/_meta/lint-baseline.json), not against zero.
A gate fails only when its count RISES ABOVE the baseline, so a vault with old debt can
adopt the lint green and still block every regression. A gate born red is backlog, and
it trains everyone to ignore the exit code. Fix pages, then `--lower-baseline`. Raising
a baseline is a conversation, not a commit.

Run locally, it lints the WORKING TREE (untracked files included), not the commit.
To see what CI sees, run it in a fresh clone (SKILL.md).

Usage:
  python3 lint.py [--root .] [--vault NAME] [--only g1,g2] [--stale-days N] [--json]
  python3 lint.py --init-baseline     # first adoption: record today's counts (file must not exist)
  python3 lint.py --lower-baseline    # after fixing: lower counts that went down (never raises)

Exit: 0 = no gate above baseline · 1 = regression · 2 = usage error.
"""
import argparse
import datetime
import glob
import json
import os
import re
import subprocess
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(HERE, "..", "work-index"))
from generate import find_vault, frontmatter_bounds, parse_frontmatter  # noqa: E402

WORK_INDEX = os.path.join(HERE, "..", "work-index", "generate.py")
WIKI_INDEX = os.path.join(HERE, "..", "wiki-index", "generate.py")
INDEXED_DIRS = ["decisions", "cross-cutting", "sources/external", "postmortems"]  # wiki-index DIRS
MAX_SUMMARY = 250            # same limit as wiki-index
INDEX_MAX_BYTES = 20_480     # hand-kept catalogs: split into a generated sub-index past this
INDEX_LINE_MAX = 300
REQUIRED_FM = ["title", "type", "status", "updated"]
SKIP_TOP = {"work", ".obsidian", "_meta"}
# Normative docs whose `file:line` citations must resolve (METHODOLOGY principle 4).
RULE_DOCS = [".agents/METHODOLOGY.md", ".agents/rules/*.md", ".agents/llm/*.md"]
CITE = re.compile(r"`([A-Za-z0-9_./-]+\.[A-Za-z0-9]+):(\d+)(?:-(\d+))?`")
CODE_PATH = re.compile(r"`((?:scripts|\.claude/skills|\.githooks)/[A-Za-z0-9_./-]+\.(?:sh|py|yml|yaml|json))`")
ENTRY = re.compile(r"^- \[\[")
# Files an agent loads whole (rules, entry-points, skill bodies). Antigravity CLI cuts each rule
# file at ~24,000 bytes (24 KB) and the model never sees the rest — a gate or a 🔒 line
# past the cut is silently absent. The cap leaves headroom for de-templating and the
# per-project growth of a rule. Change it here if a target agent's limit differs.
RULE_MAX_BYTES = 22_000
ROOT_ENTRY_POINTS = ["AGENTS.md", "GEMINI.md"]


def read(path):
    with open(path, encoding="utf-8", errors="replace") as fh:
        return fh.read()


def load_pages(root, vault):
    out = []
    base = os.path.join(root, vault)
    for dirpath, dirnames, filenames in os.walk(base):
        dirnames[:] = [d for d in dirnames if d != ".obsidian"]
        rel_dir = os.path.relpath(dirpath, base)
        rel_dir = "" if rel_dir == "." else rel_dir
        for f in filenames:
            if f.endswith(".md"):
                text = read(os.path.join(dirpath, f))
                out.append(dict(rel=os.path.join(rel_dir, f), name=f[:-3], dir=rel_dir,
                                top=rel_dir.split(os.sep)[0], fm=parse_frontmatter(text),
                                body=text))
    return out


def is_template(p):
    return p["name"].startswith("_") or any(s.startswith("_") for s in p["dir"].split(os.sep))


def finding(check, path, msg):
    return dict(check=check, path=path, msg=msg)


# ── gates ────────────────────────────────────────────────────────────────────
def g_catalog_drift(ctx):
    out = []
    # A fresh vault (no trio yet, index never generated) has nothing to drift from.
    fresh = not ctx["work"] and not os.path.exists(
        os.path.join(ctx["root"], ctx["vault"], "work", "_index.md"))
    r = subprocess.run([sys.executable, WORK_INDEX, "--check", "--root", ctx["root"],
                        "--vault", ctx["vault"]], capture_output=True, text=True)
    if r.returncode != 0 and not fresh:
        why = [l for l in r.stderr.splitlines() if l.startswith(("drift", "✗"))]
        why.sort(key=lambda l: "quarter rollover" not in l)  # the date-only cause first
        out.append(finding("catalog-drift", f"{ctx['vault']}/work/_index.md",
                           "work index drift or trio error — run /work-index --check: "
                           + "; ".join(why[:3])))
    for d in INDEXED_DIRS:
        pages = glob.glob(os.path.join(ctx["root"], ctx["vault"], d, "*.md"))
        if not any(not os.path.basename(p).startswith("_") for p in pages):
            continue  # no page yet: the catalog is created with the first one
        r = subprocess.run([sys.executable, WIKI_INDEX, d, "--check", "--root", ctx["root"],
                            "--vault", ctx["vault"]], capture_output=True, text=True)
        if r.returncode == 1:
            out.append(finding("catalog-drift", f"{ctx['vault']}/{d}/_index.md",
                               f"generated catalog drifted — run /wiki-index {d}"))
    return out


def g_missing_summary(ctx):
    return [finding("missing-summary", p["rel"], "page in a generated-catalog dir without `summary`")
            for p in ctx["knowledge"] if p["dir"] in INDEXED_DIRS and not is_template(p)
            and not p["fm"].get("summary")]


def g_summary_too_long(ctx):
    out = []
    for p in ctx["knowledge"] + ctx["work"]:
        s = str(p["fm"].get("summary") or "")
        if len(s) > MAX_SUMMARY:
            out.append(finding("summary-too-long", p["rel"],
                               f"summary has {len(s)} chars (limit {MAX_SUMMARY}) — digest, not catalog entry"))
    return out


def g_frontmatter(ctx):
    out = []
    for p in ctx["knowledge"]:
        if is_template(p):
            continue
        miss = [k for k in REQUIRED_FM if not p["fm"].get(k)]
        if miss:
            out.append(finding("frontmatter", p["rel"], "missing: " + ", ".join(miss)))
    return out


def g_broken_wikilink(ctx):
    """A missing target is unambiguous, so it is a gate. Links inside code spans/fences
    are examples, and targets with placeholders ({ } * … ...) are documentation."""
    known = {p["rel"][:-3] for p in ctx["all"]} | {p["name"] for p in ctx["all"]}
    known |= {f"{d}/_index" for d in INDEXED_DIRS}  # generated on the dir's first page
    out = []
    for p in ctx["all"] + ctx["extra_sources"]:
        if is_template(p) or (p["dir"] == "_meta" and p["name"].startswith("lint-")):
            continue
        body = re.sub(r"```.*?```", "", p["body"], flags=re.S)
        body = re.sub(r"`[^`\n]*`", "", body)
        for tgt in re.findall(r"\[\[([^\]|#]+)", body):
            t = tgt.strip()
            if not t or any(c in t for c in "{}*<>") or "..." in t or "…" in t:
                continue
            t = t[:-3] if t.endswith(".md") else t
            if t not in known and t.split("/")[-1] not in known:
                out.append(finding("broken-wikilink", p["rel"], f"[[{t}]] has no target"))
    return out


def g_index_format(ctx):
    """Hand-kept catalogs: byte budget, one PHYSICAL line per entry, line length.
    The one-line convention lived in the index's own body and held nothing — there
    were two writers (/wiki-sync, /ingest-source) and zero checks."""
    out = []
    for p in ctx["all"]:
        if p["top"] == "work" or not (p["rel"] == os.path.join("_meta", "index.md")
                                      or p["name"] == "_index"):
            continue
        if p["fm"].get("status") == "generated":
            continue  # covered by catalog-drift
        size = len(p["body"].encode("utf-8"))
        if size > INDEX_MAX_BYTES:
            out.append(finding("index-format", p["rel"], f"{size} B > budget {INDEX_MAX_BYTES} B — "
                               "move a section to its own (generated) sub-index"))
        lines = p["body"].splitlines()
        for i, line in enumerate(lines):
            if not ENTRY.match(line):
                continue
            if len(line) > INDEX_LINE_MAX:
                out.append(finding("index-format", f"{p['rel']}:{i + 1}",
                                   f"entry has {len(line)} chars > {INDEX_LINE_MAX} — the detail lives in the page"))
            nxt = lines[i + 1] if i + 1 < len(lines) else ""
            if nxt.strip() and not nxt.startswith("#") and not ENTRY.match(nxt):
                out.append(finding("index-format", f"{p['rel']}:{i + 2}",
                                   "entry continues on another physical line — one line per entry"))
    return out


def g_rule_citation(ctx):
    """A rule describing code without pointing at it cannot be checked against reality;
    one pointing at a line that no longer exists is worse. Checks existence and range
    only — a citation is point-in-time, and its CONTENT is not compared with today's file."""
    out, root = [], ctx["root"]
    for pattern in RULE_DOCS:
        for doc in sorted(glob.glob(os.path.join(root, pattern))):
            rel = os.path.relpath(doc, root)
            for i, line in enumerate(read(doc).splitlines(), 1):
                for m in CITE.finditer(line):
                    target, end = m.group(1), int(m.group(3) or m.group(2))
                    tp = os.path.join(root, target)
                    if not os.path.isfile(tp):
                        out.append(finding("rule-citation", f"{rel}:{i}", f"`{target}` does not exist"))
                    elif end > len(read(tp).splitlines()):
                        out.append(finding("rule-citation", f"{rel}:{i}",
                                           f"`{m.group(0).strip('`')}` is past the end of the file"))
                for m in CODE_PATH.finditer(line):
                    if not os.path.exists(os.path.join(root, m.group(1))):
                        out.append(finding("rule-citation", f"{rel}:{i}", f"`{m.group(1)}` does not exist"))
    return out


def g_rule_size(ctx):
    """Every `.agents/rules/*.md` (any `trigger:` — agy cuts each rule file it loads, and
    `model_decision` rules load mid-session), the root entry-points and every
    `.claude/skills/*/SKILL.md` must fit RULE_MAX_BYTES. Skills are a precaution: the cap
    is measured on rules (⚠ unverified for skill bodies), and a rule's pointer into a
    skill section past the cut would point at nothing. Bytes, not characters: the limit
    is in bytes, and accented prose or emoji cost more than one."""
    root, out = ctx["root"], []
    files = sorted(glob.glob(os.path.join(root, ".agents", "rules", "*.md")))
    files += [os.path.join(root, f) for f in ROOT_ENTRY_POINTS if os.path.isfile(os.path.join(root, f))]
    files += sorted(glob.glob(os.path.join(root, ".claude", "skills", "*", "SKILL.md")))
    for path in files:
        size = os.path.getsize(path)
        if size > RULE_MAX_BYTES:
            out.append(finding("rule-size", os.path.relpath(path, root),
                               f"{size} B > {RULE_MAX_BYTES} B — an agent may cut it on load "
                               "(Antigravity: ~24 KB per rule file); move rationale/examples to a "
                               "skill's reference file, keep every 🔒 line"))
    return out


# ── warnings ─────────────────────────────────────────────────────────────────
def w_stale(ctx):
    out = []
    for p in ctx["knowledge"]:
        refs, upd = p["fm"].get("code_refs") or [], str(p["fm"].get("updated") or "")
        if isinstance(refs, str):
            refs = [refs]
        for ref in refs:
            if not upd or not os.path.exists(os.path.join(ctx["root"], ref)):
                continue
            r = subprocess.run(["git", "log", "-1", "--format=%cs", "--", ref], cwd=ctx["root"],
                               capture_output=True, text=True)
            last = r.stdout.strip()
            if last and last > upd:
                out.append(finding("stale", p["rel"], f"`{ref}` changed {last}, page updated {upd}"))
                break
    return out


def w_orphan(ctx):
    linked = set()
    for p in ctx["all"] + ctx["extra_sources"]:
        for t in re.findall(r"\[\[([^\]|#]+)", p["body"]):
            linked |= {t.strip(), t.strip().split("/")[-1]}
    return [finding("orphan", p["rel"], "no inbound wikilink") for p in ctx["knowledge"]
            if not is_template(p) and p["rel"] != "overview.md"
            and p["rel"][:-3] not in linked and p["name"] not in linked]


def w_stalled(ctx):
    today, lim, out = datetime.date.today(), ctx["stale_days"], []
    for p in ctx["work"]:
        st, upd = p["fm"].get("status"), str(p["fm"].get("updated") or "")
        if st not in {"open", "approved", "in_progress"}:
            continue
        try:
            age = (today - datetime.date.fromisoformat(upd)).days
        except ValueError:
            continue
        if age > lim:
            out.append(finding("stalled", p["rel"], f"`{st}` for {age} days (limit {lim})"))
    return out


YAML_COMMENT_KEYS = ("summary", "title")


def w_yaml_comment(ctx):
    """An unquoted `summary`/`title` holding ` #` is cut there: YAML (and the kit's
    parsers) read ` #...` as a comment, so `summary: merged in PR #29` catalogs as
    "merged in PR". A warning, not a gate: the value is valid YAML, only probably not
    what the author meant. Quote it."""
    out = []
    for p in ctx["all"]:
        if is_template(p):
            continue
        b = frontmatter_bounds(p["body"])
        if not b:
            continue
        for line in p["body"][b[1]:b[2]].splitlines():
            m = re.match(r"^(%s):\s*(.*)$" % "|".join(YAML_COMMENT_KEYS), line)
            if m and m.group(2)[:1] not in ("'", '"') and re.search(r"\s#", m.group(2)):
                out.append(finding("yaml-comment", p["rel"],
                                   f"unquoted `{m.group(1)}` holds ` #` — YAML drops the rest "
                                   f"as a comment; quote the value"))
    return out


GATES = {"catalog-drift": g_catalog_drift, "missing-summary": g_missing_summary,
         "summary-too-long": g_summary_too_long, "frontmatter": g_frontmatter,
         "broken-wikilink": g_broken_wikilink, "index-format": g_index_format,
         "rule-citation": g_rule_citation, "rule-size": g_rule_size}
WARNINGS = {"stale": w_stale, "orphan": w_orphan, "stalled": w_stalled,
            "yaml-comment": w_yaml_comment}


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--root", default=os.getcwd())
    ap.add_argument("--vault", default=None)
    ap.add_argument("--only", default=None, help="comma-separated gate/warning names")
    ap.add_argument("--stale-days", type=int, default=14)
    ap.add_argument("--json", action="store_true")
    ap.add_argument("--init-baseline", action="store_true")
    ap.add_argument("--lower-baseline", action="store_true")
    a = ap.parse_args()

    vault = a.vault or find_vault(a.root)
    if not vault:
        print("no *_wiki vault found under --root; pass --vault", file=sys.stderr)
        return 2
    only = set(a.only.split(",")) if a.only else None
    if only and only - set(GATES) - set(WARNINGS):
        print(f"unknown check(s): {sorted(only - set(GATES) - set(WARNINGS))}", file=sys.stderr)
        return 2

    allp = load_pages(a.root, vault)
    extra = []
    for d in (".agents",):
        # os.walk does not follow symlinks: .agents/skills -> ../.claude/skills (the Antigravity
        # skills link) must not pull every skill body into the wikilink check.
        # Dot-dirs and dot-files are pruned, as the recursive glob this replaced skipped them.
        for dirpath, dirs, filenames in os.walk(os.path.join(a.root, d)):
            dirs[:] = sorted(x for x in dirs if not x.startswith("."))
            for f in sorted(filenames):
                if f.startswith(".") or not f.endswith(".md"):
                    continue
                fp = os.path.join(dirpath, f)
                extra.append(dict(rel=os.path.relpath(fp, a.root), name=f[:-3],
                                  dir=d, top=d, fm={}, body=read(fp)))
    ctx = dict(root=a.root, vault=vault, stale_days=a.stale_days, all=allp, extra_sources=extra,
               knowledge=[p for p in allp if p["top"] not in SKIP_TOP and p["dir"] != ""
                          or p["rel"] == "overview.md"],
               work=[p for p in allp if p["top"] == "work" and not is_template(p)
                     and p["dir"] in ("work/tasks", "work/plans", "work/executions")])

    gates = {k: fn(ctx) for k, fn in GATES.items() if not only or k in only}
    warns = {k: fn(ctx) for k, fn in WARNINGS.items() if not only or k in only}
    counts = {k: len(v) for k, v in gates.items()}

    bpath = os.path.join(a.root, vault, "_meta", "lint-baseline.json")
    baseline = json.load(open(bpath)) if os.path.exists(bpath) else {}
    if a.init_baseline or a.lower_baseline:
        if only:
            print("baseline flags need the full gate set (drop --only)", file=sys.stderr)
            return 2
        if a.init_baseline and os.path.exists(bpath):
            print(f"{bpath} exists — use --lower-baseline; raising is a conversation", file=sys.stderr)
            return 2
        new = counts if a.init_baseline else {k: min(counts.get(k, 0), b) for k, b in baseline.items()}
        new = {k: v for k, v in sorted(new.items()) if v}
        with open(bpath, "w", encoding="utf-8") as fh:
            json.dump(new, fh, indent=2, sort_keys=True)
            fh.write("\n")
        print(f"baseline written: {new or '{} (all gates at zero)'}")
        return 0

    over = {k: (n, baseline.get(k, 0)) for k, n in counts.items() if n > baseline.get(k, 0)}
    under = {k: (counts[k], b) for k, b in baseline.items() if k in counts and counts[k] < b}

    if a.json:
        print(json.dumps(dict(gates=gates, warnings=warns, over_baseline=over,
                              under_baseline=under), ensure_ascii=False, indent=1))
        return 1 if over else 0

    print(f"Wiki lint — {datetime.date.today()} — {vault} ({len(allp)} pages)")
    print("GATES (drive the exit code; ratchet against the baseline)")
    for k, hits in gates.items():
        b = baseline.get(k, 0)
        print(f"  {'✗' if k in over else ('⚠' if hits else '✔')} {k}: {len(hits)}"
              + (f" (baseline {b})" if b else ""))
        for h in hits[:20]:
            print(f"      {h['path']} — {h['msg']}")
        if len(hits) > 20:
            print(f"      … and {len(hits) - 20} more")
    if warns:
        print("WARNINGS (need a human reading; never fail)")
    for k, hits in warns.items():
        print(f"  {'⚠' if hits else '✔'} {k}: {len(hits)}")
        for h in hits[:8]:
            print(f"      {h['path']} — {h['msg']}")
        if len(hits) > 8:
            print(f"      … and {len(hits) - 8} more")
    for k, (n, b) in sorted(over.items()):
        print(f"✗ {k}: {n} — above baseline {b}. Regression.")
    for k, (n, b) in sorted(under.items()):
        print(f"↓ {k}: {n} — below baseline {b}. Run --lower-baseline and commit it.")
    return 1 if over else 0


if __name__ == "__main__":
    sys.exit(main())
