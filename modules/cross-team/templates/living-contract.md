<!--
  Installs as: {{project}}_wiki/sources/external/_handoff_templates/living-contract.md
  See INSTALL.md §5 and modules/cross-team/README.md.

  A LIVING-CONTRACT page is the DURABLE source of truth for an interface shared
  with a partner team. It lives in {{project}}_wiki/cross-cutting/ (it crosses the
  boundary between your team and the partner). Copy to
  {{project}}_wiki/cross-cutting/{subject}-contract.md and fill {...}.
  Do NOT de-template `{...}` — those are per-contract fill-ins.

  Authored prose is in {{KNOWLEDGE_LANG}}.
-->
---
title: {Subject} — contract with the partner team
type: contract
scope:
  area: []                     # single-repo: free text. Monorepo: apps/packages.
status: draft                  # stub | draft | stable | stale
updated: {YYYY-MM-DD}
summary: One sentence — the interface this contract governs.
external_tickets: []           # partner ticket/issue IDs
sources:                       # the handoff/response docs that fed this page
  - sources/external/{YYYY-MM-DD}_{slug}.md
code_refs: []                  # OUR files that implement our side of the contract
related: []
---

# {Subject} — living contract

**Audience:** the partner team's LLM and ours — the running source of truth for this interface.

> **Self-contained.** Assume a reader with no access to the *other* side's repo. The current-state table below is authoritative; the update history explains how it got there. **Do not rewrite history blocks** — overwrite only the current-state table.

## 1. Current state (authoritative — overwritten in place)

> The present truth of every field / endpoint / message. This table is **overwritten** as things change — that is what caps the page's growth. Tag each row **P** = proposal (not yet agreed/deployed) or **V** = implemented-and-validated (live, confirmed both sides).

| Item | Shape / value | Owner | P/V | Notes |
|---|---|---|---|---|
| {field / endpoint / message} | {type / format} | {us / partner} | V | {...} |
| {field} | {type} | {partner} | P | proposed R2, not deployed |

## 2. Environment state (deployable changes)

> "Is it live?" has exactly one answer. A change on a branch but not in PROD is a different fact from one in PROD.

| Change | Code branch | DEV | PROD |
|---|---|---|---|
| {change} | merged | ✅ | ✅ |
| {change} | in-review | ⚠ | — |

> Legend: ✅ present & validated · ⚠ present but unconfirmed · — not there.

## 3. Update history (append-only — never rewritten)

> One dated block per change. Newest at top or bottom (be consistent). Never edit a past block.

### ⚠ UPDATE {YYYY-MM-DD} — {what changed}
- **Was:** {prior state}
- **Now:** {new state}
- **Why / source:** [[sources/external/{YYYY-MM-DD}_{slug}]] · Q{k}
- **State:** proposal | implemented-and-validated

### ⚠ UPDATE {YYYY-MM-DD} — {earlier change}
- **Was:** …
- **Now:** …
- **Why / source:** …
- **State:** …

## 4. Open items

> What is still unsettled — unresolved blocking questions from the latest handoff, proposals awaiting agreement, validations pending.

- [ ] {open item} → handoff [[sources/external/{YYYY-MM-DD}_{slug}]] Q{k}
