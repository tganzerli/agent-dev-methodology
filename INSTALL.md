# INSTALL — Agent Playbook

> **You are an LLM agent** (Claude, Codex, Gemini/Antigravity, Cursor, …). A human has pointed you at this kit and asked you to install this development methodology into a **target project**. This file is your executable playbook. Follow it top to bottom. Do not improvise structure — the layout is load-bearing (see `docs/design-rationale.md`).
>
> **Golden rule of this install:** you are scaffolding a *methodology*, not doing project work yet. Create files, ask the interview questions, wire the entry-points. Do **not** start writing product code or documenting the codebase until the methodology is in place and the human confirms.

## 0. Prerequisites

- A target project repo (may be empty or existing). Know its **root path**.
- The human available to answer a short interview (§1).
- Obsidian is the intended graph tool for the wiki. The vault is a plain folder of markdown; Obsidian is not required to *install*, only to *browse the graph* later.

## 1. Install interview (ask the human, then record answers)

Ask these before creating anything. Keep it to one round; propose sensible defaults so the human can just confirm.

| # | Question | Placeholder it fills | Default |
|---|---|---|---|
| 1 | **Project name?** (human-readable) | `{{PROJECT}}` | folder name |
| 2 | **Vault folder slug?** The knowledge vault will be `<slug>_wiki/`. | `{{project}}` → vault `{{project}}_wiki/` | project name, kebab-case |
| 3 | **Knowledge-content language?** Docs of this kit stay English, but plans/wiki/tasks are authored in this language. | `{{KNOWLEDGE_LANG}}` | ask — do not assume |
| 4 | **Is this a monorepo** with multiple apps and/or shared packages, each on its own long-lived branch? | installs `modules/monorepo/` | no |
| 5 | **Which agents** will operate in this repo? (Claude Code, Codex, Gemini/Antigravity, Cursor, …) | which `adapters/*` + entry-points to generate | Claude + a generic `AGENTS.md` |
| 6 | **Does a partner team** (e.g. backend) collaborate through their own LLM, exchanging specs/contracts? | installs `modules/cross-team/` | no |
| 7 | **Git host?** (GitHub, GitLab, Bitbucket, none/local) | wording of monorepo CI stubs + PR guidance | GitHub |
| 8 | **Do multiple agents work this repo** — concurrently, or handing work across sessions — and need to coordinate / hand off? | installs `modules/intra-team/` | no |
| 9 | **Does the project make quantitative/empirical claims** (performance, cost, accuracy, …) it must stand behind? | installs `modules/benchmarks/` | no |
| 10 | **Does the project expose a versioned contract** other code/teams/systems depend on (public API, DB schema, wire/IPC protocol, event schema, FFI ABI)? | installs `modules/contracts/` | no |
| 11 | **Does the project depend on external services** (DB, broker, cache, …) that must be reproducible across machines and CI? | installs `modules/dev-env/` | no |

> **Never guess question 3.** If the human does not state a knowledge language, ask explicitly. Everything the methodology generates (plans, wiki pages) is in that language; getting it wrong means rewriting the vault.

Record the answers in a short block you will paste into `{{project}}_wiki/_meta/log.md` as the first entry (§6).

## 2. Placeholder substitution

Every template file in this kit uses `{{...}}` placeholders. When you copy a file into the target project, replace:

| Placeholder | Replace with |
|---|---|
| `{{PROJECT}}` | human-readable project name (answer 1) |
| `{{project}}` | vault slug (answer 2) — the vault dir is `{{project}}_wiki` |
| `{{repo}}` | target repo folder name |
| `{{KNOWLEDGE_LANG}}` | knowledge-content language (answer 3) |

Do a final grep for `{{` after install — **no placeholder may remain** in the target project (§7 checklist).

## 3. Install the CORE (always)

The core is portable to any repo, monorepo or not. Copy and de-template these from `core/` into the target project:

