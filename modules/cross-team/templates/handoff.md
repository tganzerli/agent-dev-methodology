<!--
  Installs as: {{project}}_wiki/sources/external/_handoff_templates/handoff.md
  See INSTALL.md §5 and modules/cross-team/README.md.

  A HANDOFF is an OUTBOUND document your team's LLM authors FOR the partner
  team's LLM. Copy this file to {{project}}_wiki/sources/external/{YYYY-MM-DD}_{slug}.md
  and fill the {...} per-doc placeholders. Do NOT de-template the `{...}` below —
  those are per-handoff fill-ins, distinct from the kit-wide `{{...}}` resolved at install.

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

# {Handoff title}

**Audience:** the partner team's LLM (e.g. the backend team's coding agent) — write for another LLM reader.
**Author:** your team's agent, gated by {human}.

> **Self-contained rule.** Assume you (the reader) have **zero access to our repository**. *Everything you need to act on this handoff is in this document.* Any `file:line` reference below is **provenance for our own audit trail — not required reading for you.** If something matters for your work, it is stated inline here.

## 1. Context

> Why this exchange exists. The goal in plain terms. Any decision already made on our side that frames the ask. 1–3 paragraphs.

## 2. What we already have

> Current state on our side, described so the partner needs nothing else. Citations here are **provenance-only** — mark them:
>
> - Our adapter already emits field `X` on event `Y`. 📎 *(provenance only — our repo)* `lib/.../foo.dart:42`
>
> The partner reads the prose; the citation is just our paper trail.

## 3. What we need from you

> The spec, **written implementable-inline** — paste the FULL thing the partner must build. Do not say "mirror our implementation"; reproduce it here.

- **The algorithm / field list / state machine (in full):**

  > Paste the complete, unambiguous specification. If it is long or must be byte-exact, put the verbatim block under `sources/external/_raw/{slug}.md` (or `.json`) and link it:
  >
  > See the exact payload in [`_raw/{slug}.json`](_raw/{slug}.json). Sample capture: [`artifacts/{slug}-sample.log`](artifacts/{slug}-sample.log).

- **Constraints / invariants** the partner must preserve.
- **What "done" looks like** on the partner's side (acceptance).

## 4. Open questions

> Stable numbered questions. IDs **never change across rounds** — on a follow-up, append new IDs and re-status the old ones; never renumber or delete. 🔴 = blocking, ⚪ = non-blocking.

| ID | Blocking | Question | Status |
|---|---|---|---|
| Q1 | 🔴 | {question} | open |
| Q2 | ⚪ | {question} | open |
| Q3 | 🔴 | {question} | open |

> Status vocabulary: `open → answered → resolved`; `superseded` (with a pointer to the replacing question) if invalidated.

## 5. Closing asks

Two asks, both required:

1. **Send us back a return document we can ingest.** Please reply as a markdown document in the same shape: answers **keyed to the Q IDs above**, and a **provenance tag per claim** — `✅` you verified it in your code, `⚠` asserted-but-not-audited / runtime-only. We will ingest it directly.
2. **Bring a plan-then-execute proposal before touching your code.** Before implementing anything above, produce a short plan (what you will change and why) and get it approved on your side. No code before an approved plan — this mirrors our own working rule.

---

## Round log

> Append one line per round. Keeps the thread legible without renumbering questions.

- **R1 — {YYYY-MM-DD}:** sent. Blocking: Q1, Q3.
