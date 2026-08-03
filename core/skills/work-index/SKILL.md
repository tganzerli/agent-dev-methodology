---
name: work-index
description: Deterministically generate the work index {{project}}_wiki/work/_index.md + {{project}}_wiki/work/archive/YYYY-Qn.md from the trio frontmatter. Active catalog = open/in_progress + those closed in the current quarter; older ones go to archive/. Replaces hand-editing the index — kills drift and merge conflicts (regenerate > hand-merge). Use after closing/reopening a trio, after backfilling summary/topic, or when resolving an _index.md merge conflict.
argument-hint: "[--check] [--quarter YYYY-Qn] [--verbose]"
allowed-tools: Bash(python3 *), Bash(git *), Read
---

# Work Index

Generates the work catalog from the trio frontmatter. The index stops being a hand-edited showcase and becomes a **deterministic output**. See `.agents/METHODOLOGY.md` §5.5.

## When to use

- **After closing/reopening a trio** or changing `status`/`summary`/`topic` in the frontmatter.
- **After a backfill** of `summary`/`topic`.
- **At quarter turn** — trios closed in the quarter that ended roll into `archive/`.
- **On an `_index.md`/`archive/*` merge conflict** — `git checkout --theirs` (or `--ours`) to unblock and **regenerate** instead of resolving by hand.

## When NOT to use

- To edit a piece of work's narrative — that lives in the frontmatter `summary:` (one sentence) and the execution body (detail). The index is derived; never edit it directly.

## What it generates

| Output | Content |
|---|---|
| `{{project}}_wiki/work/_index.md` | Active: all `open`/`in_progress` + those closed in the current quarter. One line per trio. |
| `{{project}}_wiki/work/archive/YYYY-Qn.md` | Trios closed in each past quarter. |
| `{{project}}_wiki/work/archive/_index.md` | Router over the archive files. |

Line format: `emoji [[work/tasks/{id}]] · status · scope · [topic] — summary ↳ plan · exec`.
`summary` resolves by precedence: `execution.summary` → `task.summary` → `plan.summary` → `title`.

## Steps

1. `git branch --show-current` — run on the working branch. *(Monorepo module only)* avoid `demo_*`/`staging_*`.
2. **Dry-run:** `python3 .claude/skills/work-index/generate.py --check --root .`
   - Reports drift (files that would change) + warnings (`topic` outside vocabulary, trio without summary). Exits 1 if there is drift.
   - The script auto-detects the `*_wiki` vault under `--root`; pass `--vault <name>` if there is more than one.
3. **Generate:** `python3 .claude/skills/work-index/generate.py --root .`
   - Confirm on stderr that `trios == active + archive` (no trio lost).
4. **Sanity:** `git diff --stat {{project}}_wiki/work/_index.md` — should shrink; no `work_id` disappears (only migrates to archive).
5. Determinism: pass `--quarter YYYY-Qn` to pin the current quarter (useful when regenerating on a merge, guarantees identical output across machines).

## Notes

- **Idempotent:** running twice on the same day produces no diff.
- **No PyYAML:** own frontmatter parser in `generate.py` (shared with `/work-find`).
- `topic` vocabulary is seeded in `generate.py` (`VALID_TOPICS`) and documented in `_meta/conventions.md` §4 — extend it there before using a new label.
- Legacy files without a `YYYY-MM-DD_slug` name are ignored (per the work naming convention).
