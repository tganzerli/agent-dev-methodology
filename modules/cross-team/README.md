# Cross-team module — bidirectional LLM↔LLM collaboration

> **OPTIONAL module.** Install only when a **partner team** (e.g. backend, firmware, another product squad) collaborates with your team **through their own LLM agent**, exchanging specs, contracts, and questions as markdown documents. If external docs only flow *inward* and you never author outbound specs, you do **not** need this module — the core `ingest-source` skill already covers one-directional ingest.

## 1. What this adds

| Artifact | Path | Purpose |
|---|---|---|
| `cross-team-handoff` skill | `.claude/skills/cross-team-handoff/SKILL.md` | Author an **outbound handoff**, ingest an **inbound response**, and maintain the **living-contract** page. Human-gated (`disable-model-invocation: true`). |
| Handoff template | `{{project}}_wiki/sources/external/_handoff_templates/handoff.md` | Outbound spec + stable numbered questions + dual closing ask. |
| Response template | `{{project}}_wiki/sources/external/_handoff_templates/response.md` | Inbound answer keyed to question IDs, per-claim provenance tags. |
| Living-contract template | `{{project}}_wiki/sources/external/_handoff_templates/living-contract.md` | A `cross-cutting/` page holding the current contract state + append-only history. |
| Frontmatter extension | appended into `{{project}}_wiki/_meta/conventions.md` | New fields: `direction`, `doc_role`, handoff `status`, `external_tickets`, provenance tags. See `conventions-extension.md`. |

It **complements** the core, it does not replace it. The core `ingest-source` skill remains the inbound-only path for external docs when there is **no** partner-LLM collaboration (a one-off PDF, an article, a spec you will never answer). This module is what you reach for when the exchange is a **conversation between two LLMs** across rounds.

## 2. Where cross-team docs live

```
{{project}}_wiki/
├── sources/
│   └── external/
│       ├── YYYY-MM-DD_slug.md        ← each handoff / response doc (summary-first, self-contained)
│       ├── _raw/                     ← verbatim text/JSON that must NOT be summarized (paste as-is)
│       ├── artifacts/                ← binary / sample files (logs, captures, sample payloads)
│       └── _handoff_templates/       ← the three templates this module installs
└── cross-cutting/
    └── <subject>-contract.md         ← the living-contract page (type: contract)
```

- **`sources/external/YYYY-MM-DD_slug.md`** — one file per exchanged document (both directions). Summary-first, like any source page, **but self-contained** (§3).
- **`_raw/`** — when text must survive verbatim (a JSON payload, an exact error string, an algorithm the partner must implement byte-for-byte), drop it here and link to it. The "summary, don't copy" rule of `ingest-source` yields here: a contract exchange sometimes *needs* the literal bytes. Keep raw text out of the summary body; point at `_raw/`.
- **`artifacts/`** — non-text or sample files (a captured log, a sample device dump, a screenshot). Referenced from the doc, never inlined.
- **`cross-cutting/<subject>-contract.md`** — the durable **living contract** (§4), which outlives any single round.

## 3. The proven pattern

This module codifies a hand-shape that was run repeatedly by hand before it was a skill. Five rules:

1. **Every handoff opens with `Audience:` and `Author:` lines.** `Audience:` names **the partner team's LLM** as the intended reader ("the backend team's coding agent"). `Author:` names who wrote it (your team's agent + the human who gated it). The reader is another LLM — write for it.

2. **Self-contained rule.** The document must assume the reader's LLM has **zero access to your repo**. *Everything it needs is in the document.* Provenance citations back to your own code (`file:line`) are included **as provenance only** — labelled so, and explicitly *not required reading* for the partner. If a claim matters to the partner, state it inline; don't make them chase a file they can't open.

3. **Spec written implementable-inline.** When you need the partner to build something, paste the **full** thing — the entire algorithm, the complete field list, the exact state machine — into the doc. Do not reference "our implementation"; reproduce what they must reproduce.

4. **Stable numbered questions.** Open questions get **stable IDs** (`Q1`, `Q2`, …) that **do not change across rounds**. Each carries a **blocking flag** (🔴 blocking / ⚪ non-blocking) and a **status** (`open | answered | resolved | superseded`). New rounds append `Q7`, `Q8`… and never renumber the old ones — so "the answer to Q3" means the same thing in round 4 as in round 1.

