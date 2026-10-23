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
| 12 | **Does the project deliver long-form prose** for people outside the repo (thesis/dissertation, paper, technical articles, posts), derived from the work it does? | installs `modules/writing/` | no |
| 13 | **Does this project coordinate with another project in a separate repo on the same machine**, whose agent can read your files but does not share your checkout? | installs `modules/peer-relay/` (requires answer 8 = yes) | no |
| 14 | **Commit messages and PR text in the knowledge language?** Only the commit description and the PR title/body; the Conventional Commits type (`feat:`, `docs:` …), branch names, tags and identifiers stay ASCII English either way. | `{{COMMIT_LANG}}` — `English`, or answer 3 | no (English) |

> **Never guess question 3.** If the human does not state a knowledge language, ask explicitly. Everything the methodology generates (plans, wiki pages) is in that language; getting it wrong means rewriting the vault.

Record the answers in a short block you will paste into `{{project}}_wiki/_meta/log.md` as the first entry (§6).

**Stamp the kit version.** The install record also carries `kit_commit: <sha>` — the commit of this kit checkout (`git rev-parse HEAD` in the kit). Write the same stamp to `.agents/KIT_VERSION`, one `key: value` per line:

```
kit_commit: <full sha of the kit checkout>
project: <answer 1>
knowledge_lang: <answer 3>
commit_lang: <answer 14: English, or answer 3>
installed: <YYYY-MM-DD>
modules: [<installed modules>]
```

`/methodology-upgrade` reads it to tell kit changes from local evolutions; without it the comparison cannot say who moved. Update it only when the project adopts kit changes up to a newer commit.

## 2. Placeholder substitution

Every template file in this kit uses `{{...}}` placeholders. When you copy a file into the target project, replace:

| Placeholder | Replace with |
|---|---|
| `{{PROJECT}}` | human-readable project name (answer 1) |
| `{{project}}` | vault slug (answer 2) — the vault dir is `{{project}}_wiki` |
| `{{repo}}` | target repo folder name |
| `{{KNOWLEDGE_LANG}}` | knowledge-content language (answer 3) |
| `{{COMMIT_LANG}}` | commit-message and PR language (answer 14): `English`, or the knowledge language |
| `{{ABS_PATH_TO_THIS_REPO}}` | absolute path of the target repo (peer-relay module only) |

Do a final grep for `{{` after install — **no placeholder may remain** in the target project (§7 checklist). Two kinds of double braces are **not** placeholders and must stay as shipped: `{{args}}` in the Gemini CLI command files (`.gemini/commands/*.toml` — Gemini CLI substitutes it at run time) and Go-template format strings such as `{{.State.Health.Status}}` in the dev-env skill (Docker reads them). CI workflow files use `${{ … }}` expressions for the same reason; the checklist grep does not scan them.

## 3. Install the CORE (always)

The core is portable to any repo, monorepo or not. Copy and de-template these from `core/` into the target project:

```
kit core/                              →  target project
──────────────────────────────────────────────────────────
core/METHODOLOGY.md                    →  .agents/METHODOLOGY.md
core/mcp.md                            →  .agents/mcp.md          (only if the project uses MCP servers)
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
core/templates/adr.md                  →  {{project}}_wiki/decisions/_templates/adr.md
core/templates/wiki-page.md            →  {{project}}_wiki/_meta/_page_template.md
core/templates/source.md               →  {{project}}_wiki/sources/external/_template.md
core/templates/postmortem.md           →  {{project}}_wiki/postmortems/_template.md
core/templates/review.md               →  REVIEW.md               (repo root — the reviewer's instructions; fill it with the human)
core/templates/pull_request_template.md →  .github/pull_request_template.md   (other hosts: their PR-template path, answer 7)
core/skills/*                          →  .claude/skills/*
core/agents/*                          →  .claude/agents/*        (Claude Code only)
core/hooks/require-approved-plan.sh    →  .claude/hooks/require-approved-plan.sh   (optional, recommended — §6; chmod +x)
core/hooks/claude-settings.json        →  .claude/settings.json   (with the plan gate, Claude Code; MERGE into an existing file — §6)
core/hooks/agy-hooks.json              →  .agents/hooks.json      (with the plan gate, Antigravity CLI — §6)
core/hooks/commit-msg                  →  .githooks/commit-msg    (optional, recommended — §6)
core/ci/check_commit_trailers.py       →  scripts/ci/check_commit_trailers.py   (optional, recommended — §6)
core/ci/methodology-checks.yml         →  .github/workflows/methodology-checks.yml   (optional — §6; adapt to the git host)
```

