# AGENTS.md — {{PROJECT}}

> Universal entry-point for **any** LLM agent operating in this repository. This file is intentionally thin: it points at the canonical methodology and tells you what to read, in order. It never duplicates methodology content.
>
> Agent-specific conventions (tools, model hints, quirks) live in `.agents/llm/<agent>.md`.

## You are an agent working in this repo

**Read always, in order:**

1. **`.agents/METHODOLOGY.md`** — the canonical, LLM-agnostic methodology. Everything flows from here.
2. **`.agents/rules/mandatory_planning_rule.md`** — no code before an approved plan (`trigger: always_on`).
3. **`.agents/rules/git_branching_rule.md`** — the core single-repo branching rule. *(monorepo projects)* the same path holds the monorepo variant, which also adds **`.agents/rules/knowledge_source_of_truth_rule.md`**.
3b. **Any installed optional-module rule** — `benchmark_protocol_rule.md`, `contract_change_rule.md`, `dev_environment_rule.md` are `trigger: always_on` when their module is installed. Read whichever are present in `.agents/rules/`.
4. **`.agents/llm/<your-name>.md`** — your agent-specific adapter, if present.
5. **`{{project}}_wiki/overview.md`** — the product map.

**Consult on demand — catalogs and references, not prerequisites:**

- **`{{project}}_wiki/work/_index.md`** — work in flight. For *past* work, **search** (`/work-find <term>`) instead of reading the catalog end to end.
- **`{{project}}_wiki/_meta/index.md`** — the knowledge catalog.
- **`{{project}}_wiki/_meta/conventions.md`** — only if you will write to the wiki.
- **`.claude/skills/_index.md`** — Claude Code discovers skills natively; the index explains the set, it is not a prerequisite.
- **`.agents/mcp.md`** — the MCP server catalog, if the project has one. Read it before adding, removing, or debugging an MCP server.

> Catalogs grow monotonically; the work does not. Reading them at session open turns a growing artifact into a fixed per-session cost that competes with the actual task. Everything that is a **gate** is in the first list. See METHODOLOGY §6.6.

## Non-negotiables

- **Plan-then-execute.** No code change before a plan in `{{project}}_wiki/work/plans/{ID}.md` is `status: approved`.
- **Human gate at every transition.** Plan approval, execution review, and `/wiki-sync` each require the human.
- **`file:line` citations** for every technical claim in plans and wiki. Unanchored → `⚠ unverified`.
- **Scope attribution** on every plan/execution/wiki page.
- **Knowledge language:** author plans and wiki content in **{{KNOWLEDGE_LANG}}**. Code and identifiers in English.

## Agent Skills

This project follows the [Agent Skills spec](https://agentskills.io/specification). Skills live in `.claude/skills/`.
- **Native discovery** (Claude Code, Antigravity/Gemini via `.agents/skills.json` or `.agents/skills/`, and other spec-compliant agents): skills are found automatically.
- **Legacy discovery** (e.g. Gemini CLI without native support): read `.claude/skills/_index.md` and load the matching `SKILL.md` when the topic applies. Do not invent skills; use only the listed ones.

Manual-only skills (`disable-model-invocation: true`) run **only** on explicit human request (e.g. `/wiki-sync`, `/wiki-lint`, `/commit`) — they have side effects and depend on a human gate.
