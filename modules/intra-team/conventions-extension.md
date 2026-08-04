# Conventions extension — intra-team module

> **Installer:** append the section below (everything between the two `⟪…⟫` markers) into
> `{{project}}_wiki/_meta/conventions.md`, as a new top-level section after §4 "Page types".
> Do **not** create a separate file in the target project — these fields belong in the one
> canonical conventions doc so every agent finds them there. Remove the `⟪…⟫` markers when
> pasting.
>
> This extension is only installed when the **intra-team module** is active (INSTALL.md §5-bis).
> It standardizes frontmatter for agent↔agent relay messages and the coordination board — pinning
> the vocabulary before first use so concurrent agents don't drift into private conventions.

---

⟪ BEGIN drop-in section — paste into {{project}}_wiki/_meta/conventions.md ⟫

## Intra-team frontmatter (agent↔agent, same repo)

Messages exchanged between agents working the **same repo** extend the base frontmatter with the fields below. They apply to pages in `work/relay/` (messages and the coordination board).

**Governing rule: reference-first** — the opposite of `cross-team`'s self-contained rule. The reader shares your repository, so cite `file:line` / `[[wikilinks]]` and let them open the source. Do **not** re-paste an algorithm, field list, or state machine that already lives in code or the wiki — duplication drifts.

```yaml
---
title: ...
type: relay                    # relay for messages; relay-board for the coordination board
direction: outbound            # outbound (we authored it) | inbound (we received it)
from_agent: {model/role}       # e.g. opus-4.8/auth-refactor
to_agent: {model/role | any}   # `any` broadcasts to whoever picks up the scope
msg_role: note                 # note | request | response | handoff | conflict
status: sent                   # MESSAGE lifecycle: sent | read | acked | resolved | superseded
                               #   (base stub|draft|stable|stale still applies to the
                               #    coordination board)
updated: 2026-08-04
summary: One sentence — what this message coordinates.
work_refs: []                  # internal work_ids / [[wikilinks]] / branches — keep greppable
related: []
---
```

### Field meanings

| Field | Applies to | Values | Meaning |
|---|---|---|---|
| `direction` | all relay messages | `outbound \| inbound` | Did this agent author it (`outbound`) or receive it (`inbound`)? |
| `from_agent` / `to_agent` | all relay messages | free string | Agent identity — model + role/session, e.g. `opus-4.8/auth-refactor`. `to_agent: any` broadcasts to whoever picks up the scope. |
| `msg_role` | all relay messages | `note \| request \| response \| handoff \| conflict` | The message's role in the exchange: `note` = non-blocking heads-up; `request` = ask another agent to do/decide something; `response` = answer a request, keyed to its ask IDs; `handoff` = transfer ownership of a work item; `conflict` = two agents collide on a scope, propose a resolution. |
| `status` (message) | relay messages | `sent \| read \| acked \| resolved \| superseded` | Lifecycle of a message: `sent` → `read` → `acked` → `resolved` (or `superseded` by a later message). For the coordination board, keep the base `stub\|draft\|stable\|stale`. |
| `work_refs` | all relay messages | list of strings | Internal `work_id`s / `[[wikilinks]]` / branch names the message concerns, kept **greppable** (`grep -rn <work_id> {{project}}_wiki/`). |

### Claim-state tags (in the body, per claim)

Between two agents in the **same** repo, both can open the same files — the asymmetry is not access but **time**: the author may describe code on their uncommitted working tree or an unmerged branch, not yet visible where the reader stands. So relay claims are tagged by **state**:

| Tag | Meaning | Reader's duty |
|---|---|---|
| `✅ landed` | Committed on a branch the reader can read; carries a `file:line`. | Verify it yourself — it's real and visible. |
| `⚠ in-flight` | In the author's working tree / a not-yet-merged branch. Invisible to the reader. | **Do not build on it** until it lands; treat as a promise, not a fact. |
| `🔒 intent` | The author *plans* to do this; not started. Pure coordination signal. | Plan around it; expect it may change or never happen. |

This is a **different axis** from both other tag sets in this vault: the base `⚠ unverified` marker means "no citation yet"; `cross-team`'s `⚠` means "asserted by a party we cannot audit"; intra-team's `⚠ in-flight` means "real but not yet visible on the reader's branch". A claim touching code the reader can already open **must** carry a `file:line` and be tagged `✅ landed`.

### Stable ask IDs

Open asks in a `request` use **stable IDs** (`A1`, `A2`, …) that **never change across rounds**. Follow-up rounds append new IDs; prior ones are re-statused (`open → answered → resolved`) or `superseded` (with a pointer), never renumbered or deleted. See the `intra-team` skill.

### Where these docs live
- Messages → `work/relay/{YYYY-MM-DD}_{slug}.md`.
- Coordination board → `work/relay/_board.md`.
- Both live in the `work/` layer: they are **not** cataloged in `_meta/index.md` (that catalogs knowledge, not coordination), and they are **not** trios — they never enter the generated `work/_index.md` (`work-index` / `work-find` / `work-audit` scan only `tasks/`, `plans/`, `executions/`).

⟪ END drop-in section ⟫
