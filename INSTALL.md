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

## 8. Hand-off to the human

Report: which modules you installed and why, the language chosen for knowledge content, the entry-points generated, and the reading order for a fresh agent (METHODOLOGY §9). Then stop — the first real task starts the normal work cycle (`work-cycle` skill), which begins with the human authoring a task.

> **Do not** begin documenting the existing codebase or writing code as part of the install. That is the first *work cycle*, gated on the human's first task and an approved plan.
