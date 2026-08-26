<!--
  Installs as: {{project}}_wiki/sources/external/_handoff_templates/handoff.md
  See INSTALL.md §5 and modules/cross-team/README.md.

  A HANDOFF is an OUTBOUND document your team's LLM authors FOR the partner
  team's LLM. Copy this file to {{project}}_wiki/sources/external/{YYYY-MM-DD}_{slug}.md
  and fill the {...} per-doc placeholders. Do NOT de-template the `{...}` below —
  those are per-handoff fill-ins, distinct from the kit-wide `{{...}}` resolved at install.

  ─────────────────────────────────────────────────────────────────────────────
  THIS TEMPLATE IS THE FULL SHAPE, NOT A SKELETON.

  A handoff that only carries context + spec + questions reads as a ticket, and
  it gets answered like a ticket: partially, and without the information you
  need to write your own code. The sections below exist because each one closed
  a specific failure observed in real exchanges:

    · No named target system  → the partner's LLM guesses which service owns the
                                change and specs it in the wrong place.
    · No project context      → the partner cannot judge whether your proposal is
                                reasonable, so they implement it literally.
    · No state per dependency → "pending" and "already works, don't break it"
                                get treated as the same kind of request.
    · No checklist            → multi-item asks come back partially answered.
    · Generic "send a reply"  → the reply omits exactly what unblocks you, and
                                you burn a whole round asking for it.
    · No DEV-vs-PROD split    → "it's done" means merged, and you validate against
                                an environment that does not have it.
    · No appendix to confirm  → field names diverge silently and surface months
                                later.
    · No contact              → the reply goes to whoever last spoke, or nowhere.

  SCALE, don't skip. Sections 1–7 and 9 are REQUIRED at any size (a one-question
  handoff still needs a target system, a return-doc ask, and a contact — they are
  just short). Section 8 (appendices) is conditional: include it when the partner
  must confirm or map a field list, an enum, or a schema against their own.
  ─────────────────────────────────────────────────────────────────────────────

  Authored prose is in {{KNOWLEDGE_LANG}}. Verbatim payloads the partner must
  consume byte-for-byte go under {{project}}_wiki/sources/external/_raw/ and are
  linked; sample/binary files under .../artifacts/.
-->
---
title: {Handoff — human title}
type: source
direction: outbound
doc_role: handoff
scope:
  area: []                     # single-repo: free text. Monorepo: apps/packages.
status: sent                   # sent | answered | resolved | superseded
updated: {YYYY-MM-DD}
summary: One sentence — what we are asking the partner team for. Feeds the catalog.
external_tickets: []           # partner ticket/issue IDs — keep greppable, e.g. [ABC-1234]
sources: []
code_refs: []                  # our files cited for PROVENANCE only (partner cannot open them)
related: []                    # wikilinks — e.g. the living-contract page
---

# {Handoff title — name the interface and the ask, not just the topic}

> **From:** {your team, with the concrete artifact: app/service name, repo/monorepo}.
> **To:** {partner team} responsible for **{the CONCRETE system that owns the change — service/module/repo name}**, and the AI assistant supporting it.
>
> **How to read this document — IMPORTANT.** It is **100% self-contained**. Do **not** assume access to our repository, our wiki, or any other document of ours — **everything you need is here** (current contract, fields, values, examples). The code/JSON blocks and tables are the source of truth for this exchange. Where we cite `file:line` from our code, it is **provenance** for our own audit trail — you do **not** need to resolve it.
>
> **Purpose of this document:** (1) give you the **complete current state on our side**; (2) list **everything we depend on you for**, with implementable-inline specification; (3) **ask for a return document** (§6) carrying the concrete contract — endpoints, how to reach them, and the exact response shape.
>
> **There are two explicit asks at the end** (§6 and §7). {If true, state the gate plainly: "We will not write a line of code on our side until the contract comes back from you — this document is the gate."}

---

## 1. Context (enough to act)

