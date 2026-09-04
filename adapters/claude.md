<!--
  Installs as: .agents/llm/claude.md  (plus a thin root CLAUDE.md stub — see INSTALL.md §6).
  De-template the {{...}} placeholders at install. This adapter holds Claude-family
  specifics ONLY; the canonical, LLM-agnostic methodology is .agents/METHODOLOGY.md.
-->
# Claude adapter — {{PROJECT}}

> Specifics for the Claude family (Claude Code, Claude Desktop, direct API). The canonical methodology is `.agents/METHODOLOGY.md` — read it first. This file never duplicates methodology content; it only maps it to Claude's tools and quirks.

## 1. Native tools to prefer

When running as Claude Code:

- **TodoWrite / task tracking** for executions with more than ~4 steps. Each step of `{{project}}_wiki/work/plans/{ID}.md` §4.5 becomes a tracked item.
- **Read** to open files (never `cat`/`head`/`tail`).
- **Edit** for surgical changes (preferred over `Write` on existing files — see `mandatory_planning_rule.md` §3 "punctual edits").
- **Write** only for new files or a full rewrite.
- **Bash** for git, find, grep, and the project's build/test CLI.
- **Agent (Explore / read-only search)** for broad read-only sweeps (>3 queries) where you only need the conclusion, not the file dumps.
- **Agent (Plan)** when the human asks for a new plan of medium/high complexity.

## 2. Parallel calls

Whenever tool calls are independent (multiple `Read`s, independent `Bash`es), emit them **in the same response** to parallelize. Only serialize when a later call depends on an earlier result.

## 3. Models — never switch mid-session

**The prompt cache is keyed by the model.** Running `/model` in the middle of a session discards the cached prefix: the next request re-reads the entire history with no cache hit, at full input price and full latency. The same applies to changing the effort level, and to `opusplan` — which resolves to different models in plan vs. execution mode, so **every plan-mode toggle is a model switch that starts a fresh cache**. Convenient, and it keeps the whole cost.

Choose the model **at the top of the session** and leave it there. When you need more capability mid-task, **dispatch a sub-agent** — it has its own context and its own cache, so the main thread's prefix is never reprocessed. That is the only way to buy capability without paying the switch.

### 3.1. Roles live in `.claude/agents/`

One file per role, each declaring `model:` in its frontmatter. The kit ships templates in `core/agents/` (see `INSTALL.md`). Set, mapped to METHODOLOGY §4.2:

| Phase | Role | Runs in |
|---|---|---|
| §4.2 Task | `task-author` | sub-agent |
| §4.2.5 Analyses | `analyst` (N in parallel) | sub-agent |
| §4.2.5 Broad sweep | `mechanic` | sub-agent |
| §4.3 Plan | `planner` | sub-agent |
| **§4.4 Execution** | — | **main thread** |
| §4.4 Heavy or mechanical step | `planner` / `mechanic` | sub-agent |
| §4.5 Wiki sync | `scribe` | sub-agent |

**The execution is not delegated wholesale.** Its log is live and its gates need human confirmation in the moment — an isolated sub-agent does neither. What you delegate are discrete steps, in both directions: *up* for a step harder than the average, *down* for a mechanical one.

**Pin tiers, never version names.** A tier alias resolves to the current generation, so the file does not rot when a new model ships — and it does not become the fixed role→model table that METHODOLOGY §4.2 warns against. The role's tier is a floor: the main thread can override it per invocation when the specific work calls for it.

> Any concrete line-up written down **ages**. As a rough heuristic *at time of writing*: a top-tier reasoning tier for planning and task framing, a balanced tier for analysis and wiki drafting, a small/fast tier for mechanical sweeps.

## 4. Skills — native discovery

Claude Code discovers `.claude/skills/` **natively**; the catalog is readable at `.claude/skills/_index.md`. Skills do not replace METHODOLOGY or rules — they offload on-demand material.

- **Auto skills** load when their `description`/`paths` match.
- **Manual-only skills** (`disable-model-invocation: true`, e.g. `/wiki-sync`, `/wiki-lint`, `/commit`, and — if the cross-team module is installed — `/cross-team-handoff`) run **only** on explicit human request; they have side effects and depend on a human gate.

