<!--
  Installs as: .agents/llm/<agent>.md for ANY agent without a dedicated adapter
  (Cursor, Cline, Aider, Windsurf, a bespoke harness, …). De-template the {{...}}
  placeholders at install and rename the file to the agent. This is the FALLBACK
  adapter: it assumes nothing about native capabilities. The canonical methodology
  is .agents/METHODOLOGY.md.
-->
# Generic agent adapter — {{PROJECT}}

> Fallback layer for any agent without a dedicated adapter in `.agents/llm/`. Assume **no** special capabilities (no native skill discovery, no persistent memory, no bespoke tools). The canonical methodology is `.agents/METHODOLOGY.md` — read it first.

## 1. Entry point & reading order

Whatever your surface, load context in this order (this mirrors `AGENTS.md`, the universal entry-point most agents look for):

1. `AGENTS.md` (repo root) — the universal entry-point convention.
2. `.agents/METHODOLOGY.md` — the canonical, LLM-agnostic methodology. Everything flows from here.
3. `.agents/rules/mandatory_planning_rule.md` — no code before an approved plan (`trigger: always_on`).
4. *(monorepo projects only)* `.agents/rules/git_branching_rule.md` and `.agents/rules/knowledge_source_of_truth_rule.md`.
5. `.claude/skills/_index.md` — the skills catalog (§3).
6. `{{project}}_wiki/_meta/conventions.md` — before writing to the wiki.
7. `{{project}}_wiki/_meta/index.md` (knowledge) and `{{project}}_wiki/work/_index.md` (work).
8. `{{project}}_wiki/overview.md` — the product map.

If your surface has no automatic file loading, the human must paste `.agents/METHODOLOGY.md` + `{{project}}_wiki/_meta/index.md` into your context.

## 2. Non-negotiables (same for every agent)

- **Plan-then-execute.** No code change before `{{project}}_wiki/work/plans/{ID}.md` is `status: approved`. Name the gate to the human before advancing — you honor gates by instruction, not by lock.
- **Human gate at every transition** (plan approval, execution review, `/wiki-sync`).
- **`file:line` citations** for every technical claim in plans and wiki. Unanchored → `⚠ unverified`. If a sub-process produced a citation you did not verify, **check it before writing it**.
- **Scope attribution** on every plan/execution/wiki page.
- **Knowledge language:** author plans and wiki content in **{{KNOWLEDGE_LANG}}**; code and identifiers in English.
- **Surgical edits:** modify only what the human asked; do not rewrite whole files (`mandatory_planning_rule.md` §3). Prefer editing existing files over creating new ones.

## 3. Skills — read the catalog, no native discovery assumed

Do not assume your agent auto-discovers `.claude/skills/`. Consume it manually:

1. Read `.claude/skills/_index.md` — the catalog of available skills.
2. When a task matches a skill's description/trigger, open and follow that `SKILL.md`.
3. **Lazy-load** a skill's `references/*.md` only when its specific subject arises.
4. **`disable-model-invocation: true`** skills (e.g. `/wiki-sync`, `/wiki-lint`, `/commit`, `/cross-team-handoff`) run **only** on explicit human request — they have side effects and depend on a human gate. **`user-invocable: false`** skills are background knowledge — load silently when relevant.
5. **Do not invent skills.** Use only those listed; suggest a new one if a recurring case lacks coverage.

## 4. No persistent memory — the repo is the memory

Assume nothing you "learn" survives the session. Everything durable about this project lives **in the repo**: `.agents/METHODOLOGY.md`, the wiki, the rules. This is why the project versions every methodological decision. Do not rely on agent memory; write durable knowledge to the wiki via the normal cycle.

## 5. Git workflow

> Applies **fully** only if the **monorepo module** is installed (ships `.agents/rules/git_branching_rule.md`, `trigger: always_on`). In a single-repo project, follow the normal branch/PR flow and skip the branch-naming sequence.

- **Announce every git command** before running it; the human may interrupt. Do not batch destructive ops (`push --force`, `branch -D`, `push --delete` on a permanent branch, renames) without an intermediate `[y/n]`.
- **Before creating a branch** (monorepo module): (1) `{{project}}_wiki/work/plans/{work_id}.md` exists? (2) `status: approved`? (3) name `<type>/<work_id>__<scope>` valid? If any fails, **stop and require the gate** — do not invent a name.
- **Never `git commit` on protected permanent branches** (e.g. `main`, `staging_*`) — PRs only. **`push --force` only with `--with-lease`.**
- **Host-UI actions** the CLI cannot do (branch protection, PR templates, merge checks): **guide the human** through the panel; do not work around via API.

### ⚠ No LLM co-authorship on commits (non-negotiable)

**Forbidden** to include a `Co-Authored-By:` trailer — or any footer/trailer identifying the assistant (its model or product name) — in commits produced via this agent. Applies to ordinary commits, merge commits, amendments, any trailer/footer, and PR descriptions. The author is the human; the local `git user` already records authorship. Fix a co-authored message before committing; if already committed, do not rebase without human approval.
