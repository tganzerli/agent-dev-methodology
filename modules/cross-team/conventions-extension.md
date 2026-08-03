# Conventions extension — cross-team module

> **Installer:** append the section below (everything between the two `⟪…⟫` markers) into
> `{{project}}_wiki/_meta/conventions.md`, as a new top-level section after §4 "Page types".
> Do **not** create a separate file in the target project — these fields belong in the one
> canonical conventions doc so every agent finds them there. Remove the `⟪…⟫` markers when
> pasting.
>
> This extension is only installed when the **cross-team module** is active (INSTALL.md §5).
> It standardizes frontmatter for handoff/response/contract docs — the real-world setup was
> inconsistent here, and this pins the vocabulary.

---

⟪ BEGIN drop-in section — paste into {{project}}_wiki/_meta/conventions.md ⟫

## Cross-team frontmatter (partner-team collaboration)

Docs exchanged with a **partner team** (that works through its own LLM) extend the base frontmatter with the fields below. They apply to pages in `sources/external/` (handoffs and responses) and to the living-contract page in `cross-cutting/`.

```yaml
---
title: ...
type: source                   # source for handoff/response; contract for the living contract
direction: outbound            # outbound (we authored it) | inbound (we received it)
doc_role: handoff              # handoff | response | reply | verification
status: sent                   # HANDOFF lifecycle: sent | answered | resolved | superseded
                               #   (base source/contract status stub|draft|stable|stale still
                               #    applies to non-handoff docs)
external_tickets: []           # partner ticket/issue IDs, e.g. [ABC-1234] — keep greppable
updated: 2026-08-03
sources: []
code_refs: []                  # OUR files only; on a handoff these are PROVENANCE-only
related: []
---
```

### Field meanings

| Field | Applies to | Values | Meaning |
|---|---|---|---|
| `direction` | all cross-team docs | `outbound \| inbound` | Did we author it (`outbound`) or receive it (`inbound`)? |
| `doc_role` | all cross-team docs | `handoff \| response \| reply \| verification` | The document's role in the exchange. `handoff` = outbound spec+questions; `response` = the partner's answer; `reply` = a short follow-up; `verification` = a doc confirming a deployed/validated behavior. |
| `status` (handoff) | `doc_role: handoff` | `sent \| answered \| resolved \| superseded` | Lifecycle of an outbound handoff: `sent` → `answered` (a response landed) → `resolved` (all blocking questions closed) → `superseded` (a later handoff replaces it). For non-handoff docs, keep the base `stub\|draft\|stable\|stale`. |
| `external_tickets` | all cross-team docs | list of strings | Partner ticket/issue IDs referenced, so the exchange is **greppable** from your repo (`grep -rn ABC-1234 {{project}}_wiki/`). |

### Provenance tags (in the body, per claim)

Cross-team docs tag **each factual claim** by confidence, because you cannot audit the partner's repo:

| Tag | Meaning |
|---|---|
| `✅` | **verified-in-code** — confirmed against source (yours, or the partner's per their assertion). |
| `⚠` | **not-auditable / needs-confirmation** — asserted but not audited, or runtime-only. Stays unconfirmed until validated. |

This is stricter than the base `⚠ unverified` marker: base `⚠ unverified` means "no citation yet"; the cross-team `⚠` means "asserted by a party we cannot audit". A claim that touches **your** code must still get a `file:line` citation on your side, tagged `✅`.

### Stable question IDs

Open questions in a handoff use **stable IDs** (`Q1`, `Q2`, …) that **never change across rounds**. Follow-up rounds append new IDs; prior ones are re-statused (`open → answered → resolved`) or `superseded` (with a pointer), never renumbered or deleted. See the `cross-team-handoff` skill.

### Where these docs live
- Handoffs / responses → `sources/external/YYYY-MM-DD_slug.md`; verbatim payloads → `sources/external/_raw/`; binary/sample files → `sources/external/artifacts/`.
- Living contract → `cross-cutting/<subject>-contract.md` (`type: contract`).

⟪ END drop-in section ⟫
