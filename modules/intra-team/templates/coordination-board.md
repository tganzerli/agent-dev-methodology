<!--
  Installs as: {{project}}_wiki/work/relay/_templates/coordination-board.md
  See INSTALL.md §5-bis and modules/intra-team/README.md §4.

  This is the TEMPLATE. The live board is a SINGLE maintained page —
  {{project}}_wiki/work/relay/_board.md — one per project, not one-per-copy.
  Create it once from this template, then update it in place forever.
  Fill the `{...}` placeholders; do NOT de-template `{...}` in this file itself.

  A scope lock or agreement on this board is a SOCIAL signal between
  cooperating agents — it prevents clobbering by communication, not by
  the OS or filesystem. Nothing here is enforced; it works only if every
  agent reads it before touching shared scope.

  Authored prose is in {{KNOWLEDGE_LANG}}.
-->
---
title: Coordination board
type: relay-board
scope:
  area: []                     # single-repo: free text. Monorepo: apps/packages.
status: draft                  # stub | draft | stable | stale
updated: {YYYY-MM-DD}
summary: One sentence — the active coordination state of agents on this repo.
work_refs: []                  # work_ids currently touched by an active lock/agreement
related: []
---

# Coordination board

**Audience:** every agent working this repo.

> The current-state tables below are authoritative — **"now."** The update history explains **how it got there.** **Do not rewrite history blocks** — overwrite only the current-state tables. Reference-first: link the driving message `[[work/relay/{slug}]]` and `work_id`s; do not re-explain what the message already says.

## 1. Active scope locks (authoritative — overwritten in place)

> Who is touching what, right now. Add a row when a lock is taken; **remove the row or mark it `released`** when the work lands or is handed off. Overwriting caps growth — **do not accumulate dead rows.** A lock is a **social** signal (avoid clobbering by communication), **not** OS/filesystem enforcement — nothing stops an agent from editing a locked scope; the board only works if every agent checks it first.

| Scope | Owner agent | work_id | State | Until | Note |
|---|---|---|---|---|---|
| {file/dir/module or logical scope, e.g. `lib/domain/diary_schedule_service.dart`} | {from_agent, e.g. opus-4.8/auth-refactor} | {work_id} | held | {YYYY-MM-DD or "landing of work_id"} | [[work/relay/{YYYY-MM-DD}_{slug}]] |
| {scope} | {agent} | {work_id} | releasing | {YYYY-MM-DD} | handing off — see [[work/relay/{YYYY-MM-DD}_{slug}]] |

## 2. Agreements (authoritative — overwritten in place)

> Durable decisions between in-flight work items — e.g. "A owns the `User` entity shape this week; B consumes it read-only." **P/A** column: **P** proposal (one side suggested, not both acked) or **A** agreed (both acked). **Never let a proposal read as agreed** — flip to **A** only after the other side has actually acked, in a `response` or `conflict` resolution.

| Item | Between | Decision | P/A | Source |
|---|---|---|---|---|
| {shared entity/contract/scope} | {agent A} ↔ {agent B} | {who owns what, who consumes read-only, how it's split} | A | [[work/relay/{YYYY-MM-DD}_{slug}]] |
| {shared entity/contract/scope} | {agent A} ↔ {agent B} | {proposed decision, not yet acked} | P | [[work/relay/{YYYY-MM-DD}_{slug}]] |

## 3. Update history (append-only — never rewritten)

> One dated block per lock/agreement change. Newest at top or bottom (be consistent). **Never edit a past block** — the tables above are "now," this history is "how we got here."

### ⚠ UPDATE {YYYY-MM-DD} — {what changed, e.g. "A1 locked `lib/domain/diary_schedule_service.dart`"}
- **Was:** {prior state — e.g. "no lock on this scope"}
- **Now:** {new state — e.g. "opus-4.8/auth-refactor holds the scope until work_id lands"}
- **Why / source:** [[work/relay/{YYYY-MM-DD}_{slug}]] · {work_id}
- **State:** proposal | agreed

### ⚠ UPDATE {YYYY-MM-DD} — {earlier change, e.g. "agreement on `User` entity ownership"}
- **Was:** {prior state}
- **Now:** {new state}
- **Why / source:** [[work/relay/{YYYY-MM-DD}_{slug}]] · {work_id}
- **State:** proposal | agreed

## 4. Open items

> Unresolved conflicts, proposals awaiting agreement, locks pending release. Each item links the relay message driving it.

- [ ] {open conflict/proposal/pending release} → [[work/relay/{YYYY-MM-DD}_{slug}]]
