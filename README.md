# agent-dev-methodology

A portable, **LLM-agnostic development methodology** you install into any project by pointing an agent at it. It gives every piece of work three bound artifacts — **task → plan → execution** — and grows a composable **knowledge wiki** (an Obsidian vault) so what you learn accumulates instead of scrolling off in chat history.

It is designed to be driven by **any coding agent** — Claude Code, Codex, Gemini/Antigravity, Cursor — reading the same canonical files.

## What you get

- **A work cycle with human gates.** Nothing runs before a plan is approved; nothing reaches the wiki without review. Plans are preceded by optional **parallel-agent analyses** and a **contextual model recommendation** per role.
- **A knowledge vault.** Obsidian graph linking work ↔ knowledge, mandatory frontmatter, and a strict `file:line` citation discipline (`⚠ unverified` when a claim is not anchored).
- **Skills** (per the [Agent Skills spec](https://agentskills.io/specification)) that encapsulate the repetitive flows: `work-cycle`, `wiki-sync`, `wiki-lint`, `ingest-source`, `commit`, `sync-context`, `work-index`, `work-find`, `work-audit`.
- **Optional modules** you install only when you need them:
  - **`modules/monorepo/`** — branch topology, canonical-knowledge-in-`main`, promote/sync/broadcast machinery. For multi-app/multi-package repos.
  - **`modules/cross-team/`** — bidirectional LLM↔LLM collaboration with a partner team (e.g. backend) that does **not** share your repo, via a `cross-team-handoff` skill and living-contract pages.
  - **`modules/intra-team/`** — the mirror of cross-team for agents that **do** share the repo: agent↔agent notes, requests, handoffs, conflict resolution, and a coordination board. Reference-first (cite `file:line`) instead of self-contained.
  - **`modules/benchmarks/`** — the empirical-claim discipline: a quantitative claim (performance, cost, accuracy, …) needs a reproducible evidence page or it carries `⚠ unverified <metric>` and cannot be cited. Adds a `benchmark_protocol_rule`, a benchmark-page template, and a `run-benchmark` skill.
  - **`modules/contracts/`** — the cross-boundary-contract discipline: a change to a versioned contract (public API, DB schema, wire/IPC protocol, event schema, FFI ABI) requires an atomic ADR + synchronized multi-artifact PR.
  - **`modules/dev-env/`** — reproducible external-service environments: versioned per-service containers, mandatory healthcheck, and persistent/ephemeral/benchmark lifecycle modes, operated by a `dev-env` skill.

## How to install it

Point your agent at this repo and say:

> "Install this methodology into my project at `<path>`. Follow `INSTALL.md`."

The agent runs a short **interview** (`INSTALL.md` §1) — project name, vault slug, **knowledge-content language**, monorepo yes/no, which agents, partner-team yes/no, git host — then scaffolds the core, wires the entry-points, and installs only the modules you need.

> The kit's own documentation is in **English**. The **content the methodology generates** (plans, wiki pages, tasks) is written in the **language you choose at install** — the agent will ask.

## Repository layout

```
agent-dev-methodology/
├── README.md              ← you are here
├── INSTALL.md             ← the agent playbook (interview + scaffolding steps)
├── AGENTS.md              ← universal entry-point convention (multi-agent)
├── core/                  ← portable to ANY repo
│   ├── METHODOLOGY.md         canonical, LLM-agnostic
│   ├── mcp.md                 MCP server catalog, mirrored across clients (optional)
│   ├── rules/                 mandatory_planning_rule + git_branching_rule
│   ├── templates/             task / plan / execution / wiki-page / source
│   ├── skills/                the generic core skills (+ scripts)
│   ├── agents/                role sub-agents with a pinned model tier (Claude Code)
│   └── vault/                 Obsidian skeleton (_meta, overview, .obsidian)
├── modules/
│   ├── monorepo/          ← OPTIONAL: branching + promote/sync/broadcast
│   ├── cross-team/        ← OPTIONAL: partner-team LLM handoff (no shared repo)
│   ├── intra-team/        ← OPTIONAL: agent↔agent messaging (shared repo)
│   ├── benchmarks/        ← OPTIONAL: reproducible empirical-claim / benchmark pages
│   ├── contracts/         ← OPTIONAL: versioned cross-boundary contract changes
│   └── dev-env/           ← OPTIONAL: reproducible external-service containers
├── adapters/              ← per-agent entry-point templates
└── docs/
    ├── design-rationale.md    the seed-vs-accretion story (install core first, defer the rest)
    └── glossary.md
```

## The one idea to keep

**Work lives inside the vault.** `work/tasks|plans|executions/` sit *inside* `{{project}}_wiki/`, so the Obsidian graph connects a domain page to every plan and execution that ever touched it. This is the load-bearing decision — see `docs/design-rationale.md`.

## Provenance

Distilled from a production mobile monorepo that ran this methodology across multiple apps, packages, and agents. The Obsidian format skills are vendored from [`kepano/obsidian-skills`](https://github.com/kepano/obsidian-skills) (MIT). See `docs/design-rationale.md` for what was proven in practice vs. what is a generalization.
