# Design Rationale — seed vs. accretion

> Why the methodology is shaped the way it is, and — crucially for an installing agent — **what to install first vs. what to defer**. Distilled from a production monorepo that ran this methodology across multiple apps, packages, and agents over months. Read this before deviating from the layout.

## The core insight

The methodology has a **minimal seed** that shipped on day one and worked in a plain repo, and a set of **accretions** that were each added later *only when a specific pain appeared*. If you install the whole thing into a small project, most of it is dead weight. **Install the seed. Add an accretion when — and only when — its triggering pain shows up.**

## The seed (install always — `core/`)

These existed from the first day and are irreducible:

1. **Plan-then-execute** as an always-on rule, with a hard human approval gate before any code runs.
2. **The trio** — task (human request) / plan (LLM analysis) / execution (live log) — bound by a shared `work_id = YYYY-MM-DD_slug`.
3. **Three status vocabularies** — task `open→in_progress→done` (+ `cancelled`/`aborted`); plan `draft→approved→executed`; execution `in_progress→done`/`aborted`.
4. **A canonical, LLM-agnostic `METHODOLOGY.md`** + thin per-agent adapters. One source of truth; stubs only point to it.
5. **An Obsidian vault** (`{{project}}_wiki/`) with mandatory frontmatter, the **`file:line` citation discipline** (`⚠ unverified` fallback), and wikilinks — with **`work/` living inside the vault** so the graph connects work ↔ knowledge. *This is the single most load-bearing layout decision.*
6. **The `sources/external` ingest pattern** for partner/external docs (summary + link, never raw copy).
7. **A first set of skills:** `work-cycle`, `wiki-sync`, `wiki-lint`, `ingest-source`.
8. **Two catalogs** (`_meta/index.md` for knowledge, `work/_index.md` for work), a `conventions.md`, an `overview.md`, and an append-only `_meta/log.md`.

If you install nothing else, the project already has a working, disciplined methodology.

> **Note on branching.** A later refinement promoted a *minimal* git branching discipline into the seed (`core/rules/git_branching_rule.md`): `main`/`dev`, throwaway `experiment/<slug>`, and plan-gated `<type>/<work_id>__<scope>` ephemerals with a creation gate. Any repo where an agent creates branches wants it; only the multi-app permanent topology stays deferred to the monorepo module. It appears in the accretion table below as a core-shipped item, for honesty about when it arrived.

## The accretions (defer until the pain appears)

Each was a response to a concrete problem. Add it when you recognize the trigger.

| Accretion | Trigger that justified it | Where in the kit |
|---|---|---|
| **Minimal git branching** (`main`/`dev`, `experiment/<slug>`, plan-gated `<type>/<work_id>__<scope>` ephemerals) | An agent can create branches — true even in a single repo | `core/rules/git_branching_rule.md` |
| **Multi-app branch topology** (per-app permanent branches, promote/broadcast) | Multiple apps on independent cadences | `modules/monorepo/` |
| **Knowledge-canonical-in-`main`** + `promote-knowledge` / `sync-knowledge` | Knowledge fragmented across per-app branches; `main` went stale | `modules/monorepo/` |
| **`work-audit`** | Drift between trio frontmatter and the index | `core/skills/` (generic, but born from scale) |
| **`dev_packages` trunk + CI broadcast** | N simultaneous package PRs were operationally heavy | `modules/monorepo/` |
| **Generated work-index + quarterly archive + `topic`/`summary` + `work-find`** | The flat index hit ~45k tokens; drift; merge conflicts; no thematic axis | `core/skills/` (`work-index`, `work-find`) |
| **Execution = historical / knowledge = living memory** corollary | Costly lessons were dying in chronological logs nobody re-reads | `core/` (conventions §"Execution = historical log") |
| **Pre-plan parallel-agent analyses + contextual per-role model recommendation** | Big/risky tasks needed investigation before a plan could be trusted | `core/` (METHODOLOGY §4.2.5, `work-cycle`) |
| **Agent↔agent messaging** (relay notes/requests/handoffs/conflicts + coordination board) | More than one agent on the same repo — concurrent agents clobbering each other's scope, or work handed across sessions with context lost | `modules/intra-team/` |
| **Empirical-claim discipline** (reproducible benchmark page, `⚠ unverified <metric>`, hypothesis verdict, anti-p-hacking) | The project makes quantitative claims it must stand behind | `modules/benchmarks/` |
| **Cross-boundary contract discipline** (atomic ADR + synchronized PR for a versioned contract) | The project exposes a versioned contract other code/teams depend on | `modules/contracts/` |
| **Reproducible external-service env** (versioned containers, healthcheck, lifecycle modes) | The project depends on external services (DB/broker/cache) | `modules/dev-env/` |

