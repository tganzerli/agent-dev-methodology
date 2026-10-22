---
name: reset-dev-branch
description: Reset the local dev_<app> to its remote after its content was already promoted (docs/__knowledge PR merged + broadcast received). A script decides, read-only, that no content is local-only; the skill creates a backup branch and only then runs `git reset --hard origin/<branch>`. Use when the branch shows "ahead" with no extra content.
argument-hint: ""
disable-model-invocation: true
allowed-tools: Bash(git *), Bash(python3 *), Read
---

# Reset Dev Branch

Resets the local `dev_<app>` to `origin/<branch>` **after** `/promote-knowledge` carried its content to `main` and the broadcast brought it back.

> **Monorepo module skill.** In a single-repo project there is no promote/broadcast round trip, and this skill does not apply.

## Why it exists

`/promote-knowledge` does not carry commits: it copies the **end state** of files to a `docs/<id>__knowledge` branch cut from `main` (`knowledge_source_of_truth_rule.md` §3.2). The content returns through the broadcast, but the authoring commits stay only on `dev_<app>`, with other hashes, and git counts them "ahead" forever. Measured in one installation: 27 commits ahead, none with code, a tree **identical** to the remote's.

⛔ **The criterion is not "0 ahead"** (that is the goal, not the condition). It is **"no local-only content"**: for every file the local commits touched, the remote's version is identical — deletions included. `scripts/dev_branch_reset.py` decides (self-test with a negative proof in `scripts/test_dev_branch_reset.sh`).

**Mandatory human gate.** `disable-model-invocation: true`: it rewrites local history, so it runs only on explicit invocation. The controls are the script and the `[y/n]` of step 4 (`git_branching_rule.md`, destructive operations).

## When to use

- After a `docs/<id>__knowledge` PR was **merged** and the **broadcast reached** the `dev_<app>` (the remote already has the content).
- When `git status -sb` shows the branch "ahead" and you suspect it is only hashes.

## When NOT to use

- On `main`, `staging_*`, `demo_*` or `dev_packages` — the script refuses.
- Before the broadcast: the remote does not have the content yet; the script refuses ("local only"), and that is not an error.
- With an uncommitted change to a tracked file — the script refuses.
- If the branch is **0 ahead** and only behind: `git merge --ff-only origin/<branch>` is enough (nothing rewritten, no backup).

## Steps

### 1. Validate context

- `git branch --show-current` → must be `dev_<app>`. Announce every Git command to the human.

### 2. Decide (read-only)

```bash
python3 scripts/dev_branch_reset.py            # runs `git fetch` and prints the report; writes nothing
```

Exit `0` = safe · `1` = refused · `2` = error. `--format json` for programs; `--no-fetch` to skip the fetch.

### 3. If refused: stop

Show the `FAIL` items and guide — **never** insist:

| Reason | What to say |
|---|---|
| `5. no local-only content` | A file the remote lacks (or has differently). Promote with `/promote-knowledge` and wait for the broadcast, or inspect the listed file. |
| `2. clean tracked tree` | Commit or stash the change. |
| `3. no git operation in progress` | Finish or abort the merge/rebase/cherry-pick. |
| `1. branch is a dev_<app>` | Wrong branch. |
| `4. origin/<branch> exists` | No network, or the branch does not exist. |

### 4. If safe: the only gate

If `ahead: 0` there is nothing to rewrite: suggest `git merge --ff-only origin/<branch>` and stop. Otherwise show:

```
I will reset <branch> to origin/<branch>:
  local commits leaving the branch: N (M merges)   — preserved in backup/<branch>-<date>
  files those commits touched: K (none local-only)
  undo: git reset --hard backup/<branch>-<date>
Confirm? [y/n]
```

Without an explicit `y` → **run nothing**.

### 5. Apply

```bash
python3 scripts/dev_branch_reset.py --apply --expect-head <short-sha-from-the-report>
```

The script **re-decides** (the remote may have moved), refuses if `--expect-head` does not match the current HEAD, creates `backup/<branch>-<YYYY-MM-DD>` (`-2`, `-3` if taken), runs `git reset --hard origin/<branch>`, and checks that HEAD's tree is the remote's. Report the backup and the undo command.

### 6. Backup

Do not delete the backup without asking: `branch -D` of an unmerged branch is a destructive operation (`git_branching_rule.md`).

## Anti-patterns

- ❌ `git reset --hard` by hand. This is the sanctioned path.
- ❌ Applying without `--expect-head`, or with a sha copied from another run.
- ❌ Running before the broadcast and "forcing" after the refusal.
- ❌ Using it to discard work that was **not** promoted: the script refuses exactly that.
- ❌ Deleting the backup branch right away.

## Cross-references

- `scripts/dev_branch_reset.py`, `scripts/test_dev_branch_reset.sh`
- `.claude/skills/promote-knowledge/SKILL.md` — the predecessor (promotes); `.claude/skills/sync-knowledge/SKILL.md` — pulls from `main`
- `.agents/rules/git_branching_rule.md` (destructive operations), `.agents/rules/knowledge_source_of_truth_rule.md` §3.2
