---
name: intra-team
description: Coordinate with another agent working the SAME repository. Covers five message roles — note (non-blocking heads-up), request (ask an agent to do/decide something), response (answer a request), handoff (transfer ownership of a work item), conflict (resolve a scope collision) — plus maintaining the coordination board (active scope locks + agreements). Use when the human (or an orchestrator) wants to announce a dependency, lock a scope, hand a work item to another agent/session, or resolve two agents colliding on the same code. Reference-first: cite file:line and [[wikilinks]] — the reader shares the repo. Requires the intra-team module.
argument-hint: "[note <slug> | request <slug> | response <path> | handoff <slug> | conflict <slug> | board]"
---

# Intra-team messaging

Agent↔agent coordination **inside one repository**. The reader is another agent that **shares your repo** — so the governing rule is **reference-first** (cite `file:line`, `[[wikilinks]]`, `work_id`; do not re-paste what the reader can open). This is the mirror image of `cross-team` (self-contained). See `modules/intra-team/README.md` for the rationale.

> **Hybrid invocation.** This skill is agent-invocable, but only the `note` flow may be authored **autonomously**. `request` / `response` / `handoff` / `conflict` and **every write to `_board.md`** carry an **in-body human gate**: draft, then STOP and get explicit human approval before writing the file. Never skip the gate on a blocking flow.

## Argument

`$ARGUMENTS` selects the flow:
- `note <slug>` → non-blocking heads-up (Flow A, autonomous-ok).
- `request <slug>` → ask another agent to do/decide something (Flow B, gated).
- `response <path-to-request>` → answer a request (Flow C, gated).
- `handoff <slug>` → transfer ownership of a work item (Flow D, gated).
- `conflict <slug>` → resolve a scope collision (Flow E, gated).
- `board` → create/update the coordination board (Flow F, gated).

If absent, ask which flow the human wants.

## Prerequisites (all flows)

- The intra-team module is installed and `{{project}}_wiki/_meta/conventions.md` carries the extended frontmatter (`direction`, `from_agent`, `to_agent`, `msg_role`, message `status`, `work_refs`, claim-state tags).
- `{{project}}_wiki/work/relay/` exists with `_board.md` and `_templates/`.
- Authored prose is in **{{KNOWLEDGE_LANG}}**.

## Reference-first rule (all flows)

The reader can open any file in this repo. Therefore:

- **Cite, don't reproduce.** Point at `file:line` and `[[wiki pages]]`; do not paste an algorithm, field list, or state machine that already lives in code or the wiki. Duplication drifts.
- **Tag every claim by state**, not by access (README §3):
  - **`✅ landed`** — committed on a branch the reader can read; carries a `file:line`.
  - **`⚠ in-flight`** — in your working tree / a not-yet-merged branch; invisible to the reader. Do not let them build on it.
  - **`🔒 intent`** — planned, not started. Coordination signal only.
- A claim touching code the reader can already open **must** carry a `file:line` (`✅ landed`). Reserve `⚠`/`🔒` for what a `grep` cannot find yet.

## Message file & frontmatter (Flows A–E)

File: `{{project}}_wiki/work/relay/{YYYY-MM-DD}_{slug}.md`. Template: `_templates/message.md`.

```yaml
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
```

---

## Flow A — `note` (non-blocking heads-up) · autonomous-ok

A dependency announcement / FYI. The only flow an agent may author without a human gate.

1. Write the message file with `msg_role: note`, `status: sent`.
2. Body: **Context** (why the heads-up), **What changed / what to watch**, each claim **reference-first + state-tagged**. Example: *"`User.email` is now nullable — `✅ landed` 📎 `lib/domain/user.dart:12`. Consumers should null-check."*
3. If the note concerns an active scope lock, cross-link `[[work/relay/_board]]`.
4. Append to `{{project}}_wiki/_meta/log.md`: `## [YYYY-MM-DD] relay-note | {slug} | to {to_agent}`.
5. No human gate required for `note` — but if it *also* asks for something, it is a `request`, not a `note` (use Flow B, gated).

## Flow B — `request` (ask an agent to do/decide) · GATED

Blocks the recipient. Carries **stable ask IDs**.

1. Draft the message file with `msg_role: request`, `status: sent`.
2. **Open asks** — a stable numbered table. Each ask has an **ID** (`A1`, `A2`, …) that **never changes across rounds**, a **blocking flag** (🔴 blocking / ⚪ non-blocking), and a **status** (`open | answered | resolved | superseded`).

   | ID | Blocking | Ask | Status |
   |---|---|---|---|
   | A1 | 🔴 | {what you need the other agent to do/decide} | open |

3. State everything **reference-first**: point at the code/wiki/`work_id` the ask concerns; state-tag any claim.
4. **Closing ask (dual):** (a) **acknowledge and respond in-thread** — a `response` keyed to the `A` IDs; (b) **respect the shared gate** — no code before an approved plan on their side, and **check `_board.md`** for scope locks before touching shared code.
5. **HUMAN GATE — STOP.** Show the full draft; write the file only after explicit approval.
6. Append to `_meta/log.md`: `## [YYYY-MM-DD] relay-request | {slug} | to {to_agent} | N asks (M blocking)`.

## Flow C — `response` (answer a request) · GATED

Ingest/answer an inbound `request`.

1. File: `{YYYY-MM-DD}_{slug}-response.md`, `direction: inbound`, `msg_role: response`.
2. **Thread the answers** — one block per ask, reusing the **stable `A` IDs** from the originating request (never renumber).
3. Each answer is **reference-first + state-tagged**. Where it touches shared code, add a `file:line` (`✅ landed`).
4. In the originating request, flip each answered ask's status (`answered` / `resolved`). If an answer invalidates an assumption, open a **new** ask (`A7`, …) in the next round rather than editing the old one.
5. If the exchange settles a durable lock/agreement → feed the **board** (Flow F).
6. **HUMAN GATE — STOP** before writing. Append to `_meta/log.md`: `## [YYYY-MM-DD] relay-response | {slug} | K asks answered`.

