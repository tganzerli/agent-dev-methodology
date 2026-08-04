# Development Methodology — {{PROJECT}}

> Canonical, **LLM-agnostic** document. Any agent (Claude, Codex, Gemini/Antigravity, Cursor, etc.) operating in this repository must follow it. Per-agent specifics live in `.agents/llm/`.
>
> **Language note.** This methodology document is written in English. The **knowledge content** it governs — plans, wiki pages, tasks, executions — is authored in **{{KNOWLEDGE_LANG}}**, the language chosen for this project at install time. Code and identifiers are always in English. If `{{KNOWLEDGE_LANG}}` is unset, the installing agent MUST ask the human which language the wiki/plans should be written in before generating any content.

## 1. Objective

Ensure every piece of work over this repository produces three bound artifacts — **task → plan → execution** — and that the knowledge generated **composes over time** in the **wiki**, instead of being lost to chat history or scattered files.

## 2. Principles

1. **Everything is markdown.** Tasks, plans, executions, wiki — all `.md`. Any LLM can read and write them.
2. **Paths relative to repo root.** No `$HOME` or user-absolute paths.
3. **Human gate at every transition.** A plan does not run without approval. An execution does not close without review. The wiki does not update without an explicit `/wiki-sync`.
4. **Source-of-truth discipline.** Every technical claim in the wiki or in a plan carries a `file:line` citation. A claim without a citation is marked `⚠ unverified` until someone anchors it.
5. **Scope attribution.** Every wiki page, plan, and execution declares what it affects. In a single-repo project this is the module/area; in a monorepo it is which `apps/*` and/or `packages/*` (see the optional monorepo module).
6. **The methodology lives in exactly one place.** This file is the source. Per-LLM entry-point stubs (`CLAUDE.md`, `GEMINI.md`, `AGENTS.md`, …) only point here.

## 3. Repository structure (work layer)

```
{{repo}}/
├── .agents/                    ← meta (consumed by LLMs, outside the Obsidian vault)
│   ├── METHODOLOGY.md          ← this file (canonical source)
│   ├── rules/                  ← atomic rules (e.g. mandatory_planning_rule.md)
│   ├── llm/                    ← per-LLM specifics (claude.md, gemini.md, …)
│   └── mcp.md                  ← MCP server catalog (if any)
├── {{project}}_wiki/           ← Obsidian vault — knowledge + work
│   ├── _meta/                  ← conventions, index, log
│   ├── overview.md             ← map of the product
│   ├── <knowledge dirs>/       ← domain/entities/services/flows/contracts/decisions/sources…
│   └── work/                   ← task/plan/execution cycle (versioned, navigable)
│       ├── tasks/              ← human requests (input)
│       ├── plans/              ← analysis + plan (generated, human-gated)
│       └── executions/         ← live log of what was done (written during exec)
├── .claude/skills/             ← Agent Skills (see §8)
└── <your code>/                ← application/library source
```

**Why `work/` lives inside `{{project}}_wiki/`:** the Obsidian vault points at `{{project}}_wiki/`. Bringing tasks/plans/executions into the vault makes the **Obsidian graph** link work ↔ knowledge — a domain page gains natural backlinks to every plan/execution that touched it. Meanwhile `.agents/` keeps only meta (methodology, rules, per-LLM specifics) — consumed by LLMs but outside the human vault.

> This work-inside-the-vault layout is **load-bearing** and part of the irreducible seed of the methodology. Do not flatten it. See `docs/design-rationale.md` in the kit.

## 4. The work cycle

Every piece of work follows 5 steps. **Do not skip steps.**

> **Optional pre-flight (cold session):** before starting new work, consider `/sync-context` to make sure local code and wiki reflect the latest remote state. Not an inviolable rule — it is context hygiene. Skip in solo sessions on the same machine nobody else touched. See `.claude/skills/sync-context/SKILL.md`.

### 4.1. Unique identifier
Each piece of work gets an ID: `YYYY-MM-DD_short-slug-in-kebab-case` (e.g. `2026-05-14_diary-schedule-service`). This ID binds the three artifacts (`{{project}}_wiki/work/tasks/{ID}.md`, `.../plans/{ID}.md`, `.../executions/{ID}.md`).

