---
name: cross-team-handoff
description: Author or advance a bidirectional LLM↔LLM exchange with a partner team (e.g. backend). Covers three flows — (1) author an OUTBOUND handoff (spec + stable numbered questions + dual closing ask) to the partner team's LLM, (2) ingest an INBOUND response with per-claim provenance tags, (3) maintain the living-contract page in cross-cutting/. Use when the human asks to write a handoff to the partner team, ingest their reply, or update the shared contract. Requires the cross-team module.
argument-hint: "[outbound <slug> | inbound <path-or-url> | contract <subject>]"
disable-model-invocation: true
---

# Cross-team handoff

Bidirectional collaboration with a **partner team** (e.g. backend) that works through **its own LLM agent**. This skill codifies the proven handoff / response / living-contract pattern. See `modules/cross-team/README.md` for the rationale.

> **Manual-only.** This skill has side effects (writes docs the partner will consume, mutates the living contract) and depends on a human gate. Run it **only** on explicit human request — never auto-invoke.

## Argument

`$ARGUMENTS` selects the flow:
- `outbound <slug>` → author a new handoff (Flow A).
- `inbound <path-or-url>` → ingest a partner response (Flow B).
- `contract <subject>` → create/update the living-contract page (Flow C).

If absent, ask which of the three the human wants.

## Prerequisites (all flows)

- The cross-team module is installed and `{{project}}_wiki/_meta/conventions.md` carries the extended frontmatter (`direction`, `doc_role`, handoff `status`, `external_tickets`, provenance tags).
- Authored prose is in **{{KNOWLEDGE_LANG}}**; verbatim `_raw/` payloads and anything the partner LLM must consume in a specific language stay in that language.

---

## Flow A — author an OUTBOUND handoff

File: `{{project}}_wiki/sources/external/{YYYY-MM-DD}_{slug}.md`. Template: `_handoff_templates/handoff.md`.

### A1. Frame the audience and self-containment
- Set `Audience:` to **the partner team's LLM** ("the backend team's coding agent"), and `Author:` to your side (agent + gating human).
- Adopt the **self-contained rule**: assume the reader has **zero access to your repo**. Everything it needs is in this document.

### A2. Write the sections (see template order)
1. **Context** — why this exchange exists; the goal in plain terms.
2. **What we already have** — current state on your side. Here `file:line` citations are allowed **but marked provenance-only** ("for our audit trail — not required reading for you"). Never make the partner depend on a file they cannot open.
3. **What we need from you** — the spec, **written implementable-inline**: paste the *full* algorithm / field list / state machine the partner must build. Do not reference "our implementation"; reproduce it. Long verbatim blocks (exact JSON, a byte-precise routine) go to `sources/external/_raw/` and are linked; sample/binary files to `artifacts/`.
4. **Open questions** — a **stable numbered table** (§A3).
5. **Closing asks** — the **dual ask** (§A4).

### A3. Stable numbered questions (round-threading)
- Each question has a **stable ID** (`Q1`, `Q2`, …) that **never changes across rounds**.
- Each carries a **blocking flag** (🔴 blocking / ⚪ non-blocking) and a **status** (`open | answered | resolved | superseded`).
- **On a follow-up round:** do **not** renumber. Append new questions (`Q7`, `Q8`, …). Update the status of prior ones (`answered`/`resolved`) as the partner responds. If a question is invalidated, mark it `superseded` and point to the one that replaces it — never delete it. This keeps "the answer to Q3" stable across the whole thread.
- Bump the handoff `status` frontmatter: `sent` when delivered → `answered` once a response lands → `resolved` when all blocking questions are closed → `superseded` if a later handoff replaces it.

### A4. Dual closing ask (mandatory)
Every handoff ends with two asks to the partner LLM:
1. **Send back a return document we can ingest** — a response in the same shape, so Flow B can `ingest-source` it cleanly (answers keyed to the `Q` IDs, one provenance tag per claim).
2. **Bring a plan-then-execute proposal before touching your code** — propagate this methodology's gate: the partner should produce an approved plan before implementing. State it explicitly.

### A5. Register and log
- Frontmatter: `type: source`, `direction: outbound`, `doc_role: handoff`, `status: sent`, `external_tickets: [...]` (partner ticket IDs, greppable).
- Add the doc to `{{project}}_wiki/_meta/index.md` under Sources → External.
- If this handoff concerns a durable interface, ensure a living-contract page exists (Flow C) and cross-link it.
- Append to `{{project}}_wiki/_meta/log.md`: `## [YYYY-MM-DD] handoff-out | {slug} | N questions (M blocking)`.
- **Human gate:** show the full draft; the human approves before it is sent to the partner.

---

## Flow B — ingest an INBOUND response

