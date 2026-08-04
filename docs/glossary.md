# Glossary

| Term | Meaning |
|---|---|
| **Trio** | The three bound artifacts of one piece of work: **task** (human request), **plan** (LLM analysis, human-gated), **execution** (live log). Bound by a shared `work_id`. |
| **`work_id`** | Unique work identifier, `YYYY-MM-DD_slug` (kebab-case). Names the trio files and, in a monorepo, the ephemeral branch. |
| **Vault** | The Obsidian folder `{{project}}_wiki/`. Holds both knowledge pages and (inside `work/`) the trios, so the graph links work ↔ knowledge. |
| **Knowledge page** | Living, thematic memory — the distilled current state of some subject. Answers "what do we know about X today". Subject to `stale`. |
| **Execution** | Historical log — chronological, immutable by design, never `stale`, archivable by quarter. Answers "when/how was this done". |
| **`file:line` citation** | Every technical claim in a plan or wiki page points to its source: `file.dart:42`. Unanchored claims are marked `⚠ unverified`. |
| **`⚠ unverified`** | Marker on a claim that lacks a verifiable citation, until someone anchors it. |
| **Pre-plan analyses (§4.2.5)** | Optional triage before the plan: decompose into independent questions, dispatch parallel agents, synthesize findings (with citations) into the plan's first section. |
| **Model recommendation (per role)** | The LLM advises which model to use for task-refinement / each analysis / plan-writing — contextually, never from a fixed role→model table. |
| **`/wiki-sync`** | Manual, human-gated step that propagates a finished execution into knowledge pages. |
| **Knowledge layer** | The set of paths whose timeline is canonical in `main` (monorepo module): `.agents/`, `.claude/skills/`, wiki knowledge pages, entry-points. |
| **Promote / sync knowledge** | Monorepo skills: `promote-knowledge` pushes knowledge from a per-app branch up to `main`; `sync-knowledge` pulls `main`'s knowledge down. |
| **Broadcast** | Monorepo CI flow that propagates `main`'s knowledge (and package changes) to per-app branches automatically. |
| **Living-contract page** | Cross-team module: a `cross-cutting/` page addressed to a partner team's LLM, holding the current-state contract plus an append-only update history. |
| **Handoff / response** | Cross-team module doc roles: an outbound spec/questions doc (handoff) and its inbound answer (response), threaded across rounds. |
| **Intra-team messaging** | Optional module: agent↔agent coordination **inside one repo** (notes / requests / responses / handoffs / conflicts + a coordination board). The mirror of cross-team — **reference-first** (the reader shares the repo), not self-contained. Docs live in `work/relay/`. |
| **Coordination board** | Intra-team module: the durable `work/relay/_board.md` page holding active scope locks + agreements between agents, with an append-only history. The intra-team analogue of the living-contract page. |
| **Claim-state tag** | Intra-team marker tagging a claim by **visibility/state**, not repo access: `✅ landed` (committed, carries a `file:line`) · `⚠ in-flight` (author's working tree / unmerged branch — not visible to the reader yet) · `🔒 intent` (planned, not started). |
| **Scope lock** | A **social** (not OS-enforced) signal on the coordination board that one agent owns a scope right now, so a second agent avoids clobbering it. |
| **Accretion** | A methodology feature added later in response to a specific scaling pain (see `design-rationale.md`), as opposed to the day-one seed. |
| **Skill** | An Agent Skills unit (`.claude/skills/<name>/SKILL.md`) encapsulating a repeatable flow or background knowledge. |
| **Adapter** | A thin per-agent entry-point (`.agents/llm/<agent>.md` + root stub) pointing at the canonical methodology. |
