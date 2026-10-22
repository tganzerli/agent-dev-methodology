<!--
  Installs as: {{project}}_wiki/work/executions/_template.md
  See INSTALL.md §3 and METHODOLOGY.md §4.4.

  Authored CONTENT is written in {{KNOWLEDGE_LANG}}. Frontmatter keys/values
  stay English. This is a LIVE log — update it after each completed step,
  not only at the end. It is historical by design: never mark it `stale`,
  never rewrite past entries, only append/tick.
-->
---
title: {YYYY-MM-DD} — {human slug}
type: execution
work_id: {YYYY-MM-DD_slug}
scope:
  area: []                   # single-repo: free text
  # apps: []                 # monorepo only
  # packages: []             # monorepo only
status: in_progress          # in_progress | done | aborted
updated: {YYYY-MM-DD}
summary: One sentence — what this execution actually delivered. Feeds the generated work catalog.
topic: []                    # controlled vocabulary — see conventions.md §"work frontmatter"
related: []                  # wikilinks to knowledge pages touched
---

# Execution Log — {ID}

> **Live log.** Update this file after every completed step, not only at the end.
> ID, task, and plan share the same slug (`YYYY-MM-DD_slug`).

## Metadata

- **ID:** `{YYYY-MM-DD_slug}`
- **Task:** [[work/tasks/{ID}]]
- **Plan:** [[work/plans/{ID}]]
- **Status:** `in_progress` <!-- in_progress | done | aborted -->
- **Start:** `YYYY-MM-DD HH:MM`
- **Finish:** `—`
- **Scope:**
  - Area(s) affected: `[...]`
  <!-- Monorepo only:
  - Apps affected: `[...]`
  - Packages affected: `[...]`
  -->

## Checklist (mirrors plan §4.5)

> Copy the plan's step list here and tick as you advance. Never skip a step without recording a divergence.

- [ ] Step 1 — description
- [ ] Step 2 — description
- [ ] Step 3 — description
- ...

## Activity (chronological)

> Append-only. Every entry timestamped.

### `YYYY-MM-DD HH:MM` — start
- Opening note. What is being done right now.

### `YYYY-MM-DD HH:MM` — {step X done}
- What was done.
- Files touched: `path/to/file.ext`, `path/to/other.ext`.

## Commits

> Commits made during this execution (hash + title). Update as you commit.

- `—` (fill in when committing)

## Divergences from the plan

> If anything diverged from the plan, record it here **with justification**. If nothing diverged, write "None".

- **None.**

## Validations

> Each validation is its **command and the tail of its output** — not a claim. "Passed" without output is `⚠ unverified` (METHODOLOGY §4.4). Paste only the few lines that prove the result. Include the plan's §4.4 **Verification** command.

- [ ] Lint/static analysis — `{command}` → exit {code}
  ```
  {last lines of output}
  ```
- [ ] Test suite (scope: ...) — `{command}` → exit {code}
  ```
  {summary line: N passed, M failed}
  ```
- [ ] Build (if applicable) — `{command}` → exit {code}
- [ ] Plan §4.4 verification — `{command}` → {observed result}

## Agent review

> Clean-context `reviewer` sub-agent, before the human gate (METHODOLOGY §4.4.1). Risk tier `{low | medium | high}` (from the plan). For `low`, review may be skipped — write `skipped — low` and stop here. **At most 3 rounds**; with `Important` findings still open after round 3, stop and return to the human.

| Round | Range reviewed | Important | Nit | Pre-existing |
|---|---|---|---|---|
| 1 | `{base}..{head}` (full work diff) | 0 | 0 | 0 |

### Findings and outcome

> One row per finding. Outcome: `fixed` · `wrong` · `intentional` · `nit-ignored`. Last column: where it was **promoted** — a finding seen in earlier work becomes a rule/check/test/instruction line; a `wrong`/`intentional` pattern becomes a `REVIEW.md` "Do not flag" line (METHODOLOGY §5.6). Otherwise `—`.

| # | Round | Tag | `file:line` | Outcome | Promoted to |
|---|---|---|---|---|---|
| 1 | 1 | Important | `path/file.ext:NN` | fixed | — |

## Wiki pages affected

> Copy from plan §4.7. These are the pages `/wiki-sync {ID}` will create/update.

- `{{project}}_wiki/...` (CREATE | UPDATE | APPEND) — description of the change.

## Open notes

> Space for insights, open decisions, questions that came up during execution. These may graduate into ADRs or wiki page sections — see conventions.md §"Execution = historical log · Knowledge = living memory".

—