File: `{{project}}_wiki/sources/external/{YYYY-MM-DD}_{slug}-response.md` (or the partner's own doc, ingested). Template: `_handoff_templates/response.md`.

### B1. Collect and summarize
- Local file → read directly. URL → use the `defuddle` skill for clean markdown.
- Verbatim payloads the partner sent (exact JSON, logs) → `sources/external/_raw/` or `artifacts/`; **do not** inline them in the summary.

### B2. Per-claim provenance tags
Every factual claim the partner makes is tagged:
- **✅ verified-in-their-code** — the partner asserts they confirmed it against their own source.
- **⚠ not-auditable / needs-confirmation** — asserted but not audited, or something only observable at runtime. **You cannot open their repo**, so treat `⚠` claims as unconfirmed until a validation on *your* side (or a later round) settles them.
- Where a claim touches **your** code, re-check it on the main thread and add a `file:line` citation to your side.

### B3. Thread the answers back to the questions
- Key each answer to its **stable `Q` ID** from the originating handoff.
- In the originating handoff, flip each answered question's status (`answered`/`resolved`). If an answer invalidates an earlier assumption, open a new `Q` in the next round rather than editing the old one.
- Update the originating handoff's frontmatter `status` (`answered` → `resolved` when no blocking question remains).

### B4. Feed the living contract
- Anything the response *changes or confirms* about the interface goes into the living-contract page (Flow C) as a dated `⚠ UPDATE` block, and the current-state table is amended.
- Distinguish **proposal** (something one side suggested) from **implemented-and-validated** (deployed and confirmed by both sides).

### B5. Register and log
- Frontmatter: `type: source`, `direction: inbound`, `doc_role: response`, `external_tickets: [...]`.
- Update `{{project}}_wiki/_meta/index.md`.
- Append to `{{project}}_wiki/_meta/log.md`: `## [YYYY-MM-DD] handoff-in | {slug} | K claims (P verified, U needs-confirmation)`.
- **Human gate:** discuss takeaways (3–5 bullets) before mutating any knowledge/contract page.

---

## Flow C — maintain the LIVING-CONTRACT page

File: `{{project}}_wiki/cross-cutting/{subject}-contract.md`. Template: `_handoff_templates/living-contract.md`. Frontmatter `type: contract`.

### C1. Current-state table (caps growth)
- Maintain a single **current-state table** = the present truth of every field / endpoint / message. **Overwrite in place** as things change — this is what prevents unbounded growth. Do not accumulate stale rows here.
- Address the page to the partner LLM (an `Audience:` line), same self-contained discipline.

### C2. Append-only update history
- Every change is recorded as a dated block:
  ```
  ### ⚠ UPDATE 2026-08-03 — <what changed>
  - Was: ...
  - Now: ...
  - Why / source: [[sources/external/2026-08-03_slug]] · Qk
  - State: proposal | implemented-and-validated
  ```
- **Never rewrite history blocks.** The current-state table is "now"; the history is "how we got here".

### C3. Proposal vs. implemented-and-validated
- Tag every current-state row and every update: is it a **proposal** (sent, not agreed/deployed) or **implemented-and-validated** (live and confirmed by both sides)? Never let a proposal read as reality.

### C4. Environment-state sub-table (deployable changes)
For anything deployable, keep a grid so "is it live?" has one answer:

| Change | Code branch | DEV | PROD |
|---|---|---|---|
| <field/endpoint> | merged / in-review / — | ✅ / ⚠ / — | ✅ / ⚠ / — |

A change on a branch but not in PROD is a **different fact** from one live in PROD — the table makes that explicit.

### C5. Register and log
- Ensure the contract page is in `{{project}}_wiki/_meta/index.md` and linked from the relevant handoff/response docs (`related[]`).
- Append to `{{project}}_wiki/_meta/log.md`: `## [YYYY-MM-DD] contract-update | {subject} | <one line>`.

---

## Anti-patterns

- ❌ Referencing your own `file:line` as **required** reading for the partner — they cannot open it. Citations to your code are provenance-only; the partner's needs must be stated inline.
- ❌ Renumbering questions between rounds. IDs are stable; append and re-status, never renumber or delete.
- ❌ Dropping the dual closing ask — always request (a) a return doc to ingest and (b) a plan-before-code from the partner.
- ❌ Ingesting a response without per-claim `✅`/`⚠` tags, or treating a `⚠` claim as confirmed.
- ❌ Letting the living-contract current-state table grow unbounded (append everything). Overwrite the table; append only the history.
- ❌ Mixing a **proposal** with an **implemented-and-validated** fact in the contract.
- ❌ Auto-running this skill. It is human-gated (`disable-model-invocation: true`).
- ❌ Copying verbatim payloads into the summary body instead of `_raw/` / `artifacts/`.
