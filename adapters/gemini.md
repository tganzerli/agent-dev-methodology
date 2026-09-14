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

## 3. Operation mapping

The methodology defines operations that map to Gemini's surfaces:

| Methodology operation | In Antigravity / Agentic | In Gemini CLI (interactive) |
|---|---|---|
| Read a file | `view_file` (with start/end line bounds for exact checking) | `@file` reference or `<file path="...">` block |
| Edit a file | `replace_file_content` (surgical edits — see §4) | produce a unified diff and apply it |
| Create a file | `write_to_file` | code block for creation |
| Run a shell command | `run_command` (announce before running) | `!` in interactive mode |
| Search the repo | `grep_search`, `find_by_name`, `list_dir` | `@workspace` + query |
| Sub-agents / delegation | `invoke_subagent` (with tiers `pro`, `flash`, `flash_lite`) | parallel prompt dispatch |
| MCP tools | `call_mcp_tool` | configured in `.gemini/settings.json` |

> 🔒 **Surgical edits:** In agentic environments, prefer targeted editing tools (`replace_file_content` / targeted search-and-replace). Never rewrite an entire file to change a few lines (violates `mandatory_planning_rule.md` §3).

## 3.1. Subagents and model tiers

Just as Claude Code isolates context through role subagents in `.claude/agents/`, Gemini environments that support subagents (such as Antigravity) should dispatch subagents to buy reasoning capacity or parallelism **without invalidating the main session's context**:

| Phase | Methodology role | Gemini tier | Purpose |
|---|---|---|---|
| §4.2 Task | `task-author` | `pro` | Frame/refine the task upon human request |
| §4.2.5 Pre-plan analyses | `analyst` (N in parallel) | `flash` or `pro` | One discrete investigative question with verifiable `file:line` |
| §4.2.5 Broad sweep | `mechanic` | `flash` or `flash_lite` | Mechanical sweeps and broad repo searches |
| §4.3 Plan | `planner` | `pro` | Deep architectural reasoning and plan drafting |
| **§4.4 Execution** | — | **main thread** | Interactive execution with live log and human gates |
| §4.4 Heavy or mechanical step | `planner` / `mechanic` | `pro` / `flash_lite` | Delegating discrete isolated steps |
| §4.5 Wiki sync | `scribe` | `flash` or `pro` | Surgical drafting of knowledge pages |

**Tiers, never version names.** Tier `pro` corresponds to top-tier reasoning (Opus/advanced Sonnet); tier `flash` to balanced reasoning (Sonnet/fast); tier `flash_lite` to mechanical tasks (Haiku).

## 4. Cautions specific to Gemini

- **Verbosity:** Gemini tends to over-produce. Reinforce "follow the `mandatory_planning_rule.md` template strictly, nothing beyond it".
- **Non-surgical edits:** Gemini tends to rewrite whole files. Reinforce `mandatory_planning_rule.md` §3 "Punctual edits (strict)" using `replace_file_content` for bounded blocks.
- **`file:line` citations (Strict verification):** Gemini sometimes invents line numbers. **Always validate citations** in plans and wiki pages — open the file via `view_file` or `grep_search` and verify the exact line numbers before citing. Unanchored or guessed citations generate `⚠ unverified` and break `wiki-lint`.
- **Knowledge language:** force **{{KNOWLEDGE_LANG}}** explicitly; Gemini's default drifts with the opening prompt.
- **Git flags:** Gemini sometimes swaps flags (`-D` vs `--delete`, `--force` vs `--force-with-lease`). **Paste canonical commands** rather than letting it generate them (see §6).

## 5. Skills and Slash Commands

Gemini integrates with project skills through two complementary paths:

- **Slash Commands via `.gemini/commands/` (Gemini CLI):**
  For the Gemini CLI, each operational skill in `.claude/skills/` is exposed as a native `/command` through a `.toml` file in `.gemini/commands/` (e.g. `.gemini/commands/wiki-sync.toml`). Each command is a thin wrapper that directs the agent to read `@.claude/skills/<skill>/SKILL.md`. This delivers 100% command parity with Claude Code without duplicating skill logic.
- **Native Discovery (Antigravity) & Manual Simulation:**
  - In Antigravity / modern Gemini agentic harnesses, skills in `.claude/skills/` can be registered natively via `.agents/skills.json` (`{ "entries": [ { "path": "../.claude/skills" } ] }`) or symlinked.
  - When invoking manually: the root `GEMINI.md` carries a **"Skills available"** section (name · path · trigger). Scan that section on entering a conversation and load the corresponding `SKILL.md` when the topic matches.
- **Lazy-load references:** only read a skill's `references/*.md` when its specific subject comes up.
- **Do not invent skills.** Use only those listed in `.claude/skills/_index.md`.
- **`disable-model-invocation: true`** skills run **only** on explicit human request (side effects + human gate). **`user-invocable: false`** skills are background knowledge — load silently when relevant, never announce them as commands.

## 6. Git workflow

> A git branching rule ships in **core** (`.agents/rules/git_branching_rule.md`, `trigger: always_on`: single-repo `main`/`dev` + plan-gated `<type>/<work_id>__<scope>` ephemerals). The **monorepo module** replaces it at the same path with the multi-app topology. The branch-creation gate below applies whenever that rule is installed (it is, by default); only a project that deliberately removed the core branching rule skips it.

- **Git via shell-out** (`!` in Gemini CLI). **Announce the command first** and wait for approval. Do not run multiple destructive ops in sequence without an intermediate confirmation.
- **Before creating a branch** (per the branching rule), validate the rule's sequence: (1) `{{project}}_wiki/work/plans/{work_id}.md` exists? (2) `status: approved`? (3) name `<type>/<work_id>__<scope>` valid? If any fails: **stop and require the gate** — do not invent a name.
- **Never `git commit` on protected permanent branches** (e.g. `main`, `staging_*`) — PRs only.
- **`push --force` forbidden without `--with-lease`** on any branch.
- **Host configuration** (branch protection, rulesets, required checks, merge settings, a bot's bypass): **never on your own initiative** — guide the human through the panel. With **explicit, per-task authorisation** you may use the API, and the branching rule's §9.1 obligations then apply: scoped, **recorded** from-what-to-what, and **read back** instead of trusting the write's exit code.
- **Prefer canonical commands:** copy git commands from the branching rule rather than letting Gemini generate them (see §4).

### ⚠ No LLM co-authorship on commits (non-negotiable)

**Forbidden** to include `Co-Authored-By: Gemini <…>` — or any trailer/footer identifying the assistant (any Gemini/Google model or product name) — in commits produced via Gemini. Applies to ordinary commits, merge commits, amendments, any trailer/footer, and PR descriptions. The author is the human; the local `git user` already records authorship. If you generate a co-authored message by mistake, fix it before committing; if already committed, do not rebase without human approval. (An equivalent rule holds for every other agent's adapter.)

## 7. Limits

- **No persistent memory** equivalent to Claude Code's. Everything Gemini "knows" about this project must live **in the repo**: `.agents/METHODOLOGY.md`, the wiki, the rules. This is why the project versions **every** methodological decision instead of trusting agent memory.