Then create the empty work directories: `{{project}}_wiki/work/{tasks,plans,executions}/` and `{{project}}_wiki/work/archive/`, and write `.agents/KIT_VERSION` (§1).

The core now ships a single-repo git branching rule (`main`/`dev` + plan-gated ephemerals); the monorepo module (§4) replaces it at the same path with the multi-app topology.

**MCP catalog (only if applicable).** If any agent in this repo will use MCP servers, install `core/mcp.md` and fill its §1 table. It is a **catalog consulted on demand**, not part of the mandatory reading prefix — its job is to keep every client's mirrored config (`.mcp.json`, `.gemini/settings.json` for Gemini CLI, `.cursor/mcp.json`) in agreement, so a capability granted to one agent is not invisible to the others. Antigravity has no workspace-level MCP config (user-level `~/.gemini/config/mcp_config.json` only) — the catalog is how its users learn what to mirror. Skip the file entirely if the project uses no MCP server.

**Core skills to install** (from `core/skills/`): `work-cycle`, `wiki-sync`, `wiki-lint`, `wiki-index`, `ingest-source`, `commit`, `sync-context`, `work-index`, `work-find`, `work-audit`, `methodology-upgrade`, and the skills index `_index.md`. `wiki-lint` (`lint.py`, `list_gates.py`), `wiki-index` and `methodology-upgrade` ship scripts too, and `wiki-lint`/`wiki-index`/`work-find` import `work-index`'s parser — keep the skills as siblings. The `work-index`, `work-find` and `wiki-sync` skills ship a small Python script each — copy the whole skill directory. `wiki-sync`'s `sync_bookkeeping.py` appends to `_meta/log.md` without reading it; it auto-detects a single `*_wiki/` vault (pass `--vault` otherwise).

