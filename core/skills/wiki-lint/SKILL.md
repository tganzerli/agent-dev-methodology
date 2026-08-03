---
name: wiki-lint
description: Check wiki health — stale pages, orphans, contradictions, abandoned work, broken citations. Use when the human invokes /wiki-lint or asks for a periodic health/maintenance analysis of the wiki.
disable-model-invocation: true
---

# Wiki Lint

Wiki health analysis per `.agents/METHODOLOGY.md` §6.3.

## Scope

The lint covers **three groups of checks**:

1. **Knowledge** (the knowledge dirs under `{{project}}_wiki/` — e.g. `domains/`, `entities/`, `services/`, `flows/`, `contracts/`, `cross-cutting/`, `decisions/`, `sources/`, `overview.md`).
2. **Work** (`{{project}}_wiki/work/tasks/`, `{{project}}_wiki/work/plans/`, `{{project}}_wiki/work/executions/`).
3. **Metadata** (`{{project}}_wiki/_meta/index.md`, `{{project}}_wiki/work/_index.md`, `{{project}}_wiki/_meta/log.md`).

## Checks — Knowledge

### Stale pages
For each page with `code_refs[]` in the frontmatter:

```bash
# For each file in code_refs, compare last-modified with page.updated
git log -1 --format="%aI" -- {code_ref}
```

If any `code_ref` was modified **after** `page.updated`, propose marking `status: stale`.

### Orphan pages
- No inbound wikilink from `{{project}}_wiki/_meta/index.md` or from other pages.
- Identify: `grep -r "page-name" {{project}}_wiki/` (excluding the page itself and `_meta/index.md`).

### Broken citations
- `file:line` pointing at a file that no longer exists.
- Verify with `test -f <file>` for each citation.

### Topics without a page
Heuristic: terms repeated across multiple pages but with no page of their own. List candidates.

### Contradictions
Heuristic: conflicting claims across pages. Flag for human review — do not try to resolve automatically.

## Checks — Work

### Abandoned tasks
- `{{project}}_wiki/work/tasks/*.md` with `status: open` for more than 14 days with no matching plan.

### Unexecuted plans
- `{{project}}_wiki/work/plans/*.md` with `status: approved` for more than 14 days with no matching execution.

### Stalled executions
- `{{project}}_wiki/work/executions/*.md` with `status: in_progress` and no update for more than 7 days.

### Incomplete trios
- Plan with no sibling task (same `work_id`).
- Execution with no sibling plan.

> The lint **does not mark `{{project}}_wiki/work/` pages as stale** — they are historical by design.

## Checks — Metadata

### `{{project}}_wiki/_meta/index.md` out of date
- Knowledge pages created but not listed in the index.
- Pages listed but nonexistent (broken link).

### `{{project}}_wiki/work/_index.md` out of date
- The work index is **generated** — do not hand-check its content. Run `python3 .claude/skills/work-index/generate.py --check --root .`; a non-zero exit means it drifted from the trio frontmatter and should be regenerated.

### Broken wikilinks
- `[[path]]` pointing at a nonexistent file.

## Expected output

Structure as markdown with sections:

```markdown
# Wiki Lint Report — YYYY-MM-DD

## 🔴 Critical (needs action)
- ...

## 🟡 Warnings (review when you can)
- ...

## 🟢 OK
- N knowledge pages (M stable, K draft, L stub, X stale)
- N pieces of work in progress
- ...

## Suggested next steps
- ...
```

## Persistence

**Do not** modify pages during the lint — only report. Changes wait for the human to approve.

You may append an entry to `{{project}}_wiki/_meta/log.md`:

```markdown
## [YYYY-MM-DD] lint | N critical, M warnings
```

## Anti-patterns

- ❌ Auto-fixing issues without human approval.
- ❌ Marking pages as `stale` without checking `git log` of the `code_refs`.
- ❌ Reporting everything as critical — calibrate severity.
- ❌ Forgetting to check `{{project}}_wiki/work/_index.md` separately from `_meta/index.md`.
