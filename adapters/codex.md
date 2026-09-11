<!--
  Installs as: .agents/llm/codex.md  (Codex reads the root AGENTS.md natively — see
  INSTALL.md §6). De-template the {{...}} placeholders at install. This adapter holds
  Codex specifics ONLY; the canonical methodology is .agents/METHODOLOGY.md.
-->
# Codex adapter — {{PROJECT}}

> Specifics for OpenAI Codex agents (Codex CLI and IDE surfaces). The canonical methodology is `.agents/METHODOLOGY.md` — read it first.

## 1. Entry point

Codex reads the repo-root **`AGENTS.md`** natively as its instruction file — that is Codex's primary entry point (no separate config needed). `AGENTS.md` names the reading order and points at `.agents/METHODOLOGY.md`; this adapter is the Codex-specific layer beneath it. If Codex supports nested `AGENTS.md` files, a directory-scoped one may refine behavior for that subtree, but the canonical methodology stays single-sourced in `.agents/METHODOLOGY.md`.

## 2. Tool & permission model (differs from other agents)

- Codex runs with its own **sandbox / approval model** (file-write and command-execution permissions are governed by its configured approval mode, not by this repo). **Respect the methodology's gates regardless of the sandbox setting** — a permissive sandbox is not permission to skip the plan-approval gate.
- Prefer Codex's **native file-read/edit tools** over shelling out to `cat`/`sed`. Use **surgical edits** on existing files (mirror `mandatory_planning_rule.md` §3 "punctual edits"); full rewrites only for new files.
- Shell/command execution goes through Codex's exec tool; **announce git and other side-effecting commands** and respect the approval prompt.
- Parallelism support varies by Codex surface; when independent reads/searches can be batched, do so.

## 3. Skills — manual consumption (no native discovery)

Codex has **no native** [Agent Skills](https://agentskills.io/specification) discovery. Consume the catalog manually, like the Gemini adapter does:

1. Read `.claude/skills/_index.md` (the catalog; same path by convention).
2. When a task matches a skill's description/trigger, open and follow that `SKILL.md`.
3. **Lazy-load** a skill's `references/*.md` only when its subject arises.
4. **`disable-model-invocation: true`** skills (e.g. `/wiki-sync`, `/wiki-lint`, `/commit`, and `/cross-team-handoff` if the cross-team module is installed) run **only** on explicit human request — side effects + human gate. **`user-invocable: false`** skills are background knowledge; load silently, do not announce.
5. **Do not invent skills.** Use only those listed; suggest a new one if a recurring case lacks coverage.

## 4. Cautions

- **Name the gate** to the human before advancing (Codex honors gates by instruction, not by lock). "Is the plan approved?" precedes any code change.
- **Validate `file:line` citations** on the main thread before writing them into a plan or wiki page — especially any produced by a sub-agent/search that did not share your context.
- **Knowledge language:** author plans and wiki content in **{{KNOWLEDGE_LANG}}**; code and identifiers in English.

## 5. Git workflow

> A git branching rule ships in **core** (`.agents/rules/git_branching_rule.md`, `trigger: always_on`: single-repo `main`/`dev` + plan-gated `<type>/<work_id>__<scope>` ephemerals). The **monorepo module** replaces it at the same path with the multi-app topology. The branch-creation gate below applies whenever that rule is installed (it is, by default); only a project that deliberately removed the core branching rule skips it.

- **Announce every git command**; respect Codex's approval prompt. Do not batch destructive ops without intermediate confirmation.
- **Before creating a branch** (per the branching rule): (1) `{{project}}_wiki/work/plans/{work_id}.md` exists? (2) `status: approved`? (3) name `<type>/<work_id>__<scope>` valid? If any fails, **stop and require the gate** — do not invent a name.
- **Never `git commit` on protected permanent branches** (e.g. `main`, `staging_*`) — PRs only. **`push --force` only with `--with-lease`.**
- **Host configuration** (branch protection, rulesets, required checks, merge settings, a bot's bypass): **never on your own initiative** — guide the human through the panel. With **explicit, per-task authorisation** you may use the API, and the branching rule's §9.1 obligations then apply: scoped, **recorded** from-what-to-what, and **read back** instead of trusting the write's exit code.

### ⚠ No LLM co-authorship on commits (non-negotiable)

**Forbidden** to include `Co-Authored-By: Codex <…>` — or any trailer/footer identifying the assistant (any Codex/OpenAI model or product name) — in commits produced via Codex. Applies to ordinary commits, merge commits, amendments, any trailer/footer, and PR descriptions. The author is the human; the local `git user` already records authorship. Fix a co-authored message before committing; if already committed, do not rebase without human approval. (An equivalent rule holds for every other agent's adapter.)
