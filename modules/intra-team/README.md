# Intra-team module — agent↔agent messaging inside one repo

> **OPTIONAL module.** Install only when **more than one agent** works the **same repository** — concurrently (two agents on different areas at once) or sequentially (one agent hands a work item to the next session/agent) — and they need to **coordinate**: announce a dependency, lock a scope, request a decision, or hand off a work item. If a single agent works the repo alone, you do **not** need this module — the trio (task/plan/execution) and the execution log already record everything one agent does.

## 1. The premise, and why it inverts `cross-team`

This module is the **mirror image** of `cross-team`. Both move messages between LLM agents; they differ on **one axis** — *does the reader share your repository?*

| | `cross-team` | `intra-team` (this module) |
|---|---|---|
| Reader | a **partner team's** LLM | **another agent** on the same repo |
| Shared universe | **no** — separate repos | **yes** — same repo, wiki, branches |
| Governing rule | **self-contained**: assume zero repo access, inline everything | **reference-first**: the reader can open any file — *point*, don't re-paste |

Almost every `cross-team` rule flips here:

| Dimension | `cross-team` | `intra-team` |
|---|---|---|
| **Reader's code access** | zero → inline the full spec; `file:line` is provenance-only, *not* required reading | full → cite `file:line`, `[[wikilinks]]`, `work_id`, branch. **Do not** reproduce what the reader can open. |
| **Confidence tag** | `✅` verified-in-their-code / `⚠` can't-audit-their-repo | **claim-state**, not access: `✅ landed` / `⚠ in-flight` / `🔒 intent` (§3) |
| **Identity** | team name | **agent identity** — `from_agent` / `to_agent` (model + role/session) |
| **Linkage** | `external_tickets` (partner's tracker) | `work_refs` — internal `work_id`s, wikilinks, branch names |
| **Durable artifact** | living-contract (interface between teams) | **coordination board** (who owns which scope, active locks, agreed hand-off points) |
| **Closing ask** | (a) return a doc to ingest, (b) plan-before-code | (a) acknowledge + respond in-thread, (b) respect the shared gate + **scope-lock awareness** |
| **Language** | `{{KNOWLEDGE_LANG}}` (+ verbatim in the partner's language) | `{{KNOWLEDGE_LANG}}` throughout — same project |

**The reference-first rule is the whole point.** In `cross-team` you inline the full algorithm because the partner cannot open your files. Here the reader *is in the same repo*, so inlining a spec that already exists in code or in a wiki page is **duplication that will drift**. An `intra-team` message says *"align `DiaryScheduleService.build()` — see `lib/domain/diary_schedule_service.dart:88` and [[services/diary-schedule-service]]"*, not a pasted copy of the method.

## 2. Where intra-team docs live

Messages live **inside the vault's work layer**, so the Obsidian graph links a message to the `work_id`s and knowledge pages it references — the same load-bearing reason `work/` lives inside the vault at all.

```
{{project}}_wiki/work/
├── tasks/                       ← trio (unchanged)
├── plans/                       ← trio (unchanged)
├── executions/                  ← trio (unchanged)
└── relay/                       ← THIS MODULE
    ├── YYYY-MM-DD_slug.md        ← one file per message (note / request / response / handoff / conflict)
    └── _board.md                ← the durable coordination board (active scope locks + agreements)
```

- **`relay/YYYY-MM-DD_slug.md`** — one message per file. Reference-first: cite code and wiki, don't re-paste. Its own slug (not a `work_id`); it points at work via `work_refs`.
- **`relay/_board.md`** — the durable **coordination board** (§4). Current-state table of active scope locks + agreements, plus an append-only history. Outlives any single message.

### `relay/` is a fourth `work/` subdir — deliberately outside the trio scan

`relay/` sits beside `tasks/`/`plans/`/`executions/` but is **not** part of the task→plan→execution trio. This is intentional and already safe:

- `work-index/generate.py` and `work-find/find.py` iterate an **explicit allowlist** `("tasks", "plans", "executions")` — they never see `relay/`. `work-audit` (step 2) `ls`es only those three. So relay messages **never** pollute the generated work index, and `work-audit` never reports them as broken trios. **No script change is required.**
- Relay docs are **historical**, like executions: chronological, never `stale`, ignored by `wiki-lint`'s stale check (the whole `work/` subtree already is). `_board.md` is the relay's own catalog — the work index does not list relay.
- To find old messages: `grep` / `work-find` still reads the tree; relay files are plain markdown.

## 3. Claim-state tags — the core inversion

`cross-team` tags a claim by **repo access** (`✅` I saw it in *their* code you can't audit / `⚠` I couldn't audit their repo). Between two agents in the **same** repo that asymmetry vanishes — both can open the same files. What remains is a **temporal / branch asymmetry**: the author may be describing code that is on their **uncommitted working tree** or their **branch**, not yet visible where the reader stands. So the tag encodes **state**, not access:

| Tag | Meaning | Reader's duty |
|---|---|---|
| `✅ landed` | Committed on a branch the reader can read. Carries a `file:line`. | Verify it yourself — it's real and visible. |
| `⚠ in-flight` | In the author's working tree / a not-yet-merged branch. Not visible to the reader yet. | **Do not build on it** until it lands; treat as a promise, not a fact. |
| `🔒 intent` | The author *plans* to do this; not started. Pure coordination signal. | Plan around it; expect it may change or never happen. |

A claim that touches code the reader can already open **must** carry a `file:line` and be tagged `✅ landed`. The value of `⚠ in-flight` / `🔒 intent` is precisely to name the things a `grep` **won't** find yet — the collisions that cause two agents to clobber each other.

## 4. The coordination board (`relay/_board.md`)

Messages are *episodic* (one exchange). The **board** is *durable* — the running answer to *"who is touching what right now, and what have we agreed?"* so no agent re-derives it from ten messages.

- **Active scope locks** — a current-state table: `scope · owner agent · work_id · state · until`. Overwritten in place as locks are taken and released (this caps growth). A lock is a **social** signal (avoid clobbering), not a filesystem lock.
- **Agreements** — durable decisions between in-flight work items ("A owns the `User` entity shape this week; B consumes it read-only"). Tagged **proposal** vs **agreed**.
- **Append-only history** — dated `⚠ UPDATE YYYY-MM-DD` blocks: what lock/agreement changed and why. Never rewritten; the current-state table is "now", the history is "how we got here".

## 5. Frontmatter this module standardizes

Appended into `{{project}}_wiki/_meta/conventions.md` (drop-in section in `conventions-extension.md`):

| Field | Values | Meaning |
|---|---|---|
| `direction` | `outbound \| inbound` | Did this agent author it (`outbound`) or receive it (`inbound`)? |
| `from_agent` / `to_agent` | free string | Agent identity — model + role/session, e.g. `opus-4.8/auth-refactor`. `to_agent: any` broadcasts. |
| `msg_role` | `note \| request \| response \| handoff \| conflict` | The message's role (§6). |
| `status` (message) | `sent \| read \| acked \| resolved \| superseded` | Lifecycle of a message. |
| `work_refs` | `[]` | Internal `work_id`s / wikilinks / branches the message concerns — keep greppable. |
| claim-state tags | `✅` / `⚠` / `🔒` (per claim, in body) | `landed` / `in-flight` / `intent` (§3). |

## 6. Message roles and the hybrid gate

| `msg_role` | Purpose | Blocking? | Gate |
|---|---|---|---|
| `note` | Heads-up / dependency announcement (FYI) | non-blocking | **agent may author autonomously** |
| `request` | Ask the other agent to do/decide something | blocks the recipient | human gate |
| `response` | Answer a `request` (keyed to its ask IDs) | — | human gate |
| `handoff` | Transfer ownership of a work item to another agent | — | human gate |
| `conflict` | Two agents collide on a scope; propose a resolution | blocks both | human gate |

**Hybrid invocation.** The `intra-team` skill is agent-invocable at the frontmatter level so an orchestrated multi-agent run can drop a `note` without a human in the loop. But `request` / `response` / `handoff` / `conflict` and **every write to `_board.md`** carry an **in-body human gate** — the skill stops and asks for approval before writing. Open asks use **stable IDs** (`A1`, `A2`, …) that never renumber across rounds, exactly like `cross-team`'s `Q` IDs.

## 7. Install

See `INSTALL.md` §5-bis. In short:

1. Copy `skills/intra-team/` → `.claude/skills/intra-team/`.
2. Copy `templates/*` → `{{project}}_wiki/work/relay/_templates/`.
3. Create `{{project}}_wiki/work/relay/` (empty) and an initial `{{project}}_wiki/work/relay/_board.md` from the board template.
4. Append `conventions-extension.md` into `{{project}}_wiki/_meta/conventions.md`.
5. Register `intra-team` in `.claude/skills/_index.md` (mark it hybrid: agent-invocable, in-body gate on the blocking flows).

All authored content is in **{{KNOWLEDGE_LANG}}**, like the rest of the wiki.

## 8. Boundary — what this is NOT

- **Not the execution log.** An execution records *what one agent did* (historical, addressed to nobody). A relay message is *addressed and forward-looking* — "do X", "don't touch Y", "I hand you Z".
- **Not the §4.2.5 pre-plan analyses.** Those dispatch **ephemeral** sub-agents whose context dies with the turn. Relay messages are **durable** and persist across sessions.
- **Not a filesystem lock.** A scope lock on the board is a **social** convention between cooperating agents, not enforcement. It prevents clobbering by *communication*, not by the OS.
- **Not `cross-team`.** If the reader cannot open your repo, you need `cross-team` (self-contained), not this.

## 9. Opt-in escalations (NOT default)

The reference-first message + coordination-board shape is the core. Heavier ideas — install only if the pain appears:

- **Machine-checked scope locks in CI** — a pre-merge hook that fails a PR touching a scope another agent holds on `_board.md`. *Escalate when:* social locks are ignored and clobbering keeps happening. Until then, the board is advisory.
- **Structured broadcast bus** — a queue/topic instead of one-file-per-message, for many agents at high message volume. *Escalate when:* `relay/` churns faster than humans can gate. Until then, one file per message + `work_refs` greppability suffices.

Both are **not defaults** — the seed-vs-accretion principle (`docs/design-rationale.md`).

## 10. Provenance — proven vs. generalized

Be honest about maturity: unlike `cross-team` (whose hand-shape was run repeatedly before it was a skill), this module is **largely an informed generalization**. It applies the *proven* structural spine of `cross-team` (addressed docs, stable ask IDs, episodic-message + durable-durable split, per-claim tags, dual closing ask) to the intra-repo case, **inverting** the access premise. The **reference-first rule** and the **claim-state tags** are the new, unproven pieces — adopt them, then let real multi-agent use tell you which parts earn their keep. Prune what doesn't.
