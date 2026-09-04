# Wiki Conventions

> How every page in `{{project}}_wiki/` is written and maintained. Part of the methodology (see `.agents/METHODOLOGY.md`).
>
> **Language:** page content is authored in **{{KNOWLEDGE_LANG}}**. Frontmatter keys and `type`/`status` values are English tokens; prose is `{{KNOWLEDGE_LANG}}`.

## 1. Mandatory frontmatter

Every `.md` wiki page starts with this YAML block:

```yaml
---
title: Human page name
type: entity                    # entity | service | flow | domain | contract | page | adr | source | discovery | overview | index
scope:
  # Single-repo: use `area` (free text). Monorepo: use apps/packages (module installed).
  area: []                      # e.g. [billing, auth] — or []
  apps: []                      # monorepo only — e.g. [web, mobile] or []
  packages: []                  # monorepo only — e.g. [core, ui] or []
status: stub                    # stub | draft | stable | stale
updated: 2026-05-14             # ISO date — update on every change
sources:                        # links to sources/ backing this page
  - sources/external/2026-05-13_partner-spec.md
code_refs:                      # code files this page describes (used by lint for `stale`)
  - lib/domain/entities/diary_configuration.dart
related:                        # wikilinks
  - services/diary-schedule-service
  - entities/user
---
```

### Field meanings
| Field | Required | Notes |
|---|---|---|
| `title` | yes | How it appears in `index.md`. |
| `type` | yes | Determines which subdirectory the page lives in (§4). |
| `scope` | yes | At least one sub-field filled. Cross-boundary pages live in `cross-cutting/`. |
| `status` | yes | `stub` → `draft` → `stable` → `stale`. |
| `updated` | yes | Update manually when the page is touched. |
| `sources` | when applicable | Pages in `sources/` that originated the content. |
| `code_refs` | when applicable | Repo files described. Used by lint to detect `stale`. |
| `related` | recommended | Manual cross-references. |

## 2. `file:line` citation

Every technical claim needs a citation to its source file. Inline format:

```markdown
📎 [`user_adapter.dart:42`](lib/data/adapters/user_adapter.dart)
📎 [`user_adapter.dart:41-69`](lib/data/adapters/user_adapter.dart)   ← range
```

A claim without a citation **must** be marked `⚠ unverified` at the end of the paragraph until someone anchors it.

> **Module tags.** Optional modules define specialized uncertainty tags, appended into this file by their `conventions-extension.md` at install: `⚠ unverified <metric>` (benchmarks — a quantitative claim without a reproducible page) and `⚠ contract-drift` (contracts — a contract page out of sync with its definition). They are stricter, scoped variants of `⚠ unverified`.

**When NOT to cite:** domain definitions (cite the external source/ADR instead of code); process/methodology statements (cite `.agents/METHODOLOGY.md` or a rule).

## 3. Wikilinks

Use paths relative to the `{{project}}_wiki/` root:

```markdown
See [[entities/diary-configuration]] for details.
Compare with [[packages/core/entities/user]].
```

Wikilinks are recognized by Obsidian and greppable.

## 4. Page types and where they live

### Knowledge (cataloged in `{{project}}_wiki/_meta/index.md`)
| `type` | Directory | Content |
|---|---|---|
| `overview` | `overview.md`, `*/_index.md` | High-level maps and summaries. |
| `domain` | `domains/` | Business domains. |
| `entity` | `entities/` | Domain entities. |
| `service` | `services/` | Services (domain/data layer). |
| `flow` | `flows/` | Cross-screen/service flows within an area. |
| `page` | `pages/` | Relevant UI pages. |
| `contract` | `contracts/` | Contracts with a backend/partner. |
| `adr` | `decisions/` | Local architecture decision records. |
| `source` | `sources/external/` or `sources/internal/` | Summaries of ingested sources. |
| `discovery` | `cross-cutting/` (default) or the owning area | Research/analysis pages that feed a future decision (input for an ADR). Born `draft`, become `stable` when the child ADR is registered, then serve as historical reasoning. |
| `index` | `_meta/index.md` and `_index.md` per section | Catalogs. |

Pages that cross boundaries live in `cross-cutting/`.

