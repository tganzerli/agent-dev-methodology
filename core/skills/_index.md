# Skills Index

Catalog of the skills available in this project. They follow the [Agent Skills spec](https://agentskills.io/specification) — they work in Claude Code, Codex CLI, OpenCode, and (with manual adaptation) other agents.

**Discovery:**
- **Claude Code** discovers everything here automatically — just open the project.
- **Agents without native skill discovery** (e.g. Gemini CLI) are pointed at this index by their entry-point (`GEMINI.md`, `AGENTS.md`) and read the matching `SKILL.md` when the topic hits.

## Core — operational (methodology cycle)

Implement the work cycle described in `.agents/METHODOLOGY.md`. Portable to any project, single-repo or monorepo.

| Skill | Invocation | Trigger |
|---|---|---|
| `work-cycle` | Automatic | Start/drive the task → plan → execution cycle. Includes pre-plan analysis triage (parallel agents) and contextual per-role model recommendation. |
| `wiki-sync` | Manual: `/wiki-sync {work_id}` | Propagate a finished execution to the knowledge pages. |
| `wiki-lint` | Manual: `/wiki-lint` | Check wiki health by script: gates (catalog drift, summaries, wikilinks, frontmatter, index format, rule citations) ratcheting against a baseline; warnings (stale, orphans, stalled work); the 🔒 gate list. |
| `wiki-index` | Automatic / `/wiki-index <dir>\|--all [--check]` | Generate a knowledge sub-index (`decisions/`, `cross-cutting/`, `sources/external/`, `postmortems/`) from page `summary`. Regenerate > hand-edit. |
| `ingest-source` | Manual: `/ingest-source {path-or-url}` | Ingest an external source into the wiki. |
| `commit` | Manual: `/commit [work_id?]` | Close the cycle: sync pending executions + commits grouped by work_id and type. |
| `sync-context` | Manual: `/sync-context` | Sync the local working tree with the remote before new work (fetch + status + gated pull). |
| `work-audit` | Manual: `/work-audit [--days N] [--code-check] [--fix]` | Audit drift between trio frontmatter and the generated `{{project}}_wiki/work/_index.md`. Read-only by default; `--fix` applies only deterministic corrections (never fills Commits). |
| `work-index` | Manual: `/work-index [--check] [--quarter YYYY-Qn]` | Deterministically generate `work/_index.md` (active) + `work/archive/YYYY-Qn.md` (closed by quarter) from the trio frontmatter. Regenerate > hand-edit. |
| `methodology-upgrade` | Manual: `/methodology-upgrade <kit-path>` | Compare the installed methodology with a kit checkout from the `.agents/KIT_VERSION` stamp: kit changes to adopt, local evolutions to upstream. Proposes only. |
| `work-find` | Manual: `/work-find <terms> [--topic T] [--status S]` | Ranked full-text search over old work (executions + frontmatter); returns pointers without re-reading the index. For "how was X done" / "has this bug appeared before?". |

## Modules NOT installed

Recorded at install (the kit's `INSTALL.md` §8) so nobody looks for a skill that is not here, and so installing one later is a conscious decision. Modules are additive and independent: install later from the kit's `INSTALL.md`, module section.

| Module | Why it was left out | What would bring it in |
|---|---|---|
| `{module}` | {the interview answer that excluded it} | {the concrete trigger — e.g. the first performance claim the project must defend} |

## Vendored — Obsidian skills

Knowledge about Obsidian formats (wikilinks, callouts, bases, canvas, clean web extraction). **Installed separately** — they are not part of the core kit. See the kit's vendoring notes. Load on demand when applicable; `obsidian-markdown` pairs with `wiki-sync`/`ingest-source`, and `defuddle` pairs with `ingest-source` (extract clean markdown from a URL).

## Added by optional modules

- **Monorepo module** — adds `promote-knowledge`, `sync-knowledge`, `distribute-packages` (per-app branch topology, knowledge-canonical-in-`main`, CI broadcast). Installed only for multi-app/multi-package repos. See `modules/monorepo/`.
- **Cross-team module** — adds `cross-team-handoff` (bidirectional LLM↔LLM collaboration with a partner team). See `modules/cross-team/`.
- **Intra-team module** — adds `intra-team` (agent↔agent coordination inside one repo: notes, requests, responses, handoffs, conflicts, and a coordination board). **Hybrid** invocation: `note` is agent-invocable/autonomous; every other flow carries an in-body human gate. See `modules/intra-team/`.
- **Benchmarks module** — adds `run-benchmark` (manual `/run-benchmark {work_id}`: collect environment metadata, run the exact command, do the statistics, generate a reproducible chart, write the benchmark page). Installed when the project makes quantitative/empirical claims. See `modules/benchmarks/`.
- **Contracts module** — adds **no skill** (a `contract_change_rule` + an ADR-contract template + a conventions extension). See `modules/contracts/`.
- **Dev-environment module** — adds `dev-env` (manual `/dev-env up|down|status|logs|exec`: operate versioned per-service containers, wait on healthchecks, persistent/ephemeral/benchmark lifecycle). See `modules/dev-env/`.
- **Domain skills** — background knowledge skills (`user-invocable: false`) that load automatically when the agent touches a domain area. Added as the knowledge base grows; not part of the seed.

## How to create a new skill

1. Choose the name — kebab-case; domain skills use a `domain-*` prefix.
2. Create `.claude/skills/{name}/SKILL.md` with minimal frontmatter:
   ```yaml
   ---
   name: skill-name
   description: What it does AND when to apply it. Include keywords the agent will recognize.
   ---
   ```
3. Keep the body concise — instructions, workflows. Extensive material goes to `references/*.md` (lazy-load).
4. Update this index.
5. Update any non-native agent's entry-point (`GEMINI.md`, `AGENTS.md`) if the skill should be discoverable there.

## Conventions

- **`description` is the trigger.** Write the main use case first — the spec cuts at ~1536 characters.
- **Keep the body short** — loaded skills stay in context for the rest of the session. Extensive material goes to `references/`.
- **Tool pre-approval:** use `allowed-tools: Bash(git *) Read Grep` if the skill runs commands.
- **Background/domain skills:** use `user-invocable: false` to hide them from the `/` menu.
- **Action skills — when to set `disable-model-invocation: true`.** Set it when **at least one** answer is yes:
  1. Does the skill have an effect **outside the repo, or one that is hard to revert**? (publishes, sends, starts containers, runs an expensive battery, rewrites stable knowledge pages)
  2. **Is** the skill the human gate of a cycle transition (METHODOLOGY §2, principle 3), rather than a step inside one?

  If both are no, leave it model-invocable. A deterministic, idempotent generator whose output derives from versioned files and reverts with `git checkout` (`work-index`, `wiki-index`) is **not** a case for blocking. *(Origin: deciding by example — "use it for /wiki-sync" — left a generator blocked while other skills told the agent to run its script directly: a gate the norm itself bypassed.)*
- **Automatic paths:** use `paths: "glob1, glob2"` to load the skill automatically when the agent edits matching files.