5. **Dual closing ask.** Every handoff closes with two asks to the partner LLM:
   - **(a) Send back a return document we can ingest** — a response doc in the same shape, so your side can `ingest-source` it cleanly.
   - **(b) Bring a plan-then-execute proposal before touching your code** — i.e. propagate this methodology's core gate to the partner: no code before an approved plan.

A **response** (inbound) is ingested with a **per-claim provenance tag**: `✅` verified-in-their-code vs `⚠` not-auditable / needs-confirmation. Your side cannot audit the partner's repo, so each claim they make is tagged by *their* confidence and re-checked on your side where it touches your code.

A **living-contract** page (§4) is the running source of truth for the interface, addressed to the partner LLM, capped against unbounded growth by a maintained **current-state table** plus an **append-only update history** of dated `⚠ UPDATE` blocks. For anything deployable, it carries an **environment-state sub-table** (code branch × DEV × PROD) so "is this live?" has one answer.

## 4. The living contract

Handoffs and responses are *episodic* (a round). The **living contract** is *durable* — it is where the current, agreed interface lives so nobody re-derives it from a thread of ten handoffs.

- **Current-state table** — the present truth of every field/endpoint/message. Overwritten in place as things change (this is what caps growth).
- **Append-only history** — dated `⚠ UPDATE YYYY-MM-DD` blocks recording *what changed and why*. Never rewritten; the current-state table is the "now", the history is the "how we got here".
- **Proposal vs. implemented-and-validated** — mark each item inline. A proposal your side sent is not the same as a behavior the partner deployed and both sides validated. Do not let a proposal masquerade as reality.
- **Environment-state sub-table** — for deployable changes, a `code-branch | DEV | PROD` grid. A change merged to the partner's branch but not yet in PROD is a different fact from one live in PROD.

## 5. Frontmatter this module standardizes

The real-world setup was inconsistent here; this module fixes the vocabulary. Append these to `{{project}}_wiki/_meta/conventions.md` (drop-in section in `conventions-extension.md`):

| Field | Values | Meaning |
|---|---|---|
| `direction` | `outbound \| inbound` | Did we author it (outbound) or receive it (inbound)? |
| `doc_role` | `handoff \| response \| reply \| verification` | The document's role in the exchange. |
| `status` (handoff) | `sent \| answered \| resolved \| superseded` | Lifecycle of an outbound handoff. |
| `external_tickets` | `[]` | Partner ticket/issue IDs referenced, so they are **greppable** from your repo. |
| provenance tags | `✅` / `⚠` (per claim, in body) | `✅` verified-in-code · `⚠` not-auditable / needs-confirmation. |

## 6. Install

See `INSTALL.md` §5. In short:

1. Copy `skills/cross-team-handoff/` → `.claude/skills/cross-team-handoff/`.
2. Copy `templates/*` → `{{project}}_wiki/sources/external/_handoff_templates/`.
3. Append `conventions-extension.md` into `{{project}}_wiki/_meta/conventions.md`.
4. Register `cross-team-handoff` in `.claude/skills/_index.md` (mark it manual-only).
5. Create `{{project}}_wiki/sources/external/_raw/` and `.../artifacts/` (empty).

Authored content (the handoff/response/contract bodies) is written in **{{KNOWLEDGE_LANG}}**, like the rest of the wiki — **except** verbatim `_raw/` payloads and any text the partner LLM must consume in a specific language, which stay in whatever language the interface requires.

## 7. Opt-in escalations (NOT default)

The pattern above is the **proven core** — the battle-tested handoff / response / living-contract shape. Two heavier ideas were surfaced during real use but **never implemented**; install them only if a concrete pain justifies the added machinery:

- **Shared machine-readable contract (JSON Schema / OpenAPI / protobuf).** Instead of prose + `_raw/` payloads, both teams share a single schema file as the source of truth, validated in CI on both sides. *Escalate when:* the interface is large and drifts silently, and prose contracts keep getting out of sync with the wire format. Until then, the living-contract page's current-state table is enough.
- **Shared versioned drop repo.** A third git repo both teams push contract docs to, versioned and tagged, instead of exchanging files ad hoc. *Escalate when:* the volume of exchanged docs outgrows manual hand-off and you need history/tags/access-control on the exchange itself. Until then, `sources/external/` + `external_tickets` greppability suffices.

Both are **not defaults**. Start with the proven core; add an escalation only when its triggering pain actually appears (the seed-vs-accretion principle — see `docs/design-rationale.md`).