**Recipe belongs in a skill; the gate stays in the rule.** The body of a skill genuinely does not enter context until invoked — that is the one real lazy-loading lever Claude Code gives you. So when an `always_on` rule carries a long runbook, move the runbook to a skill and keep every obligation in the rule, each with enough context to stand without the recipe around it. Do **not** carry the gate markers into the skill: a marker there implies the obligation lives in a file that may never be invoked.

**When to create a skill vs. edit METHODOLOGY:** a repeatable operational workflow → skill; a large domain body relevant only to part of the repo → skill with `paths`/`user-invocable: false`; an always-true methodological principle → METHODOLOGY or a rule. Update `.claude/skills/_index.md` whenever you add/remove a skill. Do not duplicate wiki content into a `SKILL.md` — skills **point** at the wiki.

## 5. Gates and cautions

- Claude Code honors the methodology's gates **by instruction, not by lock** — unless you give it one. **Name the gate** to the human ("is the plan approved?") before advancing.
- **Optional: make the plan gate a real lock.** A `PreToolUse` hook on `Edit`/`Write`, scoped to the code directories, can read the current work's plan and refuse the edit unless it is `status: approved`. This mechanizes a rule that already exists rather than inventing one, and it means the gate stops depending on the agent remembering. Keep the scope tight (never block the wiki or the trio), resolve the work id from the ephemeral branch name with a local marker file as fallback, and document an escape hatch. Note the hook cannot change the model — hooks gate tools, not model selection.
- Speed never justifies skipping a gate or a cycle step.
- When an `Agent` sub-agent generates wiki content, **validate every `file:line` citation on the main thread** before writing — the sub-agent does not share your context.

## 6. Persistent memory

Claude Code keeps a user-scoped memory (`.claude/projects/.../memory/`). Use it for **user preferences** (plan/wiki style) and **evolving methodological decisions**. Do **not** put wiki-owned content in memory — the wiki is versioned in the repo; memory is outside it.

## 7. Git workflow

> A git branching rule ships in **core** (`.agents/rules/git_branching_rule.md`, `trigger: always_on`: single-repo `main`/`dev` + plan-gated `<type>/<work_id>__<scope>` ephemerals). The **monorepo module** replaces it at the same path with the multi-app topology. The branch-creation gate below applies whenever that rule is installed (it is, by default); only a project that deliberately removed the core branching rule skips it.

- **Git via `Bash`** only. Do not invent non-standard flags.
- **Before creating a branch** (per the branching rule), validate the rule's sequence: (1) does `{{project}}_wiki/work/plans/{work_id}.md` exist? (2) is it `status: approved`? (3) does the name `<type>/<work_id>__<scope>` match the syntax? If any fails: **stop and require the gate** — never invent a branch name.
- **Announce every git command** before running it; the human may interrupt.
- **Destructive ops need in-the-moment human confirmation** (`[y/n]`): `push --force` (even `--with-lease`) on a permanent branch; `branch -D`; `push --delete` on any permanent branch; renaming a permanent branch. Do not batch multiple destructive ops without an intermediate confirmation.
- **Never `git commit` on protected permanent branches** (e.g. `main`, `staging_*`) — those receive PRs only.
- **Host-UI actions** (branch protection, PR templates, merge checks) that the `git` CLI cannot do: **guide the human** through the panel steps; do not work around them via API.

### ⚠ No LLM co-authorship on commits (non-negotiable)

**Forbidden** to include `Co-Authored-By: Claude <…>` — or any trailer/footer identifying the assistant (any Claude/Anthropic model or product name, "Claude Code", context-window tags, etc.) — in commits produced via Claude Code.

Applies to: ordinary commits, merge commits (including conflict resolution), amendments, any trailer/footer (`git -c trailer.*` or heredoc), and PR descriptions created via CLI or suggested for a host UI.

**Why:** the author is the human. Commits made via Claude already carry the configured local `git user`; duplicating that via co-authorship is noise. If you generate a co-authored message by mistake, **fix it before committing**; if it is already committed, do **not** rebase to rewrite history without human approval — just avoid it next time. (An equivalent rule holds for every other agent's adapter.)