```
kit core/                              →  target project
──────────────────────────────────────────────────────────
core/METHODOLOGY.md                    →  .agents/METHODOLOGY.md
core/rules/mandatory_planning_rule.md  →  .agents/rules/mandatory_planning_rule.md
core/rules/git_branching_rule.md       →  .agents/rules/git_branching_rule.md   (single-repo default; monorepo module §4 overrides at this path)
core/vault/_meta/conventions.md        →  {{project}}_wiki/_meta/conventions.md
core/vault/_meta/index.md              →  {{project}}_wiki/_meta/index.md
core/vault/_meta/log.md                →  {{project}}_wiki/_meta/log.md
core/vault/overview.md                 →  {{project}}_wiki/overview.md
core/vault/.obsidian/                  →  {{project}}_wiki/.obsidian/
core/templates/task.md                 →  {{project}}_wiki/work/tasks/_template.md
core/templates/plan.md                 →  {{project}}_wiki/work/plans/_template.md
core/templates/execution.md            →  {{project}}_wiki/work/executions/_template.md
core/templates/wiki-page.md            →  {{project}}_wiki/_meta/_page_template.md
core/templates/source.md               →  {{project}}_wiki/sources/external/_template.md
core/skills/*                          →  .claude/skills/*
```

Then create the empty work directories: `{{project}}_wiki/work/{tasks,plans,executions}/` and `{{project}}_wiki/work/archive/`.

The core now ships a single-repo git branching rule (`main`/`dev` + plan-gated ephemerals); the monorepo module (§4) replaces it at the same path with the multi-app topology.

**Core skills to install** (from `core/skills/`): `work-cycle`, `wiki-sync`, `wiki-lint`, `ingest-source`, `commit`, `sync-context`, `work-index`, `work-find`, `work-audit`, and the skills index `_index.md`. The `work-index` and `work-find` skills ship a small Python script each — copy the whole skill directory.

**Knowledge directory seed.** Create the knowledge subdirs the project will use. For a single-repo project: `{{project}}_wiki/{domains,entities,services,flows,pages,contracts,decisions,cross-cutting,sources/external,sources/internal}/`. For a monorepo, the monorepo module (§4) adds `apps/` and `packages/` layout instead.

## 4. Install the MONOREPO module (only if answer 4 = yes)

Adds the machinery for multiple apps/packages on per-app branches. Copy from `modules/monorepo/`:

```
modules/monorepo/rules/git_branching_rule.md            →  .agents/rules/git_branching_rule.md
modules/monorepo/rules/knowledge_source_of_truth_rule.md→  .agents/rules/knowledge_source_of_truth_rule.md
modules/monorepo/skills/*                               →  .claude/skills/*  (promote-knowledge, sync-knowledge, distribute-packages)
modules/monorepo/scripts/*                              →  scripts/          (broadcast stubs — adapt to the git host, answer 7)
```

Then reorganize the vault knowledge dirs under `{{project}}_wiki/apps/<app>/` and `{{project}}_wiki/packages/<pkg>/` per `modules/monorepo/README.md`, and follow its **roster checklist** for wiring each app/package into the branch topology and CI.

**If answer 4 = no:** skip this module entirely. In a single-repo project these skills collapse to no-ops (there is no second branch to promote to). Do not install them.

## 5. Install the CROSS-TEAM module (only if answer 6 = yes)

Adds bidirectional LLM↔LLM collaboration with a partner team. Copy from `modules/cross-team/`:

```
modules/cross-team/skills/cross-team-handoff/  →  .claude/skills/cross-team-handoff/
modules/cross-team/templates/*                 →  {{project}}_wiki/sources/external/_handoff_templates/
modules/cross-team/conventions-extension.md    →  append its frontmatter fields into {{project}}_wiki/_meta/conventions.md
```

Follow `modules/cross-team/README.md` to extend the source-page frontmatter (`direction`, `doc_role`, handoff `status`, `external_tickets`, provenance) and register the new skill in the skills index.