### Why `work-index`/`work-find`/`work-audit` are in `core/`, not `monorepo/`
They were *born* from scale pain, but their logic is generic — they operate on trio frontmatter, not on branch topology. A single-repo project that runs many tasks will hit the same flat-index bloat. So they ship in the portable core; only their occasional monorepo-flavored guards (e.g. "regenerate on broadcast conflict") are inert in a single repo, which is harmless.

### Why the monorepo skills are a separate module
`promote-knowledge`, `sync-knowledge`, and `distribute-packages` hardcode a `dev_<app>` / `dev_packages` / `main` branch topology and abort outside it. In a single-repo project there is no second branch to promote to — they would be no-ops or, worse, confusing. Keep them out unless the project actually has that topology.

## Pivots worth knowing (things tried and dropped)

- **Package distribution evolved N-PR "all-or-nothing" → a trunk branch → direct CI auto-merge (gate once at the source).** If you install the monorepo module, start at the mature form (trunk + broadcast), not the N-PR form.
- **The work index went from hand-edited to generated.** Hand-editing caused drift (the reason `work-audit` exists) and constant merge conflicts. Always regenerate; never hand-merge the index.
- **Rules are extended by satellite ADRs, never by rewriting history.** When a new app needed a rule tweak, a new dated ADR was added and the original left intact. ADRs are superseded, not rewritten. Nothing is deleted — history is preserved.
- **ADR filenames are `YYYY-MM-DD_slug.md`,** not numbered — numbering caused renumber churn.
- **Branching split into a seed and an accretion.** The ephemeral-branch discipline + creation gate proved valuable even in a single repo, so it moved into `core/`. Only the multi-app permanent topology (`staging_<app>`/`dev_<app>`, promote/broadcast) stayed in the monorepo module. Both ship one filename (`git_branching_rule.md`); the monorepo variant supersedes the core one when installed.
- **Rules cite the incident that hardened them.** A clause born from a concrete failure carries an inline provenance marker (a `postmortems/` wikilink, an ADR, a cycle id), the same discipline as `file:line` for wiki claims — self-justifying, and safe to prune. See METHODOLOGY §10.1.

- **Model-per-role moved from advice to mechanism.** The recommendation ("use the right model for each phase") existed for months and was *entirely advisory* — prose telling a human to switch models by hand. It was worse than useless: acting on it meant switching mid-session, which discards the prompt cache and re-reads the whole prefix. The fix was not better advice but a different lever — sub-agents with a pinned tier, whose cache is separate — so the session's model never changes. **Advice that costs money to follow is a design bug, not a discipline problem.**
- **`references/` is a convention, not a mechanism — this cost a redesign.** The plan for splitting large rules assumed `references/*.md` was lazy-loaded the way a skill's body is. Investigation showed the opposite: outside a skill directory it is indistinguishable from any path mentioned in prose, and *nothing in the rules directory is auto-loaded at all* — it enters context only because the entry-point says to read it. The **skill body** is the only genuine deferral. The objective survived; the vehicle changed. Verify the mechanism before designing around it.
- **Gate lists were summaries, so they drifted.** Written as a digest of obligations scattered through the body, they fell behind: a sweep found 29 imperative sub-rules living only in the body against 26 items listed. Promoting them by hand would have produced a bigger summary that drifts again. Marker-in-the-body plus a generated list ended the category — same verdict as the work index, one layer up. See METHODOLOGY §6.5.
- **The rules exempted themselves from the citation discipline they impose.** Principle 4 demanded `file:line` "in the wiki or in a plan"; the normative documents themselves carried **one citation across 1,151 lines**. A rule that never points at the code it describes cannot be checked against it — which is exactly how one invariant kept asserting a dead mechanism for two months after the code stopped working that way. Extending the principle to rules is cheap; the check that reports unresolved citations is cheaper.
- **Estimating a refactor by file-level ratio was wrong by 4×.** "The core is ~30% of each rule, so ~70% can move" held at the whole-file level and collapsed at section level: the heavy sections are precisely the ones containing gates. The genuinely movable share was far smaller, and the work was surgery around obligations rather than moving files. **Measure at the granularity you will actually cut at.**

