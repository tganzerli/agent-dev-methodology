---
name: peer-relay
description: Coordinate with the agent of ANOTHER project on the same machine — separate repositories that can read each other. Covers absorption (orienting in the peer's repo without sweeping it), sending a message to its inbox, reading our inbox, and the shared board. Use when you need to ask, answer, warn or hand work to a project declared in .agents/peers.md. Do not use it for agents of this same repository (that is `intra-team`) or for teams with no access to our code (that is `cross-team-handoff`).
argument-hint: "[absorb <peer> | send <peer> <slug> | read <peer> | board]"
---

# Peer-relay — coordination between projects on the same machine

The third value of an axis the other two modules treat as binary. `modules/intra-team/README.md` states it: *"they differ on one axis — does the reader share your repository?"*

| | `cross-team` | `intra-team` | **`peer-relay`** |
|---|---|---|---|
| The reader **shares** your repo | no | yes | **no** |
| The reader **can read** your repo | no | yes | **yes** |
| Rule | self-contained | reference-first | **qualified reference-first** |

It **imports the `intra-team` machinery** — the five `msg_role`s (`note`/`request`/`response`/`handoff`/`conflict`), the stable-ID ask table, the round log, the board. Read `.claude/skills/intra-team/SKILL.md` for all of them; **they are not repeated here.** What follows is only the delta.

## Prerequisites

- `.agents/peers.md` declares the peer: path, prefix, write policy, inbox, absorption entry points.
- `{{project}}_wiki/work/relay/` exists, with `_board.md` and `_templates/peer-message.md`.
- Prose in {{KNOWLEDGE_LANG}}.

## Delta 1 — the citation rule

The reason the module exists. In a two-repository universe, `router.dart:9` exists **in both** and means different things.

1. 🔒 **Every file citation carries a repo prefix.** `{peer}:lib/src/decoder/_decoder.dart:56`, `{{project}}:packages/domain/lib/src/value/enums.dart:1-3`. The prefix comes from `.agents/peers.md`. A `file:line` without a prefix is a **format error**, not style.
2. **Citing the reader's repo: pure reference-first.** They open the file. Do not re-paste.
3. **Citing our repo: reference-first *with a sufficient inline summary*.** They *can* open it, but they are in another checkout with another context loaded and **will not**. The claim stands alone in the body; the citation stays as verifiable provenance. It is the middle ground neither of the other two modules offers, and the easiest mistake, because "reference-first" invites you to just point.
4. **`[[wikilinks]]` only for pages in the reader's repo.** Vaults are separate: a wikilink into our vault is a dead link in their Obsidian. For our pages, a prefixed file path.
5. **A `work_id` is namespaced on crossing:** `{{project}}:2026-09-06_backend-foundations-track`. Both projects use `YYYY-MM-DD_slug`; a collision is a matter of time.
6. **Claim-state gains an axis.** `intra-team` distinguishes `✅ landed` / `⚠ in-flight` / `🔒 intent`. Here `landed` alone says nothing — landed **where**? Format: `✅ landed ({{project}}@main)`, `⚠ in-flight ({{project}}@docs/…__knowledge)`.

## Delta 2 — the four flows

### `absorb <peer>` · autonomous

Orients you in the peer's repo **reading only the declared entry points**, in their order, stopping when the question at hand is answered.

🔒 **Never sweep the peer's repository.** The registry exists to avoid that: a `grep -r` in someone else's repo burns context and produces a map their `overview.md` already gives in one page.

🔒 **Do not pattern-match on a section name.** A peer may write its knowledge in another language — `## Em andamento` instead of `## In progress`. A cut anchored on the wrong heading returns empty, and empty reads as "there is nothing", a false and silent conclusion. **List the headings first** (`grep -n '^#'`) and cut by what exists.

Also read the peer's **quirks** in the registry before concluding anything — they are exactly the points where an index lies (a stale `_index.md`, a local tag, a dead lock).

Output: a state summary — what the project is, what is in flight, what is locked, and what in your question is still unanswered.

### `send <peer> <slug>` · **DOUBLE HUMAN GATE**

Drafts the message in `{{project}}_wiki/work/relay/{YYYY-MM-DD}_{slug}.md` (template `peer-message.md`) and **delivers it by Pull Request** in the peer's repository.

🔒 **Delivery is a PR, never a loose file in the peer's working tree.** Dropping the file straight into their directory looks simpler and is worse in three ways: it **arrives in silence** (nothing tells the agent there it exists), it can be **swept into someone else's commit** by a broad `git add`, and it disappears on a `git clean`. A PR has a reviewer, history, notification and reversal. *(Origin: review of the mechanism before an installation's first real send.)*

🔒 **The PR obeys the branching rule of the repository that RECEIVES it, not the one that sends.** The two repositories may have different topologies — one with knowledge canonical in `main`, another with `main` as a release line and ephemerals landing in `dev`. Assuming our topology produces a PR that violates the reader's rule on the first message. The registry (`.agents/peers.md`) declares, per peer: **base branch**, **PR target**, **type** and **scope** of the branch name. If the registry does not declare them, **stop and ask** — do not deduce them from our rule.

🔒 **The delivered copy is stamped for the reader.** In the file you deliver, `direction: inbound` and `peer: {{project}}`; our own copy stays `direction: outbound`, `peer: <peer>`. A delivery carrying our outbound frontmatter is invisible to the peer's inbox reader. This has happened, four times in a row, before anyone noticed.

🔒 **Never merge the PR in the peer's repository.** Opening it is delivery; merging it is deciding for the other project. The merge belongs to the other side, to whoever reviews.

🔒 **Two gates, not one.** (a) the human approves the **text**; (b) the human approves **opening the PR in the other project's repository**. They are different decisions: the second is an external action and creates a branch and a commit in a repository that is not ours.

🔒 **Before drafting, read the peer's board** (`<peer>:…/work/relay/_board.md`) and ours. Writing about a locked scope without acknowledging the lock is exactly the clobbering the board exists to prevent.

🔒 **The PR diff is a single new file**, under the relay directory declared in the registry. No file outside it, no code change, no commit on a permanent branch of the peer.

**Procedure:**

1. Read the peer's delivery configuration in the registry (base, target, type, scope, frontmatter).
2. Check that the base is up to date (`git -C <path> fetch`), and create the ephemeral branch from it — through a `git worktree`, never `git checkout` in their working tree.
3. Commit **only** the message file, with the commit message in the language the peer uses for commits.
4. `push` + open the PR, with a body that says in one line what it is and that the decision to incorporate belongs to the reviewer.
5. **Do not merge.**

After delivery: append to `{{project}}_wiki/_meta/log.md` (`## [YYYY-MM-DD] peer-relay | {slug} | to {peer} | PR <url>`) and, if the message creates a lock or an agreement, update the board. Record the **PR URL** — it is what makes the delivery auditable later.

### `read <peer>` · autonomous

Run `python3 .claude/skills/peer-relay/inbox.py <peer>`. It lists the peer's `direction: inbound` messages in **two states**: merged into `origin/main` (pending, `status: sent|read`; `--all` shows all) and **delivered in an open PR** against `main`, not merged yet. Peers deliver by PR, so a new message passes through the second state first. Reading the working tree is not enough: it does not see the PR, and it shows the session's branch, not `main`. It also lists relay files in open PRs that are **not** stamped `inbound`/`<peer>` — a peer that delivered its outbound copy unchanged.

🔒 **Empty counts only with exit `0`.** Exit `2` means the open PRs were not checked (`gh` missing or failing, or a host other than GitHub) or the `fetch` failed; tell the human that, not "there are no messages".

🔒 **Never conclude the peer did not deliver** without exit `0`. A false negative on an open PR, read as absence, once turned into a request to chase the peer for a reply it had already sent.

Then summarize what needs an answer, prioritizing asks flagged 🔴. A message in an open PR is read from the PR; to move it to `status: read` or `answered`, the commit goes **on the PR's branch**, before the merge.

A message read becomes `status: read`; answered, `answered`. **Do not** close an ask unless the answer actually exists.

### `board` · human gate

Maintains `{{project}}_wiki/work/relay/_board.md`. Locks whose scope lives in the peer's repo carry **its prefix** in the Scope column (`{peer}:lib/`).

A lock here is a **social** signal, not a filesystem lock — and across repositories it is even more fragile, because the other agent may not have looked. When you lock a scope that crosses the boundary, **say so in the message**; do not rely on the board alone.

## Delta 3 — what the message carries in addition

The `peer-message.md` template extends `intra-team`'s `message.md` in three places:

- **Frontmatter:** `peer` (name in the registry), `peer_work_refs` (their work_ids) and `work_refs` (ours) — **separate**, because there are two namespaces.
- **"Orientation" section**, right after Context: where, **in the reader's repo**, the things the message discusses live. It saves a whole round spent on "where is that?".
- **Third closing ask:** where to deposit the answer (our inbox, absolute path). Unlike `intra-team`, there is no obvious shared place.

## Anti-patterns

- ❌ `file:line` without a repo prefix.
- ❌ A `[[wikilink]]` pointing into our vault in a message that leaves here.
- ❌ Sweeping the peer's repository instead of using the entry points.
- ❌ Writing into the peer's repo without the second gate, or outside the registry's policy.
- ❌ **Dropping the file straight into the peer's working tree.** Delivery is a PR.
- ❌ **Applying OUR branching rule to the PR that enters their repo.** Theirs applies.
- ❌ **Merging the PR in the peer's repository.** Opening is delivery; merging is deciding for the other project.
- ❌ Delivering our outbound copy unchanged (`direction: outbound`, `peer: <them>`). Their inbox reader will not list it.
- ❌ Only pointing at `{{project}}:file:line` without the inline summary — the reader will not open it.
- ❌ Using this module for an agent of **this** repo (that is `intra-team`) or for a team with no access to our code (that is `cross-team-handoff`).
- ❌ Marking an agreement as `A` on the board before the other side's real ack.
- ❌ Concluding "the peer did not deliver" from the working tree alone, without checking open PRs (`inbox.py`, exit `0`).

## References

- `.agents/peers.md` — the registry.
- `.claude/skills/intra-team/SKILL.md` — the inherited machinery.
- `.claude/skills/cross-team-handoff/SKILL.md` — the case without code access.
- `{{project}}_wiki/_meta/conventions.md` §"Peer-relay frontmatter".
