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

> ⚠️ **The template is the full shape, not a skeleton.** Filling in only context + spec + questions produces a document that reads like a ticket and gets answered like one: partially, and without the facts you need to write your own code. Every section in `A2` earned its place by closing an observed failure. **Scale the sections to the ask; do not drop them.** A one-question handoff still names its target system, still asks for a return document item by item, and still carries a contact — those are two lines each, not two pages.

### A1. Frame the reader, the target, and self-containment
- Open with a **`From:` / `To:` block**. `To:` names the partner team **and the concrete system that owns the change** — the service, module, or repo, not just "the backend team's LLM". Without it, the partner's agent guesses which service is in scope and specs the change in the wrong place. Where useful, say where it is *not* ("this is not in the admin service"). `From:` names your side with its concrete artifact (app/service, repo).
- Adopt the **self-contained rule**: assume the reader has **zero access to your repo**. Everything it needs is in this document.
- State the **purpose of the document** as an enumerated (1)(2)(3) — current state, what you depend on them for, the return document you want — and **point forward to the asks**. The partner should know what is expected of them before reading the spec.
- If your side is gated on their answer, **say so plainly** ("we will not write code until the contract comes back"). It sets the priority honestly and explains why you are asking for so much precision.

### A2. Write the sections (see template order)
1. **Context (enough to act)** — what the product/system *is* for a reader who has never seen it, then what you are building and the requirements driving the ask. Include the invariants that govern the exchange (auth, addressing, tenancy). The partner needs enough to judge whether your proposal is *reasonable*, not just to implement it literally.
2. **What is already done on our side** — what is implemented, and what is **validated, where, and when** (environment, date, real observed values) versus merely written. Citations are allowed **but marked provenance-only** ("for our audit trail — not required reading for you"). Never make the partner depend on a file they cannot open. Add a **coverage table** when the ask is "we have most of it, we need the rest". If a volume, limit, or cost motivates the ask, **put the number in** — "it does not scale" is an opinion, a measured cost is an argument.
3. **What we depend on you for** — one lettered subsection per dependency (3.A, 3.B, …), each with a **state marker in the heading** (`PENDING (blocking)` / `PARTIAL` / `ask = do not regress`) and an explicit **Where:** naming the owning system. The spec is **written implementable-inline**: paste the *full* algorithm / parameter table / field list / state machine. Do not reference "our implementation"; reproduce it. Add the error table in their existing convention, a **concrete request/response example**, and an **E2E acceptance** line per dependency. Long verbatim blocks go to `sources/external/_raw/` and are linked; sample/binary files to `artifacts/`.
   - When the partner **already receives** what you are asking them to expose, show them **where it sits on their side** — payload position, field name, ingestion point. It turns "add a feature" into "expose what you already have".
   - **Flag traps inline** where they matter: non-alphabetical array order, a flag whose name inverts its meaning, a unit already converted. A trap named here costs a sentence; discovered later it costs a round.
   - Include a final subsection for the part that **already works**, with the ask "tell us before it changes". Cheapest section in the document, prevents the most expensive surprise.
4. **Pending summary** — a scannable `- [ ]` checklist, one line per dependency plus the two asks. Multi-item handoffs come back partially answered without it.
5. **Open questions** — a **stable numbered table** (§A3). Ask for **schema and possible values**, not yes/no, whenever the answer ends up in your code.
6. **Ask 1 — return document, item by item** (§A4).
7. **Ask 2 — plan-then-execute, with its four components** (§A4).
8. **Appendices** — *conditional*: include when the partner must **confirm or map** a field list, enum, or schema against their own. State that purpose to them explicitly. Add a **silent-failure-modes** appendix listing behaviors of your client that fail with no visible error — it is what turns "we'll expose the fields" into "we'll expose them with exactly these names".
9. **Contact** — a named human, an email, and the artifact identification (repo, branch, version). Without it the reply goes to whoever last spoke, or nowhere. Close with one line on what the exchange unblocks.