## The cross-team module: what was proven vs. generalized

The **inbound** half (ingesting a partner's docs via `ingest-source`) was used heavily and is solid. The **outbound** half (authoring handoffs to a partner team's LLM) was done repeatedly *by hand* with an emergent-but-consistent shape: a top-of-file "Audience: your team's LLM" line, a self-contained rule ("assume zero access to our repo"), spec-written-inline, stable numbered questions across rounds, and a dual closing ask ("send back a document we can ingest" + "bring a plan-then-execute proposal before touching your code"). The `cross-team-handoff` skill **codifies that proven hand-shape** and standardizes its frontmatter. The heavier ideas it surfaced but that were *never implemented* — a shared machine-readable contract (JSON Schema/OpenAPI), a shared versioned drop repo — are noted in the module README as opt-in escalations, not defaults.

## The intra-team module: the mirror, mostly generalized

`modules/intra-team/` is the deliberate **mirror** of cross-team: same structural spine (addressed docs, stable ask IDs, episodic-message + durable-board split, per-claim tags, dual closing ask), one premise **inverted** — the reader **shares the repo**. That inversion flips the governing rule from *self-contained* to **reference-first** (cite `file:line`/`[[wikilinks]]`, don't re-paste), and turns the confidence tag from a repo-access question into a **claim-state** one (`✅ landed` / `⚠ in-flight` / `🔒 intent`). Unlike cross-team — whose hand-shape was run repeatedly before it became a skill — intra-team is **largely an informed generalization**: the reference-first rule and the claim-state tags are its new, unproven pieces. Adopt the spine; let real multi-agent use prune the rest (the module README §10 says so explicitly).

## A second provenance: the systems / scientific project

The benchmarks, contracts, and dev-environment modules were **not** distilled from the mobile monorepo above — they come from a second production project that ran this same methodology on a **single-repo, systems-level** codebase (a high-performance native/runtime library held to a scientific-evidence bar). There, three disciplines were battle-tested rather than merely generalized:

- **`modules/benchmarks/`** — every quantitative claim had to carry a reproducible page (hypothesis → exact command → dataset → statistics → **verdict**), with refutation treated as a valid result and an explicit anti-p-hacking stance. It is the `⚠ unverified` citation ethos extended to an empirical axis.
- **`modules/contracts/`** — a versioned cross-language ABI was governed as a contract: every change went through an atomic ADR + synchronized multi-artifact PR, with independent `MAJOR.MINOR` versioning and a runtime compatibility check. Generalized here to any versioned cross-boundary contract (public API, DB schema, wire protocol, event schema, FFI ABI).
- **`modules/dev-env/`** — external services (databases, brokers) lived in versioned, health-checked containers with explicit lifecycle modes, so benchmarks and integration tests reproduced across machines and CI.

Unlike the intra-team module (an informed generalization), these three carry real production mileage — on a **different kind of project** than the mobile monorepo, which is exactly why they ship as opt-in modules rather than seed.

## Bottom line for the installing agent

Install `core/`. Ask the interview. Add `modules/monorepo/` only for a real multi-app/multi-package repo with per-app branches. Add `modules/cross-team/` only when a partner team genuinely collaborates through an LLM that does **not** share your repo. Add `modules/intra-team/` only when more than one agent works the same repo and needs to coordinate or hand off. Resist the urge to install everything — the methodology's strength is that it starts small and grows on evidence.
