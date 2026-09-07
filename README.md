# agent-dev-methodology

A portable, **LLM-agnostic development methodology** you install into any project by pointing an agent at it. It gives every piece of work three bound artifacts — **task → plan → execution** — and grows a composable **knowledge wiki** (an Obsidian vault) so what you learn accumulates instead of scrolling off in chat history.

It is designed to be driven by **any coding agent** — Claude Code, Codex, Gemini/Antigravity, Cursor — reading the same canonical files.

## What you get

- **A work cycle with human gates.** Nothing runs before a plan is approved; nothing reaches the wiki without review. Plans are preceded by optional **parallel-agent analyses** and a **contextual model recommendation** per role.
- **A knowledge vault.** Obsidian graph linking work ↔ knowledge, mandatory frontmatter, and a strict `file:line` citation discipline (`⚠ unverified` when a claim is not anchored).
- **Skills** (per the [Agent Skills spec](https://agentskills.io/specification)) that encapsulate the repetitive flows: `work-cycle`, `wiki-sync`, `wiki-lint`, `ingest-source`, `commit`, `sync-context`, `work-index`, `work-find`, `work-audit`.
- **Optional modules** you install only when you need them — see the table below.

## Modules

The core is what every project gets. Modules are additive and independent, except where a **Requires** column says otherwise. The install interview (`INSTALL.md` §1) asks one question per module; you can also install one later by following its `INSTALL.md` section.

| Module | Install when | Adds | Requires |
|---|---|---|---|
| `monorepo` | Multiple apps and/or shared packages, each on its own long-lived branch | `git_branching_rule` (replaces the core one) + `knowledge_source_of_truth_rule`; skills `promote-knowledge`, `sync-knowledge`, `distribute-packages`; CI broadcast stubs | — |
| `cross-team` | A partner team collaborates through **their own LLM**, and they cannot read your repo | skill `cross-team-handoff`; handoff/response/living-contract templates | — |
| `intra-team` | More than one agent works **your** repo and they must coordinate | skill `intra-team`; message + coordination-board templates; `work/relay/` | — |
| `peer-relay` | Another project in a **separate repo on the same machine** collaborates; its agent can *read* your files but does not *share* your checkout | skill `peer-relay`; peer registry `.agents/peers.md`; peer-message template | `intra-team` |
| `benchmarks` | The project makes quantitative claims (performance, cost, accuracy) it must stand behind | `benchmark_protocol_rule`; skill `run-benchmark`; benchmark-page template; the `⚠ unverified <metric>` seal | — |
| `contracts` | The project exposes a versioned contract others depend on (public API, DB schema, wire/IPC protocol, event schema, FFI ABI) | `contract_change_rule`; ADR-contract template; the `⚠ contract-drift` tag. **No skill** — this module is discipline, not a flow | — |
| `dev-env` | The project depends on external services (DB, broker, cache) that must be reproducible across machines and CI | `dev_environment_rule`; skill `dev-env`; the `docker/<service>/` layout | — |
| `writing` | The project delivers long-form prose (thesis, papers, articles, posts) derived from its work | a directory-scoped override giving `content/` its own cycle; skills `write-academic`, `write-article`, `write-post`; the `⚠ source needed` seal | — |

Each module directory carries its own `README.md` with the full rationale; the table is a router, not a summary.

### Which messaging module?

Three modules move messages between agents, and they are easy to confuse. They differ on **one axis with three values** — *what access does the reader have to your repository?*

| | `cross-team` | `intra-team` | `peer-relay` |
|---|---|---|---|
| Reader **shares** your checkout | no | **yes** | no |
| Reader **can read** your files | no | yes | **yes** |
| Governing rule | **self-contained** — inline the full spec; `file:line` is provenance only | **reference-first** — cite `file:line`/`[[wikilinks]]`, never re-paste | **reference-first, qualified** — every citation carries a repo prefix |
| Typical reader | a partner squad's LLM | another agent (or session) on this repo | the agent of a sibling project on this machine |

Picking the wrong one has a specific cost. Self-contained where reference-first applies duplicates content that then drifts. Reference-first where it does not apply produces ambiguity (`lib/router.dart:9` exists in both repos), dead links (`[[wikilinks]]` do not cross vaults), and colliding identifiers (two projects both using `YYYY-MM-DD_slug`).

## How to install it

Point your agent at this repo and say:

> "Install this methodology into my project at `<path>`. Follow `INSTALL.md`."

The agent runs an **interview** (`INSTALL.md` §1): five questions that shape the scaffold — project name, vault slug, **knowledge-content language**, which agents will operate the repo, and git host — plus one yes/no per optional module. It then scaffolds the core, wires the entry-points, and installs only what you said yes to.

> **Language.** The kit's own documentation is in English; the **content the methodology generates** — plans, wiki pages, tasks, executions — is written in the language you choose at install. **Never let the agent guess it:** everything downstream is authored in that language, and getting it wrong means rewriting the vault.

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
│   ├── peer-relay/        ← OPTIONAL: agent↔agent across sibling repos (needs intra-team)
│   ├── benchmarks/        ← OPTIONAL: reproducible empirical-claim / benchmark pages
│   ├── contracts/         ← OPTIONAL: versioned cross-boundary contract changes
│   ├── dev-env/           ← OPTIONAL: reproducible external-service containers
│   └── writing/           ← OPTIONAL: prose deliverables (thesis, papers, articles, posts)
├── adapters/              ← per-agent entry-points (claude, codex, gemini, _generic)
└── docs/
    ├── design-rationale.md    the seed-vs-accretion story (install core first, defer the rest)
    └── glossary.md
```

## The one idea to keep

**Work lives inside the vault.** `work/tasks|plans|executions/` sit *inside* `{{project}}_wiki/`, so the Obsidian graph connects a domain page to every plan and execution that ever touched it. This is the load-bearing decision — see `docs/design-rationale.md`.

## Provenance

Distilled from a production mobile monorepo that ran this methodology across multiple apps, packages, and agents. The Obsidian format skills are vendored from [`kepano/obsidian-skills`](https://github.com/kepano/obsidian-skills) (MIT). See `docs/design-rationale.md` for what was proven in practice vs. what is a generalization.