## Flow D — `handoff` (transfer ownership of a work item) · GATED

One agent stops; another continues the **same** `work_id`.

1. File `msg_role: handoff`; `work_refs` names the `work_id` being transferred.
2. Body sections:
   - **State at handoff** — where the work stands, **reference-first**: link the `[[work/plans/{ID}]]`, `[[work/executions/{ID}]]`, the branch, and the last commit. State-tag anything `⚠ in-flight` (uncommitted work the receiver can't see yet).
   - **What's left** — the remaining checklist (point at the plan's steps, don't re-list).
   - **Landmines** — costly lessons hit so far (if a lesson is durable, also graduate it to a knowledge page per METHODOLOGY §5.6 — don't let it die in the message).
   - **Ownership** — set `to_agent` to the receiver; note the receiver should re-run `/sync-context` before continuing.
3. Update `_board.md`: transfer/release the scope lock on that `work_id` (Flow F).
4. **HUMAN GATE — STOP** before writing. Append to `_meta/log.md`: `## [YYYY-MM-DD] relay-handoff | {work_id} | {from_agent} → {to_agent}`.

## Flow E — `conflict` (resolve a scope collision) · GATED

Two agents touch the same scope; this proposes a resolution.

1. File `msg_role: conflict`; `to_agent` names the other agent (or `any`); `work_refs` names both work items + the contested scope.
2. Body:
   - **Collision** — what overlaps, **reference-first** (the shared `file:line` / `[[page]]` both touch).
   - **Positions** — what each side needs, state-tagged (which side has `✅ landed` code vs `⚠ in-flight`).
   - **Proposed resolution** — who owns the scope, who waits, or how to split. Prefer splitting the work over serializing when possible.
3. Record the resolution on `_board.md` as an **agreement** (Flow F), tagged `proposal` until both sides ack.
4. **HUMAN GATE — STOP** before writing. Append to `_meta/log.md`: `## [YYYY-MM-DD] relay-conflict | {slug} | {scope}`.

## Flow F — coordination board (`_board.md`) · GATED

File: `{{project}}_wiki/work/relay/_board.md`. Template: `_templates/coordination-board.md`. The durable source of truth for active locks + agreements.

1. **Active scope locks (current-state table — overwrite in place).** `scope · owner agent · work_id · state · until`. Add a row when a lock is taken; **remove/mark released** when the work lands or is handed off. Overwriting caps growth — do not accumulate dead rows here. A lock is a **social** signal, not OS enforcement.
2. **Agreements** — durable decisions between in-flight work items, tagged **proposal** (one side suggested) vs **agreed** (both acked). Never let a proposal read as agreed.
3. **Append-only history** — one dated `⚠ UPDATE YYYY-MM-DD` block per lock/agreement change: what changed, why, `work_refs`, and whether it's proposal/agreed. **Never rewrite** a history block.
4. Keep the board **reference-first**: link the message that drove each change (`[[work/relay/{slug}]]`) and the `work_id`s.
5. **HUMAN GATE — STOP** before writing. Append to `_meta/log.md`: `## [YYYY-MM-DD] relay-board | <one line>`.

---

## Registration (all flows)

- Relay files live in `{{project}}_wiki/work/relay/` and are **not** trios — they never enter the generated `work/_index.md` (`work-index`/`work-find`/`work-audit` scan only `tasks`/`plans`/`executions`). `_board.md` is the relay's own catalog.
- Do **not** add relay files to `{{project}}_wiki/_meta/index.md` (that catalogs knowledge). Their home is the `work/` layer.

## Anti-patterns

- ❌ Re-pasting code, an algorithm, or a field list the reader can open. Reference-first — cite `file:line` / `[[page]]`. (This is the inverse of `cross-team`'s self-contained rule.)
- ❌ Skipping the human gate on `request` / `response` / `handoff` / `conflict` / `_board.md`. Only `note` is autonomous.
- ❌ Tagging a claim by access instead of state. Use `✅ landed` / `⚠ in-flight` / `🔒 intent`; a landed claim needs a `file:line`.
- ❌ Letting the reader build on a `⚠ in-flight` claim as if it were `landed`.
- ❌ Renumbering ask IDs between rounds. `A1` means the same thing forever — append and re-status, never renumber or delete.
- ❌ Dropping the dual closing ask on a `request` (acknowledge-and-respond + respect-the-gate/check-the-board).
- ❌ Letting `_board.md`'s current-state table grow unbounded. Overwrite the locks table; append only the history.
- ❌ Adding relay files to `{{project}}_wiki/_meta/index.md` or expecting them in `work/_index.md`.
- ❌ Treating a board scope lock as OS enforcement — it is a social convention between cooperating agents.

## Cross-references

- `modules/intra-team/README.md` — rationale, the `cross-team` inversion, claim-state tags, boundary vs. execution/§4.2.5.
- `.agents/METHODOLOGY.md` §4.2.5 — ephemeral pre-plan sub-agents (contrast: relay is durable).
- `.agents/METHODOLOGY.md` §5.6 — a durable lesson graduates to a knowledge page (used by `handoff`).
- `.claude/skills/sync-context/SKILL.md` — the receiver runs this before continuing a `handoff`.
- `.claude/skills/cross-team-handoff/SKILL.md` — the mirror module for a partner team that does NOT share the repo.