### A3. Stable numbered questions (round-threading)
- Each question has a **stable ID** (`Q1`, `Q2`, …) that **never changes across rounds**.
- Each carries a **blocking flag** (🔴 blocking / ⚪ non-blocking) and a **status** (`open | answered | resolved | superseded`).
- **On a follow-up round:** do **not** renumber. Append new questions (`Q7`, `Q8`, …). Update the status of prior ones (`answered`/`resolved`) as the partner responds. If a question is invalidated, mark it `superseded` and point to the one that replaces it — never delete it. This keeps "the answer to Q3" stable across the whole thread.
- Bump the handoff `status` frontmatter: `sent` when delivered → `answered` once a response lands → `resolved` when all blocking questions are closed → `superseded` if a later handoff replaces it.
- **Revising a round you already sent** (expanding the wording, adding context) is allowed and does **not** license renumbering. Rewrite the body freely; keep every `Q` ID and its meaning. Add a `R{n} (revised)` line to the round log saying **explicitly whether the questions changed** — otherwise the partner cannot tell whether work already started must be redone.

### A4. The two closing asks (mandatory)
Every handoff ends with two asks to the partner LLM. Both are sections of their own, not sentences.

**Ask 1 — the return document, itemized.** A generic "please reply" returns a reply that omits exactly what unblocks you, and costs a full round to fix. Enumerate what the document must contain:
1. One numbered item **per dependency** from §3, naming the specific facts you need (final names, exact semantics, interactions, error codes, edge behavior).
2. The **updated contract**: field-by-field (name, type, nullability) including anything new, plus **one real example** — and say that example becomes your fixture.
3. **How to reach it**: URL/base per environment, and any auth or limit difference from what you described.
4. **Versions / environments**: what is in **DEV** vs **PROD** today, **item by item**. A change merged to a branch is a *different fact* from a change deployed; ask them to distinguish, or you will validate against an environment that does not have it.
5. **Their ticket IDs** per item, for tracking on both sides.
6. Repeat the **self-contained + schema-precise** requirement back to them, plus: answers **keyed to the `Q` IDs**, one **provenance tag per claim** (`✅` verified in their code / `⚠` asserted-not-audited). This is what lets Flow B ingest it cleanly.

**Ask 2 — plan-then-execute.** Propagate this methodology's gate: the partner produces an approved plan before implementing. Spell out the four components you expect in it — **what** changes (before → after), **why** (which item motivates it, risk of not doing it), **impact and compatibility** (breaks current consumers? affects stored data?), and **validation** (how they confirm, including the E2E). Ask for the ticket ID if they open one.

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

- ❌ **Shipping the skeleton.** Filling in only context + spec + questions and calling it a handoff. The template is the full shape — scale the sections down for a small ask, but do not drop them.
- ❌ Addressing the document to "the partner team's LLM" **without naming the concrete system** that owns the change. The partner's agent then guesses the target and specs it in the wrong service.
- ❌ Diving into the feature with **no project context**. A partner who cannot judge whether your proposal is reasonable will implement it literally, including the parts that are wrong.
- ❌ Listing dependencies **without a state marker** — "still pending" and "already works, do not break it" read as the same request.
- ❌ A **generic** "send us a return document". Itemize it, including *what is in DEV vs PROD today, per item*; otherwise the reply omits exactly what unblocks you.
- ❌ Treating "merged" as "deployed" — or letting the partner do so. Always ask for the environment split.
- ❌ Omitting the **contact** section. The reply then goes to whoever last spoke, or nowhere.
- ❌ Knowing a **counter-intuitive mapping** (array order that is not alphabetical, an inverted flag, a pre-converted unit) and not flagging it inline where it matters.
- ❌ Referencing your own `file:line` as **required** reading for the partner — they cannot open it. Citations to your code are provenance-only; the partner's needs must be stated inline.
- ❌ Renumbering questions between rounds. IDs are stable; append and re-status, never renumber or delete — **including when you revise and resend a round**.
- ❌ Dropping the dual closing ask — always request (a) a return doc to ingest and (b) a plan-before-code from the partner.
- ❌ Ingesting a response without per-claim `✅`/`⚠` tags, or treating a `⚠` claim as confirmed.
- ❌ Letting the living-contract current-state table grow unbounded (append everything). Overwrite the table; append only the history.
- ❌ Mixing a **proposal** with an **implemented-and-validated** fact in the contract.
- ❌ Auto-running this skill. It is human-gated (`disable-model-invocation: true`).
- ❌ Copying verbatim payloads into the summary body instead of `_raw/` / `artifacts/`.
