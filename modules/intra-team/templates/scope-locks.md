<!--
  Installs as: {{project}}_wiki/work/relay/_locks.md
  See modules/intra-team/README.md §4.

  This is the TEMPLATE. The live table is a SINGLE maintained page — one per
  project. Create it once from this template, then overwrite rows forever.
  Fill the `{...}` placeholders; do NOT de-template `{...}` in this file itself.

  THIS FILE IS LIVE STATE, and it is the only page in the vault that is. It
  needs a publication route that does NOT wait for the work to land — §4.2 of
  the module README lists the routes and what each costs. Pick one before you
  install this file; a live table on the default per-branch route is the defect,
  not the fix.

  A scope lock is a SOCIAL signal between cooperating agents — it prevents
  clobbering by communication, not by the OS. Nothing here is enforced.

  Authored prose is in {{KNOWLEDGE_LANG}}.
-->
---
title: Active scope locks
type: relay-locks
status: live
updated: {YYYY-MM-DD}
summary: One sentence — live state of who is touching what right now.
related: []
---

# Active scope locks

**Audience:** every agent working this repo, and every agent of a peer repo if `peer-relay` is installed.

> **Live state.** A lock is only a social signal if another working tree can read it **while it is
> alive**. Write rows through whatever publication route this project chose (`modules/intra-team/README.md`
> §4.2) — **never** by editing this file on your work branch, which is the defect §4 documents.
>
> **Not enforcement.** Nothing stops an agent from editing a locked scope. This works only if every
> agent reads it before touching shared scope.
>
> **What does not live here:** agreements, history and open items stay in [[work/relay/_board]], which
> is versioned with the trio because it describes what has landed.

| Scope | Owner agent | work_id | State | Until | Source |
|---|---|---|---|---|---|
| {none} | — | — | — | — | — |
| {narrowest path that serves, e.g. `lib/domain/diary_schedule_service.dart`} | {from_agent, e.g. opus-4.8/auth-refactor} | {work_id} | held | {the condition that ends it, e.g. "landing of the PR"} | [[work/plans/{work_id}]] |
| {scope, peer-prefixed if it lives in a peer repo} | {agent} | {work_id} | releasing | {condition} | [[work/relay/{YYYY-MM-DD}_{slug}]] |

## How to fill it

| Column | What goes in |
|---|---|
| **Scope** | A path, the narrowest that serves. Peer prefix when the scope lives in another repo. |
| **Owner agent** | `<model>/<skill or front>`, matching `from_agent`. |
| **work_id** | The trio that justifies the lock. **Required** — a CI check compares it against trio status. |
| **State** | `held` while the work runs · `releasing` while it lands. |
| **Until** | The **condition** that ends the lock, not a guessed date. |
| **Source** | The plan or execution that told you to take it. |

**Release in the PR that lands the work — not before, not after.** Releasing early opens the scope to
another agent while the merge is still pending; releasing late leaves this table lying for a window.

**Nothing forces you to take a lock.** This table promises **visibility**, not obligation: an empty
table is telling the truth when it says it is empty (README §4.4).
