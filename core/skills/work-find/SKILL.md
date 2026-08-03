---
name: work-find
description: Search old work (executions + trio frontmatter) by term/topic and return ranked pointers (work_id, status, summary, path:line) — without re-reading the whole _index.md. Use when the human asks "how was X done", "has this bug appeared before?", "what have we already tried for Y", or before reopening a known problem. Complements /work-index (catalog) with full-text search.
argument-hint: "<terms...> [--topic T] [--status S] [--top N]"
allowed-tools: Bash(python3 *), Bash(rg *), Read
---

# Work Find

Ranked search over the work trios. Answers "recover past work efficiently" without loading the whole index into context.

## When to use

- **"How was X done?"** — point lookup by feature/service.
- **"This bug is back — what did we try?"** — recover discarded hypotheses and prior fixes. If the lesson already graduated to a knowledge page (the execution↔knowledge rule in `conventions.md`), the search points at the trio → follow its `related:` to the thematic page.
- **Before reopening a known problem** — avoid redoing work.

## How it works

```bash
python3 .claude/skills/work-find/find.py <terms...> --root . [--top 8] [--topic T] [--status S]
```

- **AND** of all terms, case-insensitive, **word boundary** (`cat` does not match `category`).
- Ranking: match in `title`/`summary`/`topic` (weight 3) > match in the body (weight 1); recency (`updated`) breaks ties.
- Returns **pointers**, not content: `[status] work_id [topics]` + summary + `work/executions/{id}` + `path:line` of the first matching snippet. The agent then opens only the 2-3 relevant trios with `Read`.
- Auto-detects the `*_wiki` vault under `--root`; pass `--vault <name>` if there is more than one.

## Filters

| Flag | Effect |
|---|---|
| `--topic T` | Only trios with `T` in the frontmatter `topic`. Precise subject search. |
| `--status S` | Filter by trio status (`open`, `done`, …). |
| `--top N` | Max results (default 8). |

## Recommended steps

1. Run with 2-3 specific terms.
2. If noisy, narrow with `--topic` (more precise than a free term).
3. Open the top 2-3 with `Read` (executions first — the historical log).
4. If the answer is a recurring lesson, follow `related:` to the knowledge page (living memory).

## Notes

- Reuses the frontmatter parser from `/work-index` (`../work-index/generate.py`).
- Does not replace `/work-index` (catalog/navigation) — it is the **search** axis. Both read the same frontmatter.
- Pure-shell fallback if the script fails: `rg -l -i "<term>" {{project}}_wiki/work/executions/`.
