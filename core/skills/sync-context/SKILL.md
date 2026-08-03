---
name: sync-context
description: Sync the local working tree with the remote before starting new work — fetch + status + divergence report + pull with a human gate. Does not do cross-branch merges or automatic destructive operations. Use when the human invokes /sync-context or at the start of a cold session.
argument-hint: ""
disable-model-invocation: true
allowed-tools: Bash(git *)
---

# Sync Context

Ensures the local repo reflects the latest remote state before the LLM starts basing decisions on potentially outdated code/wiki. **No destructive operation (merge, rebase, reset, stash) happens without explicit confirmation.**

## When to use

- Start of a cold session after days without touching the repo.
- Before starting a new task when other devs/LLMs/machines may have updated the wiki or the code.
- Whenever you suspect "the wiki will give me stale context".

For a solo session where you know nobody else touched the repo since the last commit, this skill is unnecessary friction — skip it.

## Steps

### 1. Fetch (non-destructive)

```
git fetch --all --prune
```

Updates local refs from the remote. Changes nothing in the working tree.

### 2. Working tree check

```
git status --short
```

- **Empty output** → clean working tree, go to step 3.
- **Non-empty output** → **abort**. List modified/untracked files and instruct: "Commit, stash, or discard before syncing. I will not pull with a dirty working tree (risk of conflict or lost work)."

Never run `git stash` automatically — it hides work the human may have forgotten.

### 3. Report divergence

Current branch vs. its upstream:

```
git rev-list --left-right --count HEAD...@{u}
```

Output `A   B` means: you are `A` commits ahead, `B` behind. Interpretation:

- `0 0` → current branch in sync.
- `A 0` (A > 0) → ahead; no pull needed (push is another flow's responsibility).
- `0 B` (B > 0) → behind by B; fast-forward possible.
- `A B` (both > 0) → diverged; fast-forward is not enough — will need rebase or merge.

If the current branch is **not the default branch** (`main`), repeat against it:

```
git rev-list --left-right --count HEAD...origin/main
```

Report the divergence against `main` but **do not propose a merge automatically**. Cross-branch is a flow decision (rebase, merge, or ignore) that warrants a separate human gate — just inform.

### 4. Propose pull (current branch only)

If `B > 0`, show a preview:

```
git log HEAD..@{u} --oneline -20
```

Ask the human:

- **Fast-forward possible (`A == 0`):** `y` → `git pull --ff-only`. `n` → end without pull.
- **Divergence (`A > 0` and `B > 0`):** propose `git pull --rebase` as the default and spell out the `merge` alternative. Wait for the answer — do not choose alone. `n` → end.

After the pull, run `git status --short` plus `git log --oneline -5` and report the final state.

## Anti-patterns

- ❌ Automatic `git stash` to "clean" the working tree before a pull.
- ❌ `git pull --force`, `git reset --hard`, or any operation that discards local commits without an explicit request.
- ❌ Automatic merge of the default branch into another branch (cross-branch is a human decision).
- ❌ Pulling with a dirty working tree.
- ❌ Silent pull without showing the `git log` preview.
- ❌ Running `git push` here. This skill is ingress only.
- ❌ Choosing between `rebase` and `merge` without asking — those are project/dev preferences and vary.

## Cross-references

- *(Monorepo module only)* `/sync-knowledge` — to sync only the **knowledge layer** between the current branch and the canonical branch (a more surgical subset). Installed by the monorepo module; use it after `/sync-context` if the current branch diverges from the canonical one in wiki/methodology and you want to align only the knowledge without mixing code changes.
