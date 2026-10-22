<!--
  Installs as: .agents/llm/gemini.md  (plus a root GEMINI.md with a "Skills available"
  section — see INSTALL.md §6). De-template the double-brace placeholders at install.
  This adapter holds Gemini CLI / Antigravity CLI specifics ONLY; the canonical
  methodology is .agents/METHODOLOGY.md.
-->
# Gemini / Antigravity adapter — {{PROJECT}}

> Specifics for the two Google agent CLIs — **Gemini CLI** (`gemini`) and **Antigravity CLI** (`agy`) — plus Gemini Code Assist and the direct API. The canonical methodology is `.agents/METHODOLOGY.md` — read it first.
>
> **Two CLIs, two loaders.** They share the model family and `GEMINI.md`, and differ on almost everything else. Facts about `agy` below come from its built-in `agy-customizations` guide (agy 1.4.5) and a live probe on 2026-10-22; re-verify after a major `agy` upgrade.

## 1. What each surface loads

| Project file | Gemini CLI | Antigravity CLI (`agy`) |
|---|---|---|
| `GEMINI.md` (root) | ✅ initial context | ✅ rule, always loaded |
| `AGENTS.md` (root) | only if configured as a context file | ✅ rule, always loaded |
| `.agents/rules/*.md` (`trigger:` frontmatter) | ❌ (reached through the entry-point's reading order) | ✅ `always_on` loaded unconditionally; `model_decision` loaded progressively |
| `.agents/skills/<name>/SKILL.md` | ❌ (reads `.claude/skills/_index.md` by hand) | ✅ progressive disclosure — name + description only until activated |
| `.gemini/commands/*.toml` | ✅ native `/commands` | ❌ not used |
| `.agents/workflows/` | ❌ | ❌ not used |
| Hooks | `.gemini/settings.json` | `.agents/hooks.json` (§5.1) |
| MCP servers | `.gemini/settings.json` (project) | user-level only (§5.2) |

**Gemini Code Assist (IDE)** reads `GEMINI.md` when the workspace opens (enable it in the assistant's settings). **Direct API:** no automatic read — pass `.agents/METHODOLOGY.md` + `{{project}}_wiki/_meta/index.md` in the system prompt.

### 1.1. The `agy` rule budget — keep the always-on prefix lean

`agy` discovers workspace rules by walking from the CWD up to the repo root, and **user and workspace rules share one 20,000-token budget**; a rule that does not fit is **cut on a newline boundary** — silently, mid-rule. Everything `always_on` in `.agents/rules/` plus `GEMINI.md` and `AGENTS.md` is in that budget. This is METHODOLOGY §6.6 with a hard ceiling: keep the gate in the rule and the recipe in a skill, keep the entry-points thin, and measure the always-on set (`wc -w` × ~1.3 is a fair token estimate) whenever a rule grows. A rule cut in half still looks loaded.

## 2. Strengths to lean on

- **Large context window:** when ingesting a long source, pass the **whole document in one shot** — do not chunk. Gemini synthesizes better with the full text present. (This is why the `ingest-source` skill routes big docs to Gemini.)
- **Multi-modal:** if a source has diagrams/images, pass them alongside the text and note in the generated summary which image was consulted.
- **Function calling:** prefer structured tools over free-text parsing when available.

## 3. Operation mapping

| Methodology operation | Antigravity CLI (`agy`) | Gemini CLI (interactive) |
|---|---|---|
| Read a file | `read_file {Path}` | `@file` reference |
| Edit a file | `edit_file {Path, Target, Replacement}` (surgical — see §4) | the edit tool, or a unified diff |
| Create a file | `write_file {Path, Content}` | the write tool |
| Run a shell command | the shell tool (announce before running) | `!` in interactive mode |
| Sub-agents / delegation | subagents (tiers below) | parallel prompt dispatch |
| MCP tools | user-level servers (§5.2) | `.gemini/settings.json` |

The `agy` file-tool names and argument keys are the ones observed in the probe; other Antigravity surfaces (the IDE) expose different names — check the surface before writing a hook matcher against them.

> 🔒 **Surgical edits:** prefer the targeted edit tool (`edit_file` / search-and-replace). Never rewrite an entire file to change a few lines (violates `mandatory_planning_rule.md` §3).

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
| §4.4.1 Agent review | `reviewer` | `flash` (`pro` for tier `high`) | Clean-context review of the diff — never on the main thread |
| §4.5 Wiki sync | `scribe` | `flash` or `pro` | Surgical drafting of knowledge pages |

**Tiers, never version names.** Tier `pro` corresponds to top-tier reasoning (Opus/advanced Sonnet); tier `flash` to balanced reasoning (Sonnet/fast); tier `flash_lite` to mechanical tasks (Haiku).

## 4. Cautions specific to Gemini

- **Verbosity:** Gemini tends to over-produce. Reinforce "follow the `mandatory_planning_rule.md` template strictly, nothing beyond it".
- **Non-surgical edits:** Gemini tends to rewrite whole files. Reinforce `mandatory_planning_rule.md` §3 "Punctual edits (strict)" using the targeted edit tool for bounded blocks.
- **`file:line` citations (Strict verification):** Gemini sometimes invents line numbers. **Always validate citations** in plans and wiki pages — open the file (or grep it) and verify the exact line numbers before citing. Unanchored or guessed citations generate `⚠ unverified` and break `wiki-lint`.
- **Knowledge language:** force **{{KNOWLEDGE_LANG}}** explicitly; Gemini's default drifts with the opening prompt.
- **Git flags:** Gemini sometimes swaps flags (`-D` vs `--delete`, `--force` vs `--force-with-lease`). **Paste canonical commands** rather than letting it generate them (see §6).

## 5. Skills and slash commands

- **Antigravity CLI — native discovery through the skills link.** `agy` finds workspace skills at `.agents/skills/<name>/SKILL.md`, so the install creates the **required** symlink `.agents/skills -> ../.claude/skills`. `.agents/skills.json` is a fallback only (relative-path entries have been reported unreliable; a directory entry loads only its direct children) — see the kit's `INSTALL.md` §6. **Quote every `description:`** in a `SKILL.md` frontmatter: an unquoted description containing a colon has failed to load.
- **Gemini CLI — slash commands.** Each operational skill is exposed as a native `/command` through a `.toml` in `.gemini/commands/` (e.g. `.gemini/commands/wiki-sync.toml`), a thin wrapper that directs the agent to read `@.claude/skills/<skill>/SKILL.md`. `agy` ignores these files.
- **Manual fallback:** the root `GEMINI.md` carries a **"Skills available"** section (name · path · trigger). Scan it on entering a conversation and load the matching `SKILL.md` when the topic hits.
- **Lazy-load references:** only read a skill's `references/*.md` when its specific subject comes up.
- **Do not invent skills.** Use only those listed in `.claude/skills/_index.md`.
- **`disable-model-invocation: true`** skills run **only** on explicit human request (side effects + human gate). **`user-invocable: false`** skills are background knowledge — load silently when relevant, never announce them as commands.

### 5.1. Hooks — the plan gate as a lock

**Antigravity CLI** reads `.agents/hooks.json`: an object of **named** hooks, each holding event → matcher groups.

```json
{"plan-gate": {"PreToolUse": [{"matcher": "write_file|edit_file",
  "hooks": [{"type": "command", "command": "../.claude/hooks/require-approved-plan.sh", "timeout": 10}]}]}}
```

- A Claude-Code-style top-level `"hooks"` key is **wrong** — it loads as one hook *named* `hooks`.
- The command runs via `sh -c` with **CWD = the directory holding `hooks.json`** (`.agents/`), hence the `../` path.
- Input on stdin, camelCase JSON: `{"toolCall": {"name": "write_file", "args": {"Path": "/abs/path", "Content": "…"}}, "workspacePaths": ["/abs/workspace"], "conversationId": …}`.
- Output on stdout, JSON: `{"decision": "deny" | "ask" | "force_ask" | "allow", "reason": "…"}`. `deny` hard-blocks and the reason reaches the agent (`tool call denied by pre-tool hook: <reason>`). **Empty stdout = no opinion** — the tool proceeds through the normal permission flow.
- 🔒 **A gate never prints `"allow"`**: that auto-approves the call and skips the human's permission prompt. Allow by printing nothing.

The kit's `require-approved-plan.sh` speaks this protocol when the payload carries `toolCall` (and Claude Code's otherwise); the kit ships the file above as `core/hooks/agy-hooks.json`.

- 🔒 **Known limit:** the gate keys on the branch name / marker file (`.claude/` or `.gemini/active_work.json`). Never create or switch a branch, or write the marker, to get past a `deny` — stop and ask the human. The branch-scope barrier and human review are the real enforcement.

**Gemini CLI** configures hooks in `.gemini/settings.json` — Gemini CLI only; `agy` does not read it. The kit's gate script has not been verified against Gemini CLI's hook protocol (`⚠ unverified`).

### 5.2. MCP servers

`agy` has **no workspace-level MCP config**. Servers live in the user-level `~/.gemini/config/mcp_config.json` (manage them with `agy mcp add|list|remove`) or inside plugins — so a project's MCP intent reaches `agy` only through `.agents/mcp.md`, mirrored by hand on each machine. Gemini CLI keeps the project-level `.gemini/settings.json` (`mcpServers` key).

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

**Mechanism:** `.githooks/commit-msg` (early feedback) plus `scripts/ci/check_commit_trailers.py` in CI on every PR and every push to the default branch (the guarantee) — see the kit's `INSTALL.md` §6.

## 7. Limits

- **No persistent memory** equivalent to Claude Code's. Everything Gemini "knows" about this project must live **in the repo**: `.agents/METHODOLOGY.md`, the wiki, the rules. This is why the project versions **every** methodological decision instead of trusting agent memory.
