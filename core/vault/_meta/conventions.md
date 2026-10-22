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
summary: One sentence — the catalog line (required in generated-catalog dirs, ≤250 chars)
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
| `summary` | in generated-catalog dirs | One sentence, ≤250 chars. It **is** the page's line in the generated sub-index (`/wiki-index`); `/wiki-lint` gates on it. |
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

**Citations are point-in-time.** A `file:line` records what the source said **when the page was written**. In a closed trio (or any dated record) never "fix" a citation against today's file: an audit against the current version accuses every correct historical record and absolves the recent defect. Check against `git show <commit>:<file>` at the document's date; if the source moved on, **annotate** ("correct as of YYYY-MM-DD; the text now lives at …") instead of rewriting. Only a citation that was wrong when written is corrected. *(Origin: three correct records were rewritten to match a source changed since, and had to be restored.)*

**When NOT to cite:** domain definitions (cite the external source/ADR instead of code); process/methodology statements (cite `.agents/METHODOLOGY.md` or a rule).

## 3. Wikilinks

Use paths relative to the `{{project}}_wiki/` root:

```markdown
See [[entities/diary-configuration]] for details.
Compare with [[packages/core/entities/user]].
```

Wikilinks are recognized by Obsidian and greppable.

#### Catalog labels

`/wiki-index` titles its generated catalogs from this block (one `` - `key`: value `` per line; `{n}` = page count, `{dir}` = directory). The values below are the defaults; translate them in place when the vault is written in another language. Delete the block to fall back to the script's defaults.

<!-- catalog-labels:begin -->
- `decisions`: Decisions — Architecture Decision Records
- `cross-cutting`: Cross-cutting — knowledge that crosses boundaries
- `sources/external`: External sources — ingested summaries
- `postmortems`: Postmortems — lessons from costly bugs
- `pages`: Pages ({n})
<!-- catalog-labels:end -->

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
| `postmortem` | `postmortems/` | The lesson a costly bug taught: root cause, which layer should have caught it, where the lesson was promoted, and a reviewer replay case (METHODOLOGY §4.4.2). Blameless. Template: `postmortems/_template.md`. |
| `discovery` | `cross-cutting/` (default) or the owning area | Research/analysis pages that feed a future decision (input for an ADR). Born `draft`, become `stable` when the child ADR is registered, then serve as historical reasoning. |
| `index` | `_meta/index.md` and `_index.md` per section | Catalogs. |

Pages that cross boundaries live in `cross-cutting/`.

### Work (cataloged in `{{project}}_wiki/work/_index.md`)
| `type` | Directory | Content |
|---|---|---|
| `task` | `work/tasks/` | Human request. Status: `open | in_progress | future | paused | done | cancelled | aborted`. Human-owned. LLM edits in three tiers (METHODOLOGY §4.2): **substantive** edits (creating it, extending scope, adding a stage, changing request or criteria) only on explicit human request, proposed then applied after approval; `status`, `updated` and stage ticks are updated as work advances, ungated; **non-substantive** fixes (typo, broken link, formatting, frontmatter normalization) are allowed but announced in the same turn. |
| `plan` | `work/plans/` | LLM analysis + plan (follows `mandatory_planning_rule.md`). Status: `draft | approved | executed | cancelled | aborted`. |
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
risk: medium                          # plan only: low | medium | high (METHODOLOGY §4.4.1)
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
- **`topic`** — controlled-vocabulary labels for subject filtering and `/work-find`. A new label is added to the block below **before** use; `/work-index` reads the block and warns on off-vocabulary topics.

#### `topic` vocabulary

This block is the **only** copy: `/work-index` parses the backticked labels between the markers. Do not mirror it in a script constant — two copies drifted in every installation that kept both. Keep it small; an ad-hoc label is what makes `/work-find` useless later.

<!-- topic-vocabulary:begin -->
- `service` `entity` `flow` `domain` `contract` — knowledge-layer subject
- `build` `ci` `tooling` `refactor` `bugfix` `performance` — nature of the change
- `ui` `api` — surface
- `wiki` `methodology` `knowledge` — the vault and the method itself
<!-- topic-vocabulary:end -->

