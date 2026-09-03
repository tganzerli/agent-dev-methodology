<!--
  Installs as: .agents/llm/gemini.md  (plus a root GEMINI.md with a "Skills available"
  section — see INSTALL.md §6). De-template the {{...}} placeholders at install.
  This adapter holds Gemini / Antigravity specifics ONLY; the canonical methodology is
  .agents/METHODOLOGY.md.
-->
# Gemini adapter — {{PROJECT}}

> Specifics for Gemini agents (Gemini CLI, Gemini Code Assist / Antigravity, direct API). The canonical methodology is `.agents/METHODOLOGY.md` — read it first.

## 1. Entry points per surface

| Surface | How Gemini loads this project |
|---|---|
| **Gemini CLI / Antigravity** | Reads `GEMINI.md` at the repo root automatically as initial context. |
| **Gemini Code Assist (IDE)** | Reads `GEMINI.md` when the workspace opens (enable in the assistant's settings). |
| **Direct API** | No automatic read — pass `.agents/METHODOLOGY.md` + `{{project}}_wiki/_meta/index.md` in the system prompt. |

## 2. Strengths to lean on

- **Large context window:** when ingesting a long source, pass the **whole document in one shot** — do not chunk. Gemini synthesizes better with the full text present. (This is why the `ingest-source` skill routes big docs to Gemini.)
- **Multi-modal:** if a source has diagrams/images, pass them alongside the text and note in the generated summary which image was consulted.
- **Function calling:** prefer structured tools over free-text parsing when available.

## 3. Operation mapping (Gemini CLI)

| Methodology operation | In Gemini CLI |
|---|---|
| Read a file | `@file` reference or a `<file path="...">` block |
| Edit a file | produce a unified diff and apply it (surgically — see §4) |
| Run a shell command | `!` in interactive mode |
| Search the repo | `@workspace` + query |
| Multiple reads | chain several `@` refs in one prompt to parallelize |

## 4. Cautions specific to Gemini

- **Verbosity:** Gemini tends to over-produce. Reinforce "follow the `mandatory_planning_rule.md` template strictly, nothing beyond it".
- **Non-surgical edits:** Gemini tends to rewrite whole files. Reinforce `mandatory_planning_rule.md` §3 "Punctual edits (strict)" every time you ask for a plan adjustment — edit only the named section.
- **`file:line` citations:** Gemini sometimes invents line numbers. **Always validate** citations in plans and wiki pages — open the file and check.
- **Knowledge language:** force **{{KNOWLEDGE_LANG}}** explicitly; Gemini's default drifts with the opening prompt.
- **Git flags:** Gemini sometimes swaps flags (`-D` vs `--delete`, `--force` vs `--force-with-lease`). **Paste canonical commands** rather than letting it generate them (see §6).

## 5. Skills — Native discovery (Antigravity) vs manual simulation (Gemini CLI)

- **Antigravity / Modern Gemini Agentic Environments:** Discovery of Agent Skills in `.claude/skills/` is **native**. Registering `.agents/skills.json` (`{ "entries": [ { "path": "../.claude/skills" } ] }`) or creating a symlink `.agents/skills -> ../.claude/skills` allows Gemini to discover and execute all skills automatically (same behavior as Claude Code).
- **Gemini CLI (Legacy):** Does not support native skill discovery. The agent reads `.claude/skills/_index.md` or the "Skills available" section in root `GEMINI.md` and loads the matching `SKILL.md` manually when the topic applies:
  1. The catalog lives at `.claude/skills/_index.md` (same path as Claude — convention, not exclusivity).
  2. The root `GEMINI.md` carries a **"Skills available"** section (name · description · trigger) generated from that catalog.
  3. On entering a conversation, **scan that section** and load the matching `SKILL.md` when the topic applies. E.g. the human asks `/wiki-sync` → load `.claude/skills/wiki-sync/SKILL.md`.
  4. **Lazy-load references:** only read a skill's `references/*.md` when its specific subject comes up.
  5. **Do not invent skills.** Use only those listed.
  6. **`disable-model-invocation: true`** skills run **only** on explicit human request (side effects + human gate). **`user-invocable: false`** skills are background knowledge — load silently when relevant, never announce them as commands.

## 6. Git workflow

> A git branching rule ships in **core** (`.agents/rules/git_branching_rule.md`, `trigger: always_on`: single-repo `main`/`dev` + plan-gated `<type>/<work_id>__<scope>` ephemerals). The **monorepo module** replaces it at the same path with the multi-app topology. The branch-creation gate below applies whenever that rule is installed (it is, by default); only a project that deliberately removed the core branching rule skips it.

- **Git via shell-out** (`!` in Gemini CLI). **Announce the command first** and wait for approval. Do not run multiple destructive ops in sequence without an intermediate confirmation.
- **Before creating a branch** (per the branching rule), validate the rule's sequence: (1) `{{project}}_wiki/work/plans/{work_id}.md` exists? (2) `status: approved`? (3) name `<type>/<work_id>__<scope>` valid? If any fails: **stop and require the gate** — do not invent a name.
- **Never `git commit` on protected permanent branches** (e.g. `main`, `staging_*`) — PRs only.
- **`push --force` forbidden without `--with-lease`** on any branch.
- **Host-UI actions** the CLI cannot do (branch protection, PR templates, merge checks): **guide the human** through the panel; do not work around via API.
- **Prefer canonical commands:** copy git commands from the branching rule rather than letting Gemini generate them (see §4).

### ⚠ No LLM co-authorship on commits (non-negotiable)

**Forbidden** to include `Co-Authored-By: Gemini <…>` — or any trailer/footer identifying the assistant (any Gemini/Google model or product name) — in commits produced via Gemini. Applies to ordinary commits, merge commits, amendments, any trailer/footer, and PR descriptions. The author is the human; the local `git user` already records authorship. If you generate a co-authored message by mistake, fix it before committing; if already committed, do not rebase without human approval. (An equivalent rule holds for every other agent's adapter.)

## 7. Limits

- **No persistent memory** equivalent to Claude Code's. Everything Gemini "knows" about this project must live **in the repo**: `.agents/METHODOLOGY.md`, the wiki, the rules. This is why the project versions **every** methodological decision instead of trusting agent memory.