**If answer 6 = no:** skip. The core `ingest-source` skill already handles one-directional ingest of external docs; the cross-team module is only needed when you also **author outbound** handoffs and maintain a living contract with a partner LLM.

## 5-bis. Install the INTRA-TEAM module (only if answer 8 = yes)

Adds agent↔agent coordination **inside one repo** — the mirror of cross-team, for agents that **share** the repository. Copy from `modules/intra-team/`:

```
modules/intra-team/skills/intra-team/   →  .claude/skills/intra-team/
modules/intra-team/templates/*          →  {{project}}_wiki/work/relay/_templates/
modules/intra-team/conventions-extension.md  →  append its fields into {{project}}_wiki/_meta/conventions.md
```

Then:
- Create `{{project}}_wiki/work/relay/` and seed `{{project}}_wiki/work/relay/_board.md` from the coordination-board template.
- Register `intra-team` in `.claude/skills/_index.md` — mark it **hybrid** (agent-invocable; `note` is autonomous, all other flows carry an in-body human gate).
- **No script change needed:** `work-index`/`work-find`/`work-audit` scan only `tasks`/`plans`/`executions`, so `work/relay/` is ignored by design (relay docs are historical, never `stale`; `_board.md` is their own catalog).

Follow `modules/intra-team/README.md` for the reference-first rule, the claim-state tags (`✅ landed` / `⚠ in-flight` / `🔒 intent`), and the message roles.

**If answer 8 = no:** skip. A single agent working the repo alone needs nothing here — the trio and the execution log already record what one agent does.

## 5-ter. Install the BENCHMARKS module (only if answer 9 = yes)

Adds the empirical-claim discipline: a quantitative claim needs a reproducible evidence page, or it carries `⚠ unverified <metric>` and cannot be cited. Copy from `modules/benchmarks/`:

```
modules/benchmarks/rules/benchmark_protocol_rule.md  →  .agents/rules/benchmark_protocol_rule.md
modules/benchmarks/templates/benchmark-page.md       →  {{project}}_wiki/benchmarks/_template.md
modules/benchmarks/skills/run-benchmark/             →  .claude/skills/run-benchmark/
modules/benchmarks/conventions-extension.md          →  append into {{project}}_wiki/_meta/conventions.md
```

Then: create `{{project}}_wiki/benchmarks/`; register `run-benchmark` (manual-only) in `.claude/skills/_index.md`. The module registers a `bench` ephemeral branch type (already anticipated in `core/rules/git_branching_rule.md`). Benchmark pages are authored in {{KNOWLEDGE_LANG}}. See `modules/benchmarks/README.md`.

**If answer 9 = no:** skip. The core `⚠ unverified` citation discipline still applies to non-quantitative claims.

## 5-quater. Install the CONTRACTS module (only if answer 10 = yes)

Adds the cross-boundary-contract discipline: a change to a versioned contract requires an atomic ADR + synchronized multi-artifact PR. Copy from `modules/contracts/`:

```
modules/contracts/rules/contract_change_rule.md  →  .agents/rules/contract_change_rule.md
modules/contracts/templates/adr-contract.md      →  {{project}}_wiki/decisions/_templates/adr-contract.md
modules/contracts/conventions-extension.md       →  append into {{project}}_wiki/_meta/conventions.md
```

Then: ensure `{{project}}_wiki/decisions/` exists; the module registers a `contract` ephemeral branch type (already anticipated in `core/rules/git_branching_rule.md`). If the benchmarks module is installed, the rule's hot-path regression gate references it. No skill. See `modules/contracts/README.md`.

**If answer 10 = no:** skip.

## 5-quinquies. Install the DEV-ENV module (only if answer 11 = yes)

Adds reproducible external-service environments: versioned per-service containers, mandatory healthcheck, lifecycle modes. Copy from `modules/dev-env/`:

```
modules/dev-env/rules/dev_environment_rule.md  →  .agents/rules/dev_environment_rule.md
modules/dev-env/skills/dev-env/                →  .claude/skills/dev-env/
```

Then: create `docker/` at the repo root (per-service subdirs added as services appear); add `docker/**/.env` to `.gitignore`; register `dev-env` (manual-only) in `.claude/skills/_index.md`. See `modules/dev-env/README.md`.

**If answer 11 = no:** skip.

## 6. Generate the per-agent entry-points (from `adapters/`)

The methodology is agent-agnostic; each agent just needs a thin stub pointing at `.agents/METHODOLOGY.md`. For each agent named in answer 5:

- **Claude Code** → `.agents/llm/claude.md` (from `adapters/claude.md`) + a root `CLAUDE.md` stub that points to the reading order (§9 of METHODOLOGY). Claude discovers `.claude/skills/` natively.
- **Gemini / Antigravity** → `.agents/llm/gemini.md` (from `adapters/gemini.md`) + a root `GEMINI.md` with a **"Skills available"** section (Gemini has no native skill discovery — it reads the catalog and loads a `SKILL.md` when the topic matches).
- **Codex / others** → `.agents/llm/codex.md` (from `adapters/codex.md`).
- **Always** → a root `AGENTS.md` (from the kit's `AGENTS.md`, de-templated) as the universal entry-point convention. This is the file a generic agent looks for.

Every entry-point stub is short: it names the reading order and points at the canonical `.agents/METHODOLOGY.md`. Never duplicate methodology content into a stub.

## 7. Post-install verification checklist

Run these before telling the human it is done:

- [ ] `grep -rn '{{' .agents {{project}}_wiki .claude CLAUDE.md GEMINI.md AGENTS.md` returns **nothing** (all placeholders substituted).
- [ ] `.agents/METHODOLOGY.md`, `.agents/rules/mandatory_planning_rule.md` exist.
- [ ] `{{project}}_wiki/_meta/{conventions,index,log}.md` and `overview.md` exist.
- [ ] `{{project}}_wiki/work/{tasks,plans,executions,archive}/` exist (with `_template.md` in tasks/plans/executions).
- [ ] `.claude/skills/_index.md` lists exactly the skills you installed (core, plus modules if chosen).
- [ ] Root entry-point(s) for each chosen agent exist and point at `.agents/METHODOLOGY.md`.
- [ ] If monorepo module installed: `.agents/rules/git_branching_rule.md` + `knowledge_source_of_truth_rule.md` exist; roster checklist done.
- [ ] If cross-team module installed: `cross-team-handoff` skill present; conventions extended.
- [ ] First `{{project}}_wiki/_meta/log.md` entry written (the install record, §1).
- [ ] `/work-index` runs clean (generates an empty-but-valid `work/_index.md`).
- [ ] `.agents/rules/git_branching_rule.md` exists (core single-repo variant, or the monorepo module's variant if installed).
- [ ] If benchmarks module installed: `.agents/rules/benchmark_protocol_rule.md`, `{{project}}_wiki/benchmarks/_template.md`, `run-benchmark` skill, conventions extended.
- [ ] If contracts module installed: `.agents/rules/contract_change_rule.md`, `{{project}}_wiki/decisions/_templates/adr-contract.md`, conventions extended.
- [ ] If dev-env module installed: `.agents/rules/dev_environment_rule.md`, `dev-env` skill, `docker/` created + `docker/**/.env` gitignored.

## 8. Hand-off to the human

Report: which modules you installed and why, the language chosen for knowledge content, the entry-points generated, and the reading order for a fresh agent (METHODOLOGY §9). Then stop — the first real task starts the normal work cycle (`work-cycle` skill), which begins with the human authoring a task.

> **Do not** begin documenting the existing codebase or writing code as part of the install. That is the first *work cycle*, gated on the human's first task and an approved plan.