#### `parent_task` (optional) — sub-trio

A piece of work can spawn **sub-work** with its own plan and execution but **no task of its own**: an investigation that opens into separate fronts, an umbrella task whose stages become independent cycles. The plan and the execution then declare:

```yaml
parent_task: 2026-05-17_extended-protocol
```

Rules:

- **The parent task must exist** under `work/tasks/`. A `parent_task` pointing at a missing file is a data error, not a sub-trio.
- **The sub-trio has its own `work_id`** (date + slug), distinct from the parent's. It names the plan, the execution, and the branch like any other work. The slug stays kebab-case by convention; the tooling **tolerates** underscores in a sub-trio suffix (`<parent-id>_stepa`) — the plan gate reads the `work_id` from the branch non-greedily up to the `__` scope separator — so existing `_step*` names need no rename.
- **`/work-index` renders a sub-trio pointing at its parent**, as `sub · [[work/tasks/{parent}]] › {work_id}`. Without the field, the plan+execution pair reads as a "trio with no task" and the generated line links a file that never existed, with the summary degrading to the raw `work_id`.
- **Do not confuse it with a split trio.** A split trio is one piece of work whose `work_id` disagrees between the task and the plan/execution — that is drift to repair. A sub-trio is deliberate structure. **Check `parent_task` before renaming any artifact to "reunify" a trio**: in the project this kit came from, that check kept two deliberate sub-trios from being renamed as if they were drift.

#### The work index is generated, not hand-edited
`{{project}}_wiki/work/_index.md` and `work/archive/*.md` are the deterministic output of `/work-index` (reads trio frontmatter). Do not edit them by hand; adjust frontmatter and regenerate. On a merge conflict, regenerate rather than resolve by hand.

### Execution = historical log · Knowledge = living memory
- The **execution** is a chronological historical log — immutable by design, never `stale`, archivable by quarter. Answers "**when/how** was this done".
- A **knowledge page** is the living, thematic memory — the distilled current state. Answers "**what do we know about X today**".
- **Rule — a recurring lesson graduates to a knowledge page.** A costly lesson (recurring bug, discarded hypothesis, non-obvious workaround) must not die in the execution: promote it to a thematic page (`cross-cutting/` or `postmortems/`) so "what did we already try?" is answered by reading one page, not chronological archaeology.
- **Rule — a repeated review finding becomes a rule, not another comment.** A finding that already appeared in earlier work is fixed at the source (check, test, instruction line, rule clause); a `wrong`/`intentional` pattern goes to `REVIEW.md` "Do not flag". See METHODOLOGY §5.6.
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
- **plan** — `draft` → `approved` (human gate) → `executed` (set by `/wiki-sync`). Terminal alternatives: `cancelled` (the task was cancelled or absorbed before execution) and `aborted` (its execution was aborted). Leaving such a plan `approved` asserts something false — that it is authorized and waiting to run. `/work-index --check` fails on a plan whose execution exists while the plan is still `draft`, on an `approved` plan whose execution is `aborted`, and on a plan with no task (and no `parent_task`).
  - **Plan → work status.** When a trio has neither task nor execution status (a plan-only sub-trio), the generator maps the plan's: `draft`/`approved`/`executed` → `open`, `cancelled` → `cancelled`, `aborted` → `aborted`. `executed` with no execution stays `open` on purpose — it is an anomaly to notice, not to launder as `done`.
- **execution** — `in_progress` → `done`/`aborted`.

## 7. Do NOT
- ❌ Copy long excerpts from external sources (use summary + link).
- ❌ Pseudocode. If it is not a literal citation, it is prose.
- ❌ Mix scopes: a page whose scope spans two areas belongs in `cross-cutting/`.
- ❌ Update a page without updating `updated:`.
- ❌ Create a page without an entry in `{{project}}_wiki/_meta/index.md` — or, in a generated-catalog dir (`decisions/`, `cross-cutting/`, `sources/external/`, `postmortems/`), without a `summary` and a `/wiki-index` run.
- ❌ Hand-edit a generated `_index.md` (`status: generated` in its frontmatter), or keep a second list of the same pages elsewhere.
