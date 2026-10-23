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
- **At quarter turn** — trios closed in the quarter that ended roll into `archive/`. The output depends on the **date**, not only on the trios: a dormant repo with no new commit goes red on `--check` (and on `/wiki-lint`'s `catalog-drift`, in CI) the first day of a new quarter. `--check` names that case — `drift: quarter rollover only — the index was generated for YYYY-Qn …` — when regenerating with the old quarter reproduces every file; the fix is to regenerate and commit. Pin `--quarter` where a date-independent answer is needed.
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
   - Reports drift (files that would change), **errors** and warnings. Exits 1 on drift or on any error:
     - a plan with no task and no `parent_task` (or a `parent_task` with no file);
     - a plan whose execution exists while the plan is `draft`, or an `approved` plan whose execution is `aborted`.
   - Warnings never fail (they are `/work-audit` R9's input): a file **skipped** because its name is not `YYYY-MM-DD_slug.md` (invisible to the index), missing frontmatter or `status`, a status outside that type's vocabulary, a non-ISO `updated` (never archives), an off-vocabulary `topic`, a `done` execution whose plan is still `approved` (pending `/wiki-sync`).
   - The script auto-detects the `*_wiki` vault under `--root`; pass `--vault <name>` if there is more than one.
3. **Generate:** `python3 .claude/skills/work-index/generate.py --root .`
   - Confirm on stderr that `trios == active + archive` (no trio lost).
4. **Sanity:** `git diff --stat {{project}}_wiki/work/_index.md` — should shrink; no `work_id` disappears (only migrates to archive).
5. Determinism: pass `--quarter YYYY-Qn` to pin the current quarter (useful when regenerating on a merge, guarantees identical output across machines).

## Notes

- **Idempotent:** running twice on the same day produces no diff.
- **No PyYAML:** own frontmatter parser in `generate.py` (shared with `/work-find`).
- `topic` vocabulary has **one** copy: the `topic-vocabulary` block in `_meta/conventions.md`, which the script parses. Extend it there before using a new label. Without the block the script falls back to the kit seed and says so.
- Plan-only sub-trios take their status from the plan via `PLAN_STATUS_TO_WORK` (shared with `/work-find`).
- Legacy files without a `YYYY-MM-DD_slug` name are skipped, with a warning naming each one.
