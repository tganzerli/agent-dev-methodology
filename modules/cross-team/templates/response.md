<!--
  Installs as: {{project}}_wiki/sources/external/_handoff_templates/response.md
  See INSTALL.md §5 and modules/cross-team/README.md.

  A RESPONSE is an INBOUND document: the partner team's LLM answered a handoff,
  and your side ingests it here. Copy to
  {{project}}_wiki/sources/external/{YYYY-MM-DD}_{slug}-response.md and fill {...}.
  Do NOT de-template `{...}` — those are per-doc fill-ins.

  Verbatim payloads the partner sent go under .../_raw/ or .../artifacts/, never
  inlined in the summary. Authored prose is in {{KNOWLEDGE_LANG}}.
-->
---
title: {Response — human title}
type: source
direction: inbound
doc_role: response
scope:
  area: []
status: stable                 # source-page status (stub|draft|stable|stale)
updated: {YYYY-MM-DD}
summary: One sentence — what the partner answered. Feeds the catalog.
external_tickets: []           # partner ticket/issue IDs referenced
sources:
  - sources/external/{YYYY-MM-DD}_{slug}.md   # the originating handoff
code_refs: []                  # OUR files re-checked while ingesting (claims touching our code)
related: []                    # e.g. the living-contract page
---

# {Response title}

**Direction:** inbound (partner team's LLM → us).
**Answers handoff:** [[sources/external/{YYYY-MM-DD}_{slug}]] (round {N}).

> **Provenance legend.** Every claim carries a tag:
> - **✅ verified-in-their-code** — the partner states they confirmed it against their own source.
> - **⚠ not-auditable / needs-confirmation** — asserted but not audited, or only observable at runtime. **We cannot open their repo**, so a `⚠` claim stays unconfirmed until validated on our side or in a later round.

## 1. Summary

> 3–5 bullets of what the partner delivered. Discuss with the human before mutating any knowledge/contract page.

## 2. Answers (keyed to question IDs)

> One block per answered question. Reuse the **stable Q IDs** from the handoff — never renumber.

### Q1 — {restate the question} · 🔴
- **Answer:** {partner's answer}. **✅ verified-in-their-code** — {basis}.
- **Our check:** where it touches our code, re-verified. 📎 `lib/.../foo.dart:42`.
- **New handoff status for Q1:** `resolved`.

### Q2 — {restate} · ⚪
- **Answer:** {answer}. **⚠ not-auditable** — runtime-only; needs a validation run on our side before we rely on it.
- **New handoff status for Q2:** `answered` (pending our validation).

### Q3 — {restate} · 🔴
- **Answer:** {partial}. Raises a follow-up → opened **Q7** in the next round (do not edit Q3's meaning).
- **New handoff status for Q3:** `answered`.

## 3. New / changed contract facts

> What this response changes or confirms about the interface. Each feeds a dated `⚠ UPDATE` block in the living-contract page. Distinguish clearly:
>
> - **Proposal** — the partner proposed it; not yet agreed/deployed.
> - **Implemented-and-validated** — deployed and confirmed by both sides.

- {fact} — **implemented-and-validated** → contract: [[cross-cutting/{subject}-contract]].
- {fact} — **proposal** → awaiting agreement.

## 4. Verbatim material

> Link only — never inline.

- Exact payload the partner sent: [`_raw/{slug}-response.json`](_raw/{slug}-response.json).
- Sample capture: [`artifacts/{slug}-response-sample.log`](artifacts/{slug}-response-sample.log).

## 5. Follow-ups / next round

- Open questions carried forward: {Q…}.
- New questions opened this round: {Q7, …} — go into the next outbound handoff.