**Role sub-agents (Claude Code only).** `core/agents/` ships six roles — `task-author`, `analyst`, `mechanic`, `planner`, `reviewer`, `scribe` — each pinning a model **tier** in its frontmatter. They exist so the right model can be used per phase **without switching the session's model**, which would discard the prompt cache (see `adapters/claude.md` §3). The `reviewer` also exists for a reason beyond cost: its clean context keeps the author's reasoning out of the review (METHODOLOGY §4.4.1). Install them if your agent runtime supports per-sub-agent model selection; skip the directory otherwise — nothing else depends on it (without sub-agents, run the review in a **fresh session** given only the reviewer's inputs). **Adjust the `model:` tier aliases to your runtime's names**, and pin tiers rather than version numbers so the files do not rot.

**Seed `REVIEW.md` with the human.** Ask two questions and fill the template's first two sections: *which areas have a failure mode of their own* (what does "broken" look like there?) and *which paths are always high risk*. Keep it short — the reviewer reads it on every review. An empty "Do not flag" section is correct on day one; it grows from review outcomes.

**Knowledge directory seed.** Create the knowledge subdirs the project will use. For a single-repo project: `{{project}}_wiki/{domains,entities,services,flows,pages,contracts,decisions,cross-cutting,postmortems,sources/external,sources/internal}/`. For a monorepo, the monorepo module (§4) adds `apps/` and `packages/` layout instead.

**Keep empty directories.** Git does not track an empty directory, so `work/archive/`, the knowledge seed dirs, `sources/internal/` and any other directory this install leaves empty (the `content/` tree, `docker/`, `benchmarks/`, …) vanish from the first commit and from every clone. Once all sections are installed, put an empty `.gitkeep` in each:

```bash
find {{project}}_wiki content docker -type d -empty -not -path '*/.obsidian*' -exec sh -c 'touch "$1/.gitkeep"' _ {} \; 2>/dev/null
```

The kit's scripts read only `*.md`, so `.gitkeep` never shows up in a catalog or a lint finding. Delete it when the directory gets its first page, or leave it — both are harmless.

## 4. Install the MONOREPO module (only if answer 4 = yes)

Adds the machinery for multiple apps/packages on per-app branches. Copy from `modules/monorepo/`:

```
modules/monorepo/rules/git_branching_rule.md            →  .agents/rules/git_branching_rule.md
modules/monorepo/rules/knowledge_source_of_truth_rule.md→  .agents/rules/knowledge_source_of_truth_rule.md
modules/monorepo/skills/*                               →  .claude/skills/*  (promote-knowledge, sync-knowledge, distribute-packages, git-runbook, reset-dev-branch)
modules/monorepo/scripts/*                              →  scripts/          (broadcast stubs + their tests, checkers — adapt to the git host, answer 7)
```

Then reorganize the vault knowledge dirs under `{{project}}_wiki/apps/<app>/` and `{{project}}_wiki/packages/<pkg>/` per `modules/monorepo/README.md`, and follow its **roster checklist** for wiring each app/package into the branch topology and CI.

**Zero apps yet?** Keep the optional §1.1 of the branching rule (work on `main` until the first `dev_<app>`) and wire `scripts/check-transition-state.sh` into CI; otherwise delete §1.1. Delete the `bench`/`contract` rows of its §4.2 for modules not installed.

**Append-only log.** Add to the root `.gitattributes` (create it if absent): `{{project}}_wiki/_meta/log.md merge=union`. Without it, the broadcast auto-reconcile adopts `main`'s log and silently drops the `dev_<app>` entries not yet promoted. Do **not** add `_meta/index.md` or `work/_index.md` — `union` corrupts lines edited on both sides (`knowledge_source_of_truth_rule.md` §3.6).

**Path list.** Adapt the knowledge-layer path list in `knowledge_source_of_truth_rule.md` §2 and §3.6 (replace each `<placeholder>`, drop lines that do not apply, mark not-yet-created paths `— DECLARED, not yet created`), mirror it into the two skills' `KL_PATHS` and `scripts/broadcast-main.sh` `KNOWLEDGE_PATHS`, then run `python3 scripts/check-knowledge-paths.py` until it prints `ok` (rule §9.1).

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
- Create `{{project}}_wiki/work/relay/` and seed `{{project}}_wiki/work/relay/_board.md` from the coordination-board template **and** `{{project}}_wiki/work/relay/_locks.md` from the scope-locks template.
- **Choose the publication route for `_locks.md` before seeding it** — `modules/intra-team/README.md` §4.2. It is live state: on the default per-branch route it is invisible during exactly the window a lock exists for, which is the defect §4 documents. Write the choice down, with what it does not fix.
- *(Opt-in, only for the named-exception route.)* Copy `modules/intra-team/skills/scope-lock/` → `.claude/skills/scope-lock/` and paste `modules/intra-team/snippets/branching-live-state-exception.md` into the branching rule — both or neither (README §4.2) — and register `scope-lock` in `.claude/skills/_index.md` (agent-invocable).
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

## 5-sexies. Install the WRITING module (only if answer 12 = yes)

Adds long-form prose as a first-class deliverable: a directory-scoped override that swaps the trio cycle for a writing cycle inside `content/`, three human-gated writing skills, and the `⚠ source needed` seal. Copy from `modules/writing/`:

```
modules/writing/templates/content-entrypoint.md  →  content/CLAUDE.md   (and/or content/AGENTS.md, per answer 5)
modules/writing/skills/*                         →  .claude/skills/*    (write-academic, write-article, write-post)
modules/writing/conventions-extension.md         →  append into {{project}}_wiki/_meta/conventions.md
```

Then: create the `content/` tree (`academic/`, `articles/{drafts,published}/`, `posts/{drafts,published}/`, `_norms/`, `_drafts/`, `_assets/`, plus a `content/_index.md` catalog); register the three skills as **manual-only** (`disable-model-invocation: true`) in `.claude/skills/_index.md`.

**Two adaptations are required, not optional.** `write-academic` ships generic: fill in its persona with the project's domain, and replace its style section with the conventions of the **style authority that actually governs the work** (asked for at first use if `content/_norms/` is empty). If an institutional rulebook governs AI use, transcribe its binding rules and record any author override in the skill's override table, with its safeguard. See `modules/writing/README.md`.

**If answer 12 = no:** skip. The METHODOLOGY §4.6 override concept still applies to any subtree whose work has a different shape — this module is the worked instance of it for prose.

## 5-septies. Install the PEER-RELAY module (only if answer 13 = yes)

Adds agent↔agent coordination **across sibling repos on one machine** — the third value of the axis that `cross-team` and `intra-team` split on. Copy from `modules/peer-relay/`:

```
modules/peer-relay/skills/peer-relay/   →  .claude/skills/peer-relay/
modules/peer-relay/templates/peer-message.md  →  {{project}}_wiki/work/relay/_templates/
modules/peer-relay/templates/peers.md         →  .agents/peers.md
modules/peer-relay/conventions-extension.md   →  append its fields into {{project}}_wiki/_meta/conventions.md
```

**Prerequisite: answer 8 must be yes.** This module *inherits* intra-team's machinery — the five `msg_role`s, the stable-ID ask table, the round log, `work/relay/` and `_board.md` — instead of duplicating it. Installing it without intra-team leaves dangling references. Append its conventions extension **after** intra-team's, which it declares inheritance from.

Then:
- Fill `.agents/peers.md`: one section per peer with path, citation prefix, write policy, inbox, **absorption entry points in reading order**, and a **Quirks** block. The quirks block is the highest-value field — record every place an index in that repo actively misleads a reader.
- Register `peer-relay` in `.claude/skills/_index.md` — mark it **hybrid** (`absorb`/`read` autonomous; `send` carries a **double** human gate — the text, then the write into another repo; `board` gated).
- **No script change needed**, same as intra-team: `work-index`/`work-find`/`work-audit` scan only `tasks`/`plans`/`executions`.
- **Mirror the counterpart** in the peer, and diff the two registries side by side — mirroring is neither automatic nor verified, and a mismatched inbox means messages written and never read.
- Add the `relay` branch scope and the entry-point non-negotiable ("writing into a peer repo is an external action") — `modules/peer-relay/README.md` §7–§8.

Follow `modules/peer-relay/README.md` for the qualified-citation rule (a `file:line` without a repo prefix is a format error), the they-can-but-won't asymmetry, and claim-state with origin.

**If answer 13 = no:** skip. `cross-team` covers a partner with no access to your code; `intra-team` covers another agent in your repo. This module is only for the middle case.

## 6. Generate the per-agent entry-points (from `adapters/`)

The methodology is agent-agnostic; each agent just needs a thin stub pointing at `.agents/METHODOLOGY.md`. For each agent named in answer 5:

- **Claude Code** → `.agents/llm/claude.md` (from `adapters/claude.md`) + a root `CLAUDE.md` stub that points to the reading order (§9 of METHODOLOGY). Claude discovers `.claude/skills/` natively.
- **Gemini CLI / Antigravity** → `.agents/llm/gemini.md` (from `adapters/gemini.md`) + a root `GEMINI.md` with a **"Skills available"** section. Then:
  - **Skills link — REQUIRED.** Create the symlink `.agents/skills -> ../.claude/skills` (`ln -s ../.claude/skills .agents/skills`) and commit it. Antigravity discovers workspace skills at `.agents/skills/<name>/SKILL.md`; without the link it sees none of `.claude/skills/`. Use `.agents/skills.json` (`{ "entries": [ { "path": "../.claude/skills" } ] }`) **only as a fallback** where a symlink cannot exist — relative-path entries have been reported unreliable, and a directory entry loads only its direct children.
  - **Gemini CLI** → copy `core/gemini-commands/*.toml` (and any installed module `*/gemini-commands/*.toml`) into `.gemini/commands/` to expose skills as native `/command` slash commands. Antigravity does not read them.
  - **Antigravity CLI (`agy`)** → install the plan gate (next bullets) and copy `core/hooks/agy-hooks.json` to `.agents/hooks.json`. `agy` runs the hook with CWD `.agents/`, so its command is `../.claude/hooks/require-approved-plan.sh` — the same script Claude Code uses, which detects the `agy` payload. What `agy` loads, and its 20,000-token rule budget: `adapters/gemini.md` §1.
- **Codex / others** → `.agents/llm/codex.md` (from `adapters/codex.md`).
- **Always** → a root `AGENTS.md` (from the kit's `AGENTS.md`, de-templated) as the universal entry-point convention. This is the file a generic agent looks for.
- **Optional (recommended): Turn the plan gate into a real lock** → copy `core/hooks/require-approved-plan.sh` to `.claude/hooks/require-approved-plan.sh` (chmod +x), adapt its `GUARDED` prefixes to the project's code directories, and register it for Claude Code by copying `core/hooks/claude-settings.json` to `.claude/settings.json` — or, if that file exists, **merging** this entry into its `hooks.PreToolUse` array and adding its top-level `"attribution": false` (keep every other key):
  ```json
  {"attribution": false,
   "hooks": {"PreToolUse": [{"matcher": "Edit|Write|MultiEdit|NotebookEdit",
    "hooks": [{"type": "command", "command": "\"$CLAUDE_PROJECT_DIR\"/.claude/hooks/require-approved-plan.sh"}]}]}}
  ```
  The hook checks guarded code directories and verifies plan approval, neutrally supporting both `.claude/active_work.json` and `.gemini/active_work.json`. It speaks two protocols: Claude Code's (exit 2 + stderr) and Antigravity CLI's (`.agents/hooks.json`, above: a JSON `deny` on stdout to block, **empty** stdout to allow — never `"allow"`, which would skip the permission prompt). Gemini CLI hooks live in `.gemini/settings.json` (Gemini CLI only); the kit has not verified the script against that protocol.
- **Optional (recommended): mechanize the no-LLM-co-author rule** → copy `core/hooks/commit-msg` to `.githooks/commit-msg` (chmod +x) and `core/ci/check_commit_trailers.py` to `scripts/ci/`, then run `git config core.hooksPath .githooks` (once per clone — put it in the onboarding notes). The hook is early feedback only (it ignores the diff `git commit -v` appends below the scissors line); the guarantee is the CI step, which runs the same script on the commits each PR adds — `python3 scripts/ci/check_commit_trailers.py origin/<PR base>`, with a full-depth checkout — and on every push to a permanent branch — `main`, `dev`, `dev_*`, `staging_*` (`<before>..<sha>`; a brand-new branch checks every commit not yet on the default branch or another permanent line; a rewind is ok with a note; `core.commentChar` is honoured for the scissors line). Commits already on a permanent branch (`main`, `dev`, `dev_*`, `staging_*`) are excluded with repeated `--exclude`, so a release/integration PR (`dev` → `main`, `staging_<app>` → `main`) is not charged for old history. `core/ci/methodology-checks.yml` is a GitHub Actions template running it plus `/wiki-lint`. Plant a trailer once and watch both layers go red before trusting them (METHODOLOGY §6.7). For Claude Code, the `"attribution": false` key in `.claude/settings.json` (shipped in `core/hooks/claude-settings.json`; Claude Code ≥ 2.1.281) removes the cause — the assistant stops writing its co-author trailer and PR footer; the hook and CI still catch whatever gets through (an older client, a local override, another agent).

Every entry-point stub is short: it names the reading order and points at the canonical `.agents/METHODOLOGY.md`. Never duplicate methodology content into a stub. Each stub (`CLAUDE.md`, `GEMINI.md`, `AGENTS.md`) also carries the one-line commit/PR convention from the kit's `AGENTS.md` "Non-negotiables" — copy that line as-is (de-templated: it names the commit language of answer 14, which the branching rule's language clause states too). If commits follow the knowledge language and the intra-team module is installed, also set `SCOPE_LOCK_MSG_TAKE` / `SCOPE_LOCK_MSG_RELEASE` (scope-lock `SKILL.md`).

## 7. Post-install verification checklist

Run these before telling the human it is done:

- [ ] `grep -rn '{{' .agents {{project}}_wiki .claude .gemini scripts CLAUDE.md GEMINI.md AGENTS.md REVIEW.md .github/pull_request_template.md 2>/dev/null | sed -E 's/\{\{(args|\.State\.Health\.Status)\}\}//g' | grep '{{'` returns **nothing** (all placeholders substituted; the `sed` strips only the two run-time templates of §2, so a missed placeholder on the same line still shows, with its `file:line` — `scripts/` matters when the monorepo module installed the broadcast scripts, which carry `{{project}}` paths).
- [ ] `.agents/METHODOLOGY.md`, `.agents/rules/mandatory_planning_rule.md` exist.
- [ ] `{{project}}_wiki/_meta/{conventions,index,log}.md` and `overview.md` exist.
- [ ] `{{project}}_wiki/work/{tasks,plans,executions,archive}/` exist (with `_template.md` in tasks/plans/executions).
- [ ] No directory is left empty: `find {{project}}_wiki content docker -type d -empty -not -path '*/.obsidian*' 2>/dev/null` prints nothing (§3, `.gitkeep`).
- [ ] `REVIEW.md` at the repo root, with "What failure looks like" and "Always high risk" filled with the human; `{{project}}_wiki/postmortems/_template.md` exists.
- [ ] `.github/pull_request_template.md` exists (or the host's equivalent) with Summary / Testing / Risk / How to revert, and every root entry-point carries the commit/PR convention line.
- [ ] `.claude/skills/_index.md` lists exactly the skills you installed (core, plus modules if chosen).
- [ ] Root entry-point(s) for each chosen agent exist and point at `.agents/METHODOLOGY.md`.
- [ ] If Gemini installed: `.agents/llm/gemini.md` + root `GEMINI.md` exist; `test -L .agents/skills && ls .agents/skills/work-cycle/SKILL.md` succeeds (the skills link); `.gemini/commands/` populated if targeting Gemini CLI; if targeting Antigravity, `.agents/hooks.json` is the named-hook object (top-level key `plan-gate`, not `hooks`) and a guarded write on a non-ephemeral branch is denied — with `G` set to a path under one of your `GUARDED` prefixes (e.g. `G=src/probe`), `printf '%s' '{"toolCall":{"name":"write_file","args":{"Path":"'"$PWD/$G"'"}},"workspacePaths":["'"$PWD"'"]}' | (cd .agents && sh -c ../.claude/hooks/require-approved-plan.sh)` prints a `deny`.
- [ ] If monorepo module installed: `.agents/rules/git_branching_rule.md` + `knowledge_source_of_truth_rule.md` exist; roster checklist done; `.gitattributes` has `{{project}}_wiki/_meta/log.md merge=union`; `python3 scripts/check-knowledge-paths.py` prints `ok`; the five self-tests pass — `bash scripts/test-broadcast-main.sh`, `bash scripts/test-broadcast-packages.sh`, `sh scripts/test_promote_detect.sh`, `sh scripts/test_dev_branch_reset.sh`, `sh scripts/test_check_branch_scope.sh`; §1.1 kept only if no `dev_*` exists.
- [ ] If cross-team module installed: `cross-team-handoff` skill present; conventions extended.
- [ ] First `{{project}}_wiki/_meta/log.md` entry written (the install record, §1), with `kit_commit:`; `.agents/KIT_VERSION` holds the same stamp.
- [ ] `.claude/skills/_index.md` §"Modules NOT installed" lists every module left out, why, and what would bring it in (§8).
- [ ] `/work-index` runs clean (generates an empty-but-valid `work/_index.md`).
- [ ] Every always-loaded file fits the per-file cap: `wc -c AGENTS.md GEMINI.md $(grep -l '^trigger: always_on' .agents/rules/*.md) 2>/dev/null` shows each **≤ 22,000 bytes** after de-templating (Antigravity CLI cuts a rule file at ~24 KB, silently — `adapters/gemini.md` §1.1, with a probe to confirm; the lint below gates it as `rule-size`). Over it: move rationale/examples to the rule's skill, keep every 🔒 line.
- [ ] `python3 .claude/skills/wiki-lint/lint.py --root .` exits 0 (after `/work-index`, above). On an existing vault with debt, run `--init-baseline` once and commit `{{project}}_wiki/_meta/lint-baseline.json` — never start with a red gate.
- [ ] If the plan gate was installed: `.claude/hooks/require-approved-plan.sh` is executable, `python3 -m json.tool .claude/settings.json` parses and shows the `Edit|Write|MultiEdit|NotebookEdit` entry and `"attribution": false`, and a guarded write on `main` is refused — with `G` set to a path under one of your `GUARDED` prefixes (e.g. `G=src/probe`), `printf '%s' '{"tool_input":{"file_path":"'"$PWD/$G"'"}}' | CLAUDE_PROJECT_DIR=$PWD .claude/hooks/require-approved-plan.sh; echo $?` prints `2`.
- [ ] If the trailer check was installed: a planted `Co-Authored-By: Claude …` commit is refused by the hook, and `scripts/ci/check_commit_trailers.py` exits 1 on a branch carrying one.
- [ ] `.agents/rules/git_branching_rule.md` exists (core single-repo variant, or the monorepo module's variant if installed).
- [ ] If benchmarks module installed: `.agents/rules/benchmark_protocol_rule.md`, `{{project}}_wiki/benchmarks/_template.md`, `run-benchmark` skill, conventions extended.
- [ ] If contracts module installed: `.agents/rules/contract_change_rule.md`, `{{project}}_wiki/decisions/_templates/adr-contract.md`, conventions extended.
- [ ] If dev-env module installed: `.agents/rules/dev_environment_rule.md`, `dev-env` skill, `docker/` created + `docker/**/.env` gitignored.
- [ ] If writing module installed: `content/CLAUDE.md` override present and naming the safeguards it keeps; the three `write-*` skills registered as manual-only; `content/` tree created; conventions extended; **`write-academic` adapted** — persona filled in and the style section replaced with the actual style authority (a shipped-as-is `write-academic` is an incomplete install).

## 7-bis. Bootstrap commit and the `dev` branch (single-repo only)

The core branching rule has two permanent branches, `main` and `dev`, and every ephemeral branch starts from `dev` — so `dev` must exist before the first work cycle, and it must hold the **whole** install. Cut it only after the §7 checklist is green, because the checklist itself produces files to commit (`work/_index.md` from `/work-index`, a lint baseline, fixes).

1. The human commits the install **and the checklist's outputs** on `main` — the bootstrap commit. The rule cannot be followed before `dev` exists; record the commit in the install log entry as that exception.
2. `git status --porcelain` prints nothing.
3. Announce and run:
   ```bash
   git branch dev main
   git push -u origin main dev        # skip if the repo has no remote yet; push both once it does
   ```
4. Verify: `git rev-parse dev` equals `git rev-parse main`, and with a remote `git ls-remote --heads origin main dev` lists both.

Then guide the human to protect `main` and `dev` in the git host (rule §3, host neutrality). **Monorepo module installed:** skip this section — that topology has its own permanent branches and bootstrap (`modules/monorepo/README.md`).

## 8. Hand-off to the human

Record the **modules NOT installed** in `.claude/skills/_index.md` (the section the kit's index ships with): one row per module left out, with the interview answer that excluded it and the concrete trigger that would justify installing it later. It stops anyone from looking for a skill that is not there, and turns a later install into a decision instead of an accident.

Report: which modules you installed and why, the language chosen for knowledge content, the entry-points generated, and the reading order for a fresh agent (METHODOLOGY §9). Then stop — the first real task starts the normal work cycle (`work-cycle` skill), which begins with the human authoring a task.

> **Do not** begin documenting the existing codebase or writing code as part of the install. That is the first *work cycle*, gated on the human's first task and an approved plan.
