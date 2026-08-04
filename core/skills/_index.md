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
| `wiki-lint` | Manual: `/wiki-lint` | Check wiki health (stale, orphans, contradictions, abandoned work). |
| `ingest-source` | Manual: `/ingest-source {path-or-url}` | Ingest an external source into the wiki. |
| `commit` | Manual: `/commit [work_id?]` | Close the cycle: sync pending executions + commits grouped by work_id and type. |
| `sync-context` | Manual: `/sync-context` | Sync the local working tree with the remote before new work (fetch + status + gated pull). |
| `work-audit` | Manual: `/work-audit [--days N] [--code-check] [--fix]` | Audit drift between trio frontmatter and the generated `{{project}}_wiki/work/_index.md`. Read-only by default; `--fix` applies trivial corrections. |
| `work-index` | Manual: `/work-index [--check] [--quarter YYYY-Qn]` | Deterministically generate `work/_index.md` (active) + `work/archive/YYYY-Qn.md` (closed by quarter) from the trio frontmatter. Regenerate > hand-edit. |
| `work-find` | Manual: `/work-find <terms> [--topic T] [--status S]` | Ranked full-text search over old work (executions + frontmatter); returns pointers without re-reading the index. For "how was X done" / "has this bug appeared before?". |

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
- **Action skills:** use `disable-model-invocation: true` to force manual invocation (e.g. deploy, sync).
- **Automatic paths:** use `paths: "glob1, glob2"` to load the skill automatically when the agent edits matching files.