> What the product/system **is**, in plain terms, for a reader who has never seen it. Then what you are building now, and the requirements that drive the ask. Two or three short subsections beat one dense paragraph.
>
> Include the invariants that govern the exchange — auth scheme, routing/addressing model, multi-tenancy, anything the partner must not violate. The partner needs enough to judge whether your proposal is *reasonable*, not just to implement it literally.

---

## 2. What is ALREADY DONE on our side

> Current state, described so the partner needs nothing else. Say what is implemented, what is **validated and where** (environment, date, real values observed), and what is merely written. Citations here are **provenance-only** — mark them:
>
> - Our adapter already emits field `X` on event `Y`. 📎 *(provenance only — our repo)* `lib/.../foo.dart:42`
>
> A coverage table earns its place whenever the ask is "we have most of it, we need the rest" — it shows the partner precisely how small (or large) their part is:
>
> | {Consumer / screen / feature} | {Fields it uses from your side} | Coverage |
> |---|---|---|
> | ... | ... | ✅ complete / ⚠️ missing `X` → §3.B |
>
> If a limit, volume, or cost motivates the ask, **put the number here**. "It does not scale" is an opinion; "week N costs ~N×11 sequential requests" is an argument.

---

## 3. WHAT WE DEPEND ON YOU FOR

> One subsection per dependency, lettered (3.A, 3.B, …). Each one carries a **state marker in its heading** — `**PENDING (blocking)**`, `**PARTIAL**`, `**PENDING**`, `**ask = do not regress**` — so a reader scanning headings knows what is being asked of them.

### 3.A. {Dependency name} — **PENDING (blocking)**

**Where:** {the concrete system/module/handler that owns this — and, when useful, explicitly where it is *not*: "this is not in the admin service"}.

**What:** {one paragraph — the change in plain terms}.

**Specification** — written **implementable-inline**. Paste the *full* thing the partner must build: the complete parameter table, field list, algorithm, or state machine. Never say "mirror our implementation"; reproduce it.

| Param / field | Type | Required | Semantics |
|---|---|---|---|
| ... | ... | ... | ... |

Numbered semantics for anything ambiguous (inclusive vs exclusive bounds, interaction with existing parameters, ordering, what "empty" means, what stays unchanged).

**Errors** — in the partner's existing error convention:

| Code | When |
|---|---|
| ... | ... |

**Example — what we would call / what we expect back:**

```
{a concrete request and/or response, close enough to copy}
```

> Long or byte-exact payloads do not go inline — put them in `_raw/{slug}.md` (or `.json`) and link: see [`_raw/{slug}.json`](_raw/{slug}.json). Sample captures go in [`artifacts/{slug}-sample.log`](artifacts/{slug}-sample.log).

**E2E acceptance (3.A):** {what "working" looks like from the outside — the observable check both sides can run}.

---

### 3.B. {Second dependency} — **PENDING (blocking)**

> Same shape. When the partner *already receives* the data you are asking them to expose, **show them where it is on their side** — the exact payload position, field name, or ingestion point. It converts "please add a feature" into "please expose what you already have", which is a much smaller ask.
>
> ⚠️ **Flag the traps inline.** If a mapping is counter-intuitive (an array whose order is not alphabetical, a flag whose name inverts its meaning, a unit that is already converted), call it out in a blockquote right where it matters. A trap discovered by the partner in production costs a round; a trap named here costs a sentence.

---

### 3.N. {Existing, already-working part of the contract} — **ask = do not regress**

> List what you already depend on and validated, and ask to be told **before** it changes. This is the cheapest section in the document and it prevents the most expensive surprise.

---

## 4. Pending summary (checklist for you)

> A scannable checkbox list — one line per item above, plus the two asks. Multi-item handoffs come back partially answered without it.

- [ ] **3.A** {one line}
- [ ] **3.B** {one line}
- [ ] **3.N** {one line}
- [ ] **§6** Produce the return document (it is what unblocks our code)
- [ ] **§7** Approved plan before implementing

---

## 5. Open questions