### Work (cataloged in `{{project}}_wiki/work/_index.md`)
| `type` | Directory | Content |
|---|---|---|
| `task` | `work/tasks/` | Human request. Status: `open | in_progress | future | paused | done | cancelled | aborted`. Human-owned; LLM edits only on explicit request + approval. |
| `plan` | `work/plans/` | LLM analysis + plan (follows `mandatory_planning_rule.md`). Status: `draft | approved | executed`. |
| `execution` | `work/executions/` | Live execution log. Status: `in_progress | done | aborted`. |

**Important:** lint does **not** mark `work/` pages as `stale` when code changes — they are historical by design. Only knowledge pages are subject to `stale`.

### Work frontmatter
```yaml
---
title: 2026-05-14 — Initial DiaryScheduleService
type: plan                            # task | plan | execution
work_id: 2026-05-14_diary-schedule-service
scope: { area: [scheduling] }         # or apps/packages in a monorepo
status: approved
updated: 2026-05-14
summary: One sentence — what the work delivers. Feeds the generated catalog.
topic: [scheduling, service]          # controlled vocabulary (see below)
related:
  - domains/multiple-diaries
  - services/diary-schedule-service
---
```

`work_id` is shared by all three artifacts — it locates the full trio.

#### `summary` and `topic` (mandatory on new trios)
- **`summary`** — one sentence stating what the work delivers. It is the text shown in the generated catalog (`work/_index.md`). Long narrative lives **only** in the execution. Generator preference: `execution.summary` → `task.summary` → `title`.
- **`topic`** — controlled-vocabulary labels for subject filtering and `/work-find`. Seed the vocabulary in this file; a new label is added here before use. `/work-index` warns on off-vocabulary topics.

#### The work index is generated, not hand-edited
`{{project}}_wiki/work/_index.md` and `work/archive/*.md` are the deterministic output of `/work-index` (reads trio frontmatter). Do not edit them by hand; adjust frontmatter and regenerate. On a merge conflict, regenerate rather than resolve by hand.

### Execution = historical log · Knowledge = living memory
- The **execution** is a chronological historical log — immutable by design, never `stale`, archivable by quarter. Answers "**when/how** was this done".
- A **knowledge page** is the living, thematic memory — the distilled current state. Answers "**what do we know about X today**".
- **Rule — a recurring lesson graduates to a knowledge page.** A costly lesson (recurring bug, discarded hypothesis, non-obvious workaround) must not die in the execution: promote it to a thematic page (`cross-cutting/` or `postmortems/`) so "what did we already try?" is answered by reading one page, not chronological archaeology.
- To **find** old work: `/work-find <term>` (ranked grep over executions+frontmatter) instead of re-reading the index.

## 5. Recommended page structure
```markdown
---
{frontmatter}
---

# {Title}

## Summary
1-3 sentences. What it is, which area/app/package, status.

## Current state
How the code is today. `file:line` citations.

## Touch points
- Related entities: [[...]]
- Consuming services: [[...]]
- Backend contracts: [[...]]

## Decisions and trade-offs
If any. Point to an ADR in `decisions/` if large.

## Open items and gaps
What is still missing to document/implement/decide.
```

## 6. Status and lifecycle
### Knowledge pages
- **stub** — skeleton, no real content (frontmatter + title only).
- **draft** — under construction. May carry `⚠ unverified` and marked gaps.
- **stable** — every claim has a citation or source. No `⚠`.
- **stale** — `git log` shows a `code_refs` file changed after `updated`. Lint detects and marks it.

### Work pages
- **task** — `open` → `in_progress` → `done`; terminal `cancelled`/`aborted`.
  - **`future`** — accepted, deliberately **not** started (it depends on something that has not happened, or belongs to a later phase). It is the backlog status, and it is what keeps a decision from being re-litigated every time someone notices the gap again: the answer is "already decided, not now", with the trio to prove it.
  - **`paused`** — started, then suspended with work already on the ground. Distinct from `future`, because the cost of resuming is not the cost of starting: the execution log says how far it got.
  - Both are **non-terminal**, so `/work-index` keeps them in the active catalog rather than archiving them by quarter. A backlog item is not history.
- **plan** — `draft` → `approved` (human gate) → `executed`.
- **execution** — `in_progress` → `done`/`aborted`.

## 7. Do NOT
- ❌ Copy long excerpts from external sources (use summary + link).
- ❌ Pseudocode. If it is not a literal citation, it is prose.
- ❌ Mix scopes: a page whose scope spans two areas belongs in `cross-cutting/`.
- ❌ Update a page without updating `updated:`.
- ❌ Create a page without an entry in `{{project}}_wiki/_meta/index.md`.
