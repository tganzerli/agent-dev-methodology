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
    ├── _board.md                ← the DURABLE board (agreements + history + open items)
    └── _locks.md                ← the LIVE lock table — different lifetime, different route (§4)
```

- **`relay/YYYY-MM-DD_slug.md`** — one message per file. Reference-first: cite code and wiki, don't re-paste. Its own slug (not a `work_id`); it points at work via `work_refs`.
- **`relay/_board.md`** — the **durable** board (§4): agreements, append-only history, open items. Outlives any single message, and describes what has **landed**.
- **`relay/_locks.md`** — the **live** lock table (§4). Same directory, opposite lifetime: it answers "now", so it needs a publication route that does not wait for the work to land. **Do not merge it back into `_board.md`** — that is the defect §4 documents.

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

## 4. The board (`relay/_board.md`) and the live lock table (`relay/_locks.md`)

Messages are *episodic* (one exchange). The **board** is *durable*. A **scope lock is neither** — it lives for hours and must be read by a **different working tree while it is alive**. Those are opposite versioning requirements, and one file cannot serve both.

| | Live lock table | Agreements · history · open items |
|---|---|---|
| Lifetime | hours | permanent |
| Answers | "who is touching what **right now**" | "what we agreed, how we got here" |
| Who must read it | another working tree, **during** | whoever arrives later |
| Versioning that serves it | publish when taken | land when the work lands |

**This split is measured, not deduced.** In the project this kit came from, a lock lived **17.0 h** and was visible on the shared line for **zero** of them: the merge carried its creation *and* its removal in the same push, so the net was nothing. A peer agent checked the board during that window and read `(none)` — **correctly, per the file**. In a **second installation** the same declaration stands unexercised rather than disproved: board five days stale, both state tables empty, one history block, while the channel kept running. Its own agent's words: *"no lock was lost because none was taken — that is traffic luck, not a property of the design."*

The defect is **structural, not hygiene**. If `work/relay/` is versioned per-branch (this kit's default — `core/METHODOLOGY.md` §11 and the path list in `modules/monorepo/rules/knowledge_source_of_truth_rule.md` §2), then a lock written mid-cycle lives on that cycle's branch, and writer and reader are in different trees during exactly the window the signal exists for. Nothing an agent remembers to do fixes that.

### 4.1. The two files

- **`relay/_locks.md`** — the **live** table: `scope · owner agent · work_id · state · until · source`. Overwritten in place. A lock is a **social** signal (avoid clobbering), never a filesystem lock.
- **`relay/_board.md`** — **durable**: agreements (**proposal** vs **agreed**), an append-only `⚠ UPDATE YYYY-MM-DD` history, and open items. It describes **what has landed**, so it must not claim to be "now".

Keep the lock section in `_board.md` as a **permanent pointer** rather than deleting it: a reader who learned the old location lands somewhere correct instead of on a missing heading.

### 4.2. The requirement — and why this kit does not hand you the route

The live table needs a publication route that **does not wait for the work to land**. That is the requirement; the route is a **topology decision this kit cannot make for you**, because it depends on which line every agent reads.

Be aware that this kit's own monorepo module makes the obvious route unavailable: `git_branching_rule.md` §3.2 states *"Direct commit into `main` or `staging_*` is FORBIDDEN — no exception"*, and LLM gate 1 repeats it. So an installation has to choose deliberately:

| Route | What it costs |
|---|---|
| A narrow, **named** exception for that one file | A second exception in the branching rule. One installation did this and it is the route with the least friction — see §4.3. |
| A line that already accepts direct commits from an approved plan (`dev_*`) | Cheap, but only works if that line is a **single** read point for every agent. In a multi-app monorepo it is not. |
| One PR per lock, on a `relay`-scope branch | No rule change, and the measurement above is what it costs: the route existed, was written in two places, and the 17 h lock did not use it. A route documented and unused measures friction, not ignorance. |
| Machine-local file, outside version control | Lowest friction; loses the history that made this defect measurable in the first place. |

**Do not adopt a route by default.** Pick one, write down why, and write down what it does not fix.

### 4.3. What the exception route looked like, and the criterion that placed it

The installation that took the exception route learned two things worth carrying:

**Where a new exception goes.** The instinct is to widen the existing docs-trivial exception, and that was the worse edit: seven places in that repository described it by the two attributes it would have lost. The question that settled it generalizes to any rule with an exceptions section:

> **Are the two cases safe for the same reason?** If not, they are two sections.

The existing exception was safe by being **rare and human-judged** — a person chooses the diff, and judgement is the only bound. Live-state publication is safe for the opposite reason: **the diff is machine-bounded**, produced by a tool that only knows how to write one row in one file. Two arguments, two sections; the old one keeps its rarity claim true and measurable.

**A per-act human gate is the wrong safeguard here**, and it was dropped deliberately. Requiring a person to approve each lock makes a lock's visibility depend on someone being in the session — the same defect class, re-entered. Taking a lock only **announces**; it blocks nobody by mechanism and undoes in one row, which is the same carve-out this module already makes for `note` (§6). The safeguards that replaced the gate are a diff bound the tool enforces before pushing, plus CI checks after the fact (§9).

**Publish without switching branches.** Whoever takes a lock is mid-cycle with a dirty tree, so any route that requires `git checkout` will not be used. A throwaway `git worktree` on the shared line writes the row and leaves the working session untouched.

### 4.4. What none of this fixes, and say so out loud

**Nothing forces an agent to take a lock.** Every route above changes the cost of *publishing* a lock; none creates an obligation to declare scope. An empty table stays truthful when it says it is empty.

Say this wherever the mechanism is documented. The installation above found the criterion the hard way, from a peer that refused to offer its own mitigation as a fix on exactly this ground: *"the gate depends on the agent remembering."* A mechanism that promises **visibility** and delivers it is worth installing; the same mechanism sold as ending clobbering is not.

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

- **Machine-checked scope locks in CI.** ⚠ **The obvious shape does not work, and the reason is instructive.** A **pre-merge** hook that fails a PR touching a scope another agent holds reads the lock table **from the branch being merged** — the very tree the lock is stuck in. It has the same timing defect as the mechanism it would escalate, so it cannot be the escalation for it.

  What does have teeth, once the live table has a publication route (§4), is the **mirror** check plus two companions:

  | Check | What it catches |
  |---|---|
  | Fail a PR that carries a change to the live lock table | A lock travelling on a work branch is a lock nobody can see — the measured defect |
  | Fail a non-merge commit on the shared line that touches the lock table **and anything else** | Verifies the machine-bounded-diff claim instead of trusting the tool that makes it |
  | Fail a lock row whose `work_id` names a **closed** trio | A dead lock read as an active front — this happened, and a peer planned around it |

  ⚠ **Do not** also fail a row whose `work_id` has **no** trio in the checkout. That is the *normal* state of a live lock: the trio is in progress, so it is per-branch and absent from the shared line — the very asymmetry the live table exists to bridge. One installation shipped that condition, and it rejected every real lock on the first production attempt. It had passed its tests because the tests ran on the branch where the trio existed, which is never where the check runs.

  *Escalate when:* locks are taken but not seen. Until then, the board is advisory.
- **Structured broadcast bus** — a queue/topic instead of one-file-per-message, for many agents at high message volume. *Escalate when:* `relay/` churns faster than humans can gate. Until then, one file per message + `work_refs` greppability suffices.

Both are **not defaults** — the seed-vs-accretion principle (`docs/design-rationale.md`).

## 10. Provenance — proven vs. generalized

Be honest about maturity: unlike `cross-team` (whose hand-shape was run repeatedly before it was a skill), this module is **largely an informed generalization**.

**The board/lock split of §4 is the first piece this module got back from real use, and it arrived as a defect.** Two installations ran it. In one, a lock was taken and measured at 17.0 h of life with zero visibility, while a peer agent read the empty table and planned around it. In the other, nothing broke — and its own agent named why: no lock had ever been taken, which is traffic luck and not a property of the design. Both boards carried the same "authoritative — now" declaration against per-branch versioning. §4, the §9 correction and the path-list note in the monorepo module are what that use bought; the split itself is now **proven**, and the route remains per-installation. It applies the *proven* structural spine of `cross-team` (addressed docs, stable ask IDs, episodic-message + durable-durable split, per-claim tags, dual closing ask) to the intra-repo case, **inverting** the access premise. The **reference-first rule** and the **claim-state tags** are the new, unproven pieces — adopt them, then let real multi-agent use tell you which parts earn their keep. Prune what doesn't.