> Stable numbered questions. IDs **never change across rounds** — on a follow-up, append new IDs and re-status the old ones; never renumber or delete. 🔴 = blocking, ⚪ = non-blocking.
>
> Ask for **schema and possible values**, not for a yes/no, whenever the answer will end up in your code.

| ID | Blocking | Question | Status |
|---|---|---|---|
| Q1 | 🔴 | {question} | open |
| Q2 | ⚪ | {question} | open |
| Q3 | 🔴 | {question} | open |

> Status vocabulary: `open → answered → resolved`; `superseded` (with a pointer to the replacing question) if invalidated.

---

## 6. ASK 1 — return document (what we need back)

**Once you have decided your side**, we need a **self-contained return document**, which we will **ingest into our knowledge base** and which is the gate for us to start writing code. At minimum:

1. **{Dependency 3.A}:** {the specific facts you need — final names, exact semantics, interactions, error codes, edge behavior}.
2. **{Dependency 3.B}:** {same, item by item}.
3. **The updated contract:** the field-by-field list of the response (name, type, nullability) **including anything new**, plus **one real example**. State that this example becomes your fixture.
4. **How to reach it:** URL/base per environment, and any difference in auth or limits from what §2 describes.
5. **Versions / environments:** what is in **DEV** vs **PROD** today, **item by item**. A change merged to a branch is a **different fact** from a change deployed — ask them to distinguish.
6. **Their ticket IDs** per item, when they exist, so both sides can track.

> Write it **self-contained and schema-precise**: for each item, the **externally observable behavior** (request/response, types, values, error code). Assume **we have no access to your repository or wiki** — the same rule we applied here. Internal citations are welcome **if** accompanied by the observable behavior.
>
> One formatting request that helps a lot: answer **keyed to the `Q` IDs in §5**, and tag each claim with its **provenance** — `✅` verified in your code, `⚠` asserted but not audited / observable only at runtime. We treat `⚠` as unconfirmed until we validate, which prevents misunderstanding on both sides.

---

## 7. ASK 2 — plan-then-execute

We work under **plan-then-execute**: no code before an approved plan. For anything above that requires a non-trivial change on your side, **do not apply it directly** — bring your human developer a **plan** with:

1. **What** changes (handler/function/field/behavior, before → after);
2. **Why** (which item in this document motivates it, and the risk of not doing it);
3. **Impact and compatibility** (does it break current consumers? affect stored data? affect other callers?);
4. **Validation** (how you confirm it works, including the E2E).

Human approval before implementation. If you open a ticket, send us the ID.

---

## 8. Appendices — reference of what we consume

> **Conditional section.** Include it when the partner must **confirm or map** something against their own contract: a field list, an enum, a set of names, a schema. Its purpose is stated explicitly to them — *if a name or type diverges here, that is exactly the misalignment we want to resolve before we write the client.*

### Appendix A — {field / enum / schema reference}

| {Field in the response} | Expected type | Used by | Note |
|---|---|---|---|
| ... | ... | ... | ... |

> Say plainly which fields you receive and **do not** use — it tells the partner what they are free to leave alone.

### Appendix B — ⚠️ silent failure modes on our side

> Behaviors of *your* client that fail **without a visible error**, so the partner understands why you are being precise. This is the section that turns "we'll expose the fields" into "we'll expose them with exactly these names".
>
> - {e.g. a field named differently than agreed → the series/value simply does not appear; nothing throws}
> - {e.g. two channels swapped at ingestion → the output stays plausible and is wrong}

---

## 9. Contact

{Team}: **{human name}** — `{email}`.
{Artifact identification: repo, branch, app path and version.}

{One closing line: with (a)…(d) plus the return document, what this unblocks.}

---

## Round log

> Append one line per round. Keeps the thread legible without renumbering questions.
>
> If you **revise and resend the same round** (expanded wording, more context), say so here and state explicitly whether the questions changed — the partner must know whether any work already started needs redoing.

- **R1 — {YYYY-MM-DD}:** sent. Blocking: Q1, Q3.
