<!--
  Installs as: {{project}}_wiki/work/relay/_templates/message.md
  See INSTALL.md §5-bis and modules/intra-team/README.md.

  This ONE template serves all five relay roles — note / request / response /
  handoff / conflict. Copy it to {{project}}_wiki/work/relay/{YYYY-MM-DD}_{slug}.md
  and fill the {...} per-message placeholders. Do NOT de-template the `{...}`
  below — those are per-message fill-ins, distinct from the kit-wide `{{...}}`
  resolved at install. Keep or delete the role-specific sub-notes per §2 below
  to match the msg_role you're authoring.

  Authored prose is in {{KNOWLEDGE_LANG}}.

  REFERENCE-FIRST rule (the opposite of cross-team's self-contained rule): the
  reader shares this repo. Cite `file:line` and `[[wikilinks]]` — do NOT
  re-paste code, an algorithm, or a field list the reader can open themselves.
  Duplication drifts.
-->
---
title: {human title}
type: relay
direction: outbound            # outbound (we authored) | inbound (we received)
from_agent: {model/role}       # e.g. opus-4.8/auth-refactor
to_agent: {model/role | any}   # `any` broadcasts to whoever picks up the scope
msg_role: note                 # note | request | response | handoff | conflict
status: sent                   # sent | read | acked | resolved | superseded
updated: {YYYY-MM-DD}
summary: One sentence — what this message coordinates.
work_refs: []                  # work_ids / [[wikilinks]] / branches concerned — greppable
related: []
---

# {Message title}

**From:** {from_agent}
**To:** {to_agent}

> **Reference-first rule.** The reader shares this repo — they can open any file you cite. Point, don't re-paste. Tag every claim by **state**, not access:
>
> - **`✅ landed`** — committed on a branch the reader can read; carries a `file:line`.
> - **`⚠ in-flight`** — in your working tree / a not-yet-merged branch; invisible to the reader. Don't build on it.
> - **`🔒 intent`** — planned, not started. Coordination signal only.

## 1. Context

> Why this message exists — the situation that made it worth writing, in plain terms. 1–3 paragraphs. Applies to every role.

## 2. Message body

> Keep the sub-section that matches this message's `msg_role`; delete the rest.

**If `note`** — what changed / what to watch, reference-first + state-tagged:

> - `User.email` is now nullable — `✅ landed` 📎 `lib/domain/user.dart:12`. Consumers should null-check.
> - If this concerns an active scope lock, cross-link [[work/relay/_board]].

**If `handoff`** — transfer of ownership on the `work_id` named in `work_refs`:

> - **State at handoff** — where the work stands. Link `[[work/plans/{work_id}]]`, `[[work/executions/{work_id}]]`, the branch, and the last commit. Tag anything `⚠ in-flight` (uncommitted work the receiver can't see yet).
> - **What's left** — the remaining checklist; point at the plan's steps, don't re-list them.
> - **Landmines** — costly lessons hit so far. If a lesson is durable, graduate it to a knowledge page (METHODOLOGY §5.6) — don't let it die in this message.
> - **Ownership** — `to_agent` is the receiver; note that they should re-run `/sync-context` before continuing.

**If `conflict`** — two agents colliding on a scope:

> - **Collision** — what overlaps, reference-first: the shared `file:line` / `[[page]]` both sides touch.
> - **Positions** — what each side needs, state-tagged (who has `✅ landed` code vs `⚠ in-flight`).
> - **Proposed resolution** — who owns the scope, who waits, or how to split. Prefer splitting the work over serializing when possible.

**If `request` / `response`** — see §3 (Open asks) below; this section can hold any framing prose the asks need.

## 3. Open asks

> Used by `request` to raise asks; a `response` reuses the SAME IDs — never renumbers.

| ID | Blocking | Ask | Status |
|---|---|---|---|
| A1 | 🔴 | {what you need the other agent to do/decide} | open |
| A2 | ⚪ | {what you need the other agent to do/decide} | open |

> IDs **never change across rounds** — on a follow-up round, append new IDs (`A7`, `A8`, …) and re-status the old ones; never renumber or delete. Status vocabulary: `open → answered → resolved`; `superseded` (with a pointer to the replacing ask) if invalidated.

## 4. Closing asks

> For `request` / `response` / `handoff` / `conflict` — two asks, both required:

1. **Acknowledge and respond in-thread**, keyed to the `A` IDs above (a `response` file threads its answers to the same IDs — never renumber).
2. **Respect the shared gate** — no code before an approved plan on the other side, and **check [[work/relay/_board]]** for active scope locks before touching shared code.

---

## Round log

> Append one line per round. Keeps the thread legible without renumbering asks.

- **R1 — {YYYY-MM-DD}:** sent. Blocking: A1.