### 4.2. Task (human-authored, optional collaboration)
File: `{{project}}_wiki/work/tasks/{ID}.md`. Template: `{{project}}_wiki/work/tasks/_template.md`. Contains:
- Frontmatter: `type: task` (fixed), `work_id`, `scope`, `status` (`open|in_progress|done|cancelled|aborted`), `updated`, `related[]`.
- The request in natural language.
- Declared scope: what areas/apps/packages it touches.
- Acceptance criteria.
- Links to relevant external sources (e.g. partner-team specs in `{{project}}_wiki/sources/external/`).
- **Optionally, stages** when the task is large or spans more than one action. Each stage can have its own plan/execution and be marked done individually.

**Authorship and collaboration:**
- The task is, by default, **filled in and edited by the human**. The LLM does **not** alter the task on its own initiative.
- The LLM **may** collaborate on the task **only when the human explicitly asks** (e.g. "create a task covering…", "extend the task scope to…", "add a stage with these steps…").
- Even after such a request, the LLM **proposes** the change (describes what it intends) and only **applies** it after explicit human approval. The gate here mirrors the plan gate (§4.3).
- `related[]` is a soft exception: the LLM may populate it when it spots pertinent wikilinks, but should still flag the change.
- **Additional stages may be proposed by the LLM during execution of a prior stage**, when that better serves the demand. Inclusion follows the same gate: LLM proposes, human approves, then the task is updated.

**Model recommendation (contextual, per role):** when materializing/starting the work, the LLM **recommends to the human which model to use** at each decision point — creating/refining the task, running each pre-plan analysis (§4.2.5), and writing the plan (§4.3). The choice is **contextual**: it depends on the specific content of the work (reasoning depth, breadth, mechanical vs. exploratory nature, cost/latency, risk), **not** a fixed role→model table. Model line-ups change often — treat any model list in `.agents/llm/*` as a hint that may be outdated, and map these dimensions to the **models actually available right now**. The recommendation is **advisory** (one justification line per point); the human may override.

### 4.2.5. Triage and pre-plan analyses (LLM, with parallel agents)

Before writing the plan, the LLM runs a **triage session**: decide whether **prior analyses** would materially improve the plan (the *what*) or how to conduct it (the *how*).

- **When worthwhile** (≥1 trigger): current architecture/behavior is uncertain and determines the plan's shape; more than one viable approach depends on investigation; cross-boundary or external-contract impact; risky/irreversible change or an area unknown to the agent.
- **When to skip:** small, mechanical, or already well-understood task — record `analyses: not needed` + one justification line and go straight to §4.3.
- **If needed:** decompose into **discrete, independent questions** (independence enables parallelism; chain only when genuinely sequential), **dispatch agents in parallel** (one per question), collect findings with `file:line` citations, **synthesize and validate the citations on the main thread** (sub-agents do not share context; a finding without a verifiable citation → `⚠ unverified`).

**Only after analyses close** does the LLM write the plan. The synthesis enters the plan as a dedicated **`Pre-plan analyses`** section (before §4.1 — see `.agents/rules/mandatory_planning_rule.md`). Triage/analysis does **not** replace or pre-empt the plan-approval gate (§4.3).

### 4.3. Plan (LLM, with human gate)
File: `{{project}}_wiki/work/plans/{ID}.md`. Mandatory structure in `.agents/rules/mandatory_planning_rule.md`. Must contain:
- `Pre-plan analyses` section (synthesis of §4.2.5 with `file:line` citations, or `analyses: not needed`)
- §4.1 Summary and understanding
- §4.2 Affected files
- §4.3 Changes and rationale
- §4.4 Risks and impact
- §4.5 Execution steps
- §4.6 **Scope** (areas / `apps/*` / `packages/*`)
- §4.7 **Wiki impact** (pages to create/update after execution)

**Gate:** the LLM does **not execute code** until the human approves the plan.

Plan frontmatter must include `type: plan`, `work_id`, `scope`, `status` (`draft|approved|executed`), `related[]` linking the knowledge pages the plan touches.

