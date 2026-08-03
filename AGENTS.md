# AGENTS.md — {{PROJECT}}

> Universal entry-point for **any** LLM agent operating in this repository. This file is intentionally thin: it points at the canonical methodology and tells you what to read, in order. It never duplicates methodology content.
>
> Agent-specific conventions (tools, model hints, quirks) live in `.agents/llm/<agent>.md`.

## You are an agent working in this repo. Read, in order:

1. **`.agents/METHODOLOGY.md`** — the canonical, LLM-agnostic methodology. Everything flows from here.
2. **`.agents/rules/mandatory_planning_rule.md`** — no code before an approved plan (`trigger: always_on`).
3. *(monorepo projects only)* **`.agents/rules/git_branching_rule.md`** and **`.agents/rules/knowledge_source_of_truth_rule.md`**.
4. **`.claude/skills/_index.md`** — the catalog of Agent Skills available here.
5. **`{{project}}_wiki/_meta/conventions.md`** — if you will write to the wiki.
6. **`{{project}}_wiki/_meta/index.md`** — the knowledge catalog.
7. **`{{project}}_wiki/work/_index.md`** — the work catalog (tasks/plans/executions).
8. **`{{project}}_wiki/overview.md`** — the product map.
9. **`.agents/llm/<your-name>.md`** — your agent-specific adapter, if present.

## Non-negotiables

- **Plan-then-execute.** No code change before a plan in `{{project}}_wiki/work/plans/{ID}.md` is `status: approved`.
- **Human gate at every transition.** Plan approval, execution review, and `/wiki-sync` each require the human.
- **`file:line` citations** for every technical claim in plans and wiki. Unanchored → `⚠ unverified`.
- **Scope attribution** on every plan/execution/wiki page.
- **Knowledge language:** author plans and wiki content in **{{KNOWLEDGE_LANG}}**. Code and identifiers in English.

## Agent Skills

This project follows the [Agent Skills spec](https://agentskills.io/specification). Skills live in `.claude/skills/`.
- **Native discovery** (Claude Code, and other spec-compliant agents): skills are found automatically.
- **No native discovery** (e.g. Gemini CLI/Antigravity): read `.claude/skills/_index.md` and load the matching `SKILL.md` when the topic applies. Do not invent skills; use only the listed ones.

Manual-only skills (`disable-model-invocation: true`) run **only** on explicit human request (e.g. `/wiki-sync`, `/wiki-lint`, `/commit`) — they have side effects and depend on a human gate.
