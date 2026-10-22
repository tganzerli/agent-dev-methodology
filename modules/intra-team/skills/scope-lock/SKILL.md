---
name: scope-lock
description: Take or release a scope lock — the declaration that an agent is touching a scope right now. Publishes the row directly on the shared line, from inside your work branch, without switching branches or opening a PR. Use when you start touching code another agent (of this repo or of a peer) could touch, and when the work lands. For agreements, history or open items use `intra-team` (the board), not this. OPT-IN reference route of the intra-team module; install only together with the live-state exception in the branching rule.
argument-hint: "take --scope <path> --owner <agent> --work-id <id> --until <condition> --source <link> | release --scope <path>"
---

# Scope lock

> **Opt-in reference route** for `modules/intra-team/README.md` §4.2. It is valid only if the project's branching rule carries the live-state exception (`modules/intra-team/snippets/branching-live-state-exception.md`). Without that exception, this script commits directly to a protected line in violation of the rule.

## What this solves

A lock written into `_board.md` mid-cycle **stays on that cycle's branch**, so it is invisible during exactly the window it exists for. Measured: a lock lived **17.0 h** and was visible on the shared line for **zero** of them; a peer agent read the empty table, correctly per the file.

This skill publishes the row **directly on the shared line** (default `main`) through a throwaway `git worktree`, without touching your working tree.

## Invocation

**Agent-invocable, with no per-act human gate — deliberately.** A lock **announces**; it blocks nobody by mechanism and undoes in one row. Requiring a person would make a lock's visibility depend on someone being in the session, which is the defect this skill fixes. It is the same carve-out `intra-team` makes for `note`.

The safeguard is the diff bound, not a gate: `publish.sh` checks that the staged diff is **exactly** the lock file and aborts otherwise. CI can verify it after the fact (README §9).

**Every other write to `_board.md` keeps the `intra-team` human gate.**

## When to take

- When you start touching code another agent could touch — the plan says so.
- The **narrowest** scope that serves: the subdirectory, not the package.
- A scope that lives in a peer repo carries the peer prefix: `<peer>:src/module/`.

## When to release

**In the PR that lands, not before or after.** Releasing early opens the scope while the merge is pending; releasing late leaves the table lying for a window. In practice: run `release` when the merge happens.

## Usage

```bash
# Take
.claude/skills/scope-lock/publish.sh take \
  --scope   "src/module/" \
  --owner   "<model>/work-cycle" \
  --work-id "<work_id>" \
  --until   "landing of the PR" \
  --source  "[[work/plans/<work_id>]]"

# Release (changing state means release + take)
.claude/skills/scope-lock/publish.sh release --scope "src/module/"
```

Environment: `SCOPE_LOCK_FILE` (default `<the single *_wiki>/work/relay/_locks.md`), `SCOPE_LOCK_REMOTE` (default `origin`), `SCOPE_LOCK_RULE` (default `.agents/rules/git_branching_rule.md`), `SCOPE_LOCK_LINE` (default `main`).

`SCOPE_LOCK_LINE` is **unsupported for any line other than the one shared line the installed exception names.** The push carries no human gate, so the script refuses to run unless the branching rule names both that line and the lock file. It also refuses when the snippet is not installed at all.

A rejected push prints git's message. Only a moved line (`fetch first` / `non-fast-forward`) is retried, up to three times; a protected-branch, auth or hook rejection fails at once. Either failure is a lock that **could not be published** (see below).

After either command, your session's `git status` is **the same as before**. If it is not, that is a bug: report it rather than work around it.

## Reading the state

Reading is `cat`, not a command. The shared line's copy is the correct one; your branch's copy is a snapshot of when you branched.

```bash
git fetch --quiet origin main && git show origin/main:<vault>/work/relay/_locks.md
```

## Collision

`take` on a scope that is already held **fails** and does not overwrite. A collision is resolved through the `intra-team` `conflict` flow (human-gated). A `take` that overwrote the other row would be the clobbering the lock exists to prevent.

## Known limits — two cases, and the second is worse

**1. Nothing forces an agent to take a lock.** This skill drops the cost of publishing one, from "branch + PR" to one command. Forgetting is still possible, and an empty table is still telling the truth when it says it is empty. The skill promises **visibility**, not obligation.

**2. Nothing guarantees you will be able to publish.** Tool capability can vary **per session, without warning**: the same call runs in one session and is refused in the next, with no configuration change. A blocked lock produces the **same** empty table as a forgotten one, and then a scope is being touched while another agent reads "none", correctly.

> **If `take` does not complete, stop and say so.** Record in the execution log that the lock was **attempted and blocked**, naming the intended scope, and tell the human at once.
>
> **Do not try to diagnose why it was blocked.** The attempt produces a plausible, false explanation; this was measured.
>
> **Do not keep touching the scope without a lock and without a mention.** That is where the block becomes invisible, which is exactly the defect this skill exists to fix.

## Anti-patterns

- ❌ Editing `_locks.md` by hand, on your branch or on the shared line.
- ❌ Committing `_locks.md` together with anything else.
- ❌ Leaving a lock on a closed trio — a peer has read one as an active front.
- ❌ Using this skill for agreements, history or open items. That is the board, and the board is `intra-team` (Flow F, gated).
- ❌ `--until` with a guessed date. The column wants the **condition** that ends the lock.