### 4.3.5. Branch (after approval, before execution)
If the project installs a git branching rule (`.agents/rules/git_branching_rule.md` — the core single-repo rule, or the monorepo module's variant at the same path), the branch for the work is created **after** the plan is `approved` and **before** any code runs. The branch name embeds the `work_id` (`<type>/<work_id>__<scope>`), binding the trio to its branch. The creation gate is the rule's own: no branch without an approved plan; never invent a branch name. In a project with no branching rule installed, skip this sub-step and follow the project's normal flow.

### 4.4. Execution (live log)
File: `{{project}}_wiki/work/executions/{ID}.md`. The LLM writes this **during** execution, not at the end. Update after each completed step. Template: `{{project}}_wiki/work/executions/_template.md`. Contains:
- Current status (`in_progress | done | aborted`).
- The plan's checklist with items marked as they advance.
- Commits involved (`git log` by hash).
- **Divergences from the plan, with justification** — if anything changed vs. the plan, record it here.
- Validations run (tests, lint, build) with results.
- List of wiki pages affected (input for `/wiki-sync`).

**Gate:** the human reviews the execution before calling `/wiki-sync`.

### 4.5. Wiki sync (manual)
Command: `/wiki-sync {ID}`. The LLM:
1. Reads `{{project}}_wiki/work/executions/{ID}.md`.
2. Updates or creates the knowledge pages listed under "affected wiki pages" (in `{{project}}_wiki/<knowledge dirs>/` — **not** in `{{project}}_wiki/work/`).
3. Updates `related[]` of the execution with wikilinks to every page it created/touched.
4. Updates `{{project}}_wiki/_meta/index.md` (knowledge catalog) and `{{project}}_wiki/work/_index.md` (work catalog — generated; see §5.5).
5. Appends an entry to `{{project}}_wiki/_meta/log.md`:
   `## [YYYY-MM-DD] wiki-sync | {ID} | N pages touched`

**Gate:** the human reviews the diff before commit.

### 4.6. Directory-scoped overrides
The full cycle is calibrated for changes to **product code**. A subtree whose work has a different shape — long-form writing, a data corpus, generated assets — MAY declare a **lighter local cycle** through a directory-scoped entry-point (e.g. a nested `CLAUDE.md`/`AGENTS.md` in that subtree). The override replaces the heavy trio/branch flow with one that fits the material (for prose: outline → draft → review → deliver) while **keeping the safeguards that still apply**: the knowledge language, the `file:line` citation discipline, the human gates, and any always-on rule (a performance claim still needs its evidence page). The override is **explicit and local** — it never silently loosens the cycle for product code, and the default everywhere else stays the full cycle. Record the override in the subtree's entry-point so every agent discovers it.

## 5. The wiki

### 5.1. Purpose
The wiki is a **composable artifact**. Each ingest (external sources, internal executions, exploratory questions) **adds** to the wiki instead of re-deriving knowledge from scratch. Cross-references already exist. Contradictions were already flagged. The synthesis already reflects everything ingested.

### 5.2. Structure
```
{{project}}_wiki/                  ← Obsidian vault
├── _meta/
│   ├── conventions.md          ← page format, frontmatter, citations
│   ├── index.md                ← navigable catalog of every knowledge page
│   └── log.md                  ← chronological, append-only
├── overview.md                 ← high-level product map
├── <knowledge dirs>/           ← domains/ entities/ services/ flows/ pages/ contracts/
├── cross-cutting/              ← subjects that cross boundaries
├── decisions/                  ← local ADRs
├── sources/
│   ├── external/               ← summaries of external sources (e.g. partner-team specs)
│   └── internal/               ← summaries of relevant executions
└── work/                       ← versioned work cycle
    ├── _index.md               ← generated work catalog (see §5.5)
    ├── tasks/                  ← human requests (type: task)
    ├── plans/                  ← analyses + plans (type: plan)
    └── executions/             ← live logs (type: execution)
```

> **Monorepo projects** additionally organize knowledge under `apps/<app>/` and `packages/<pkg>/`. That layout and its rules live in the optional **monorepo module** — install it only if the project has multiple apps/packages. See `modules/monorepo/` in the kit.

### 5.3. Page conventions
See `{{project}}_wiki/_meta/conventions.md`. Summary:
- Mandatory YAML frontmatter (`title`, `type`, `scope`, `status`, `updated`, `sources`, `code_refs`, `related`).
- `file:line` citation for every technical claim.
- Wikilinks `[[path/to/page]]` for cross-reference.
- Status (knowledge): `stub | draft | stable | stale`.
- Status (work — task): `open | in_progress | done | cancelled | aborted`.
- Status (work — plan): `draft | approved | executed`.
- Status (work — execution): `in_progress | done | aborted`.

### 5.4. Two catalogs, distinct semantics
- `{{project}}_wiki/_meta/index.md` catalogs **knowledge** (entities, services, domains, contracts, ADRs). Lint treats `stale` as "code changed since the docs".
- `{{project}}_wiki/work/_index.md` catalogs **work** (tasks/plans/executions). Lint **ignores** `stale` here — a finished execution is not outdated, it is historical.

### 5.5. The work index is generated, not hand-edited
`{{project}}_wiki/work/_index.md` (and `work/archive/YYYY-Qn.md`) are the **deterministic output** of `/work-index`, which reads trio frontmatter. Rules:
- **Catalog ≠ digest.** Each entry is **one line** (`emoji [[task]] · status · scope · [topic] — summary` + compact links to plan/execution). Long narrative lives in the execution, not the index.
- **One file per quarter.** `_index.md` keeps only `open`/`in_progress` trios (any date) + those closed in the **current quarter**. Older closed trios go to `work/archive/YYYY-Qn.md`.
- **Never edit `_index.md`/`archive/*` by hand.** Adjust trio frontmatter and run `/work-index`. On a merge conflict, **regenerate** instead of hand-merging.

Requires `summary` and `topic` frontmatter on every trio. See conventions §"work frontmatter".

### 5.6. Execution = historical log · Knowledge = living memory
- An **execution** is a **historical log** — chronological, immutable by design, never `stale`, archivable by quarter. It answers "**when/how** was this done".
- A **knowledge page** is the **living, thematic memory** — the distilled current state. It answers "**what do we know about X today**".
- **Rule — a recurring lesson graduates to a knowledge page.** When work reveals a costly lesson (recurring bug, discarded hypothesis, non-obvious workaround), that lesson **must not die in the execution**: promote it to a thematic knowledge page (`cross-cutting/` or `postmortems/`). Then "this bug came back — what did we already try?" is answered by reading **one** thematic page, not by chronological archaeology.
- To **find** old work: use `/work-find <term>` (ranked grep over executions+frontmatter) instead of re-reading the index.

## 6. Operational workflows

### 6.1. External source ingest
1. Human places the source in a known location (or links it).
2. Human requests the ingest.
3. LLM reads, discusses takeaways with the human.
4. LLM creates `{{project}}_wiki/sources/external/YYYY-MM-DD_slug.md` — short summary + absolute link + list of topics covered. **Do not copy raw content.**
5. LLM identifies and updates the affected wiki pages.
6. LLM updates `index.md` and `log.md`.

See `.claude/skills/ingest-source/SKILL.md`.

### 6.2. Query (exploratory question)
1. LLM reads `{{project}}_wiki/_meta/index.md` first.
2. Drills into relevant pages.
3. Answers with citations to wiki pages.
4. If the answer has durable value, offer to archive it as a new page.

### 6.3. Lint (wiki health)
Run periodically (`/wiki-lint`). Check: knowledge pages `status: stale`; orphan pages; contradictions; topics mentioned but without a page; broken cross-references; tasks `open` too long without a plan; plans `approved` too long without an execution; executions `in_progress` too long without progress. Lint **ignores** `{{project}}_wiki/work/` for `stale`.

### 6.4. Wiki sync (post-execution)
See §4.5.

## 7. Anti-patterns (do NOT)
- ❌ Execute code without plan approval.
- ❌ Write to the wiki without a `file:line` citation.
- ❌ Copy raw content from external sources into the wiki (use summary + link).
- ❌ Mix content from different areas/apps/packages in one page without it being cross-cutting.
- ❌ Rewrite an entire plan when the human asks for a punctual adjustment (use surgical edits).
- ❌ Close an execution without recording divergences from the plan.
- ❌ Update the wiki automatically in a PR — always go through `/wiki-sync` with a human gate.
- ❌ Pseudocode in the wiki. If it has no `file:line`, it is `⚠ unverified`.

## 8. Agent Skills

This project adopts the [Agent Skills spec](https://agentskills.io/specification). Skills live in `.claude/skills/` (the conventional path Claude Code discovers natively; other agents consume the same directory via an instruction in their entry-point). Each skill is a directory with `SKILL.md` (frontmatter + body) and optionally `references/*.md` (lazy-load).

Core skills (portable to any project): `work-cycle`, `wiki-sync`, `wiki-lint`, `ingest-source`, `commit`, `sync-context`, `work-index`, `work-find`, `work-audit`. Skills do not replace METHODOLOGY or rules — they offload material that can live on demand. Catalog in `.claude/skills/_index.md`.

## 9. For agents new to the project

In order:
1. Read this document (`.agents/METHODOLOGY.md`).
2. Read `.agents/rules/mandatory_planning_rule.md`.
3. Read `.agents/rules/git_branching_rule.md` (the core single-repo branching rule; if the monorepo module is installed, the same path holds its monorepo variant, which also brings `.agents/rules/knowledge_source_of_truth_rule.md`).
4. Read `.claude/skills/_index.md`.
5. Read `{{project}}_wiki/_meta/conventions.md` (if you will write to the wiki).
6. Read `{{project}}_wiki/_meta/index.md` (knowledge catalog).
7. Read `{{project}}_wiki/work/_index.md` (work catalog).
8. Read `{{project}}_wiki/overview.md` (to understand the product).
9. Read `.agents/llm/{your-name}.md` if it exists.

## 10. Version and evolution
This methodology is versioned with the code. Relevant changes append an entry to `{{project}}_wiki/_meta/log.md`: `## [YYYY-MM-DD] methodology-update | summary`.

### 10.1. Rules carry their provenance
A rule — or a single rule clause — that exists because of a concrete incident **cites that incident inline**, the same discipline as a wiki claim citing `file:line`. When a costly lesson hardens a rule (a recurring failure, a discarded hypothesis, a non-obvious workaround graduated from an execution per §5.6), the new clause names its origin: a dated `postmortems/`/`cross-cutting/` page, an ADR, or the commit/cycle that produced it. This makes each clause **self-justifying** — the methodology shows its evidence instead of asking for faith — and **safe to prune**, because you can tell why a clause exists before removing it. Keep provenance markers terse (a wikilink or a short parenthetical); the narrative lives in the cited page, not in the rule.

## 11. Optional modules
- **Monorepo module** (`modules/monorepo/` in the kit): git branching model, knowledge-canonical-in-`main` rule, `promote-knowledge`/`sync-knowledge`/`distribute-packages` skills, CI broadcast. Install only for multi-app/multi-package repos with per-app branches.
- **Cross-team module** (`modules/cross-team/` in the kit): `cross-team-handoff` skill, handoff/response/living-contract templates, extended source frontmatter. Install only when a partner team collaborates through their own LLM.
- **Intra-team module** (`modules/intra-team/` in the kit): `intra-team` skill (notes/requests/responses/handoffs/conflicts + coordination board), message/board templates, extended relay frontmatter. The mirror of cross-team for agents that **share** the repo — reference-first instead of self-contained. Install only when more than one agent works the repo and needs to coordinate.
- **Benchmarks module** (`modules/benchmarks/` in the kit): the empirical-claim discipline — a `benchmark_protocol_rule.md`, a benchmark-page template, a `run-benchmark` skill, and a conventions extension adding the `⚠ unverified <metric>` seal (a quantitative claim without a reproducible page cannot be cited). Registers a `bench` ephemeral branch type. Install when the project makes quantitative/empirical claims (performance, cost, accuracy, …) it must stand behind.
- **Contracts module** (`modules/contracts/` in the kit): the cross-boundary-contract discipline — a `contract_change_rule.md` requiring an atomic ADR + synchronized multi-artifact PR for any change to a versioned contract (public API, DB schema, wire/IPC protocol, event schema, FFI ABI), an ADR-contract template, and a `⚠ contract-drift` tag. Registers a `contract` ephemeral branch type. Install when the project exposes a versioned contract other code/teams depend on.
- **Dev-environment module** (`modules/dev-env/` in the kit): reproducible external-service environments — a `dev_environment_rule.md` (versioned per-service containers, mandatory healthcheck, persistent/ephemeral/benchmark lifecycle modes) and a `dev-env` skill. Install when the project depends on external services (DB, broker, cache, …) that must be reproducible across machines and CI.
