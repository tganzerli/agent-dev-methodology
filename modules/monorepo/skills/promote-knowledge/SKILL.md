---
name: promote-knowledge
description: Promote knowledge-layer changes from the current branch (dev_<app>) to main via an ephemeral docs/<id>__knowledge branch. Detects knowledge-layer files changed since the last merge with main, creates a branch off main, copies the files, pushes, and instructs the human to open the PR. Use after /wiki-sync or after commits touching wiki/methodology. Agent-invocable; requires a single prior permission (yes/no).
argument-hint: "[work_id (optional — uses context)] [--all (promote the whole divergence vs main)] [--trio (include the task/plan/execution trio if closed)]"
disable-model-invocation: false
allowed-tools: Bash(git *), Bash(python3 *), Read, Write
---

# Promote Knowledge

Promotes **knowledge-layer** changes from the current branch to `main` via the ephemeral branch `docs/<work_id>__knowledge`. Implements `.agents/rules/knowledge_source_of_truth_rule.md` §3.2.

> **Monorepo module skill.** In a single-repo project there is no `main`/`dev_<app>` split — this skill collapses to a no-op and must not be installed.

## Agent execution (single gate)

This skill **can be run by agents** (model-invocable and by sub-agents). It requires **one prior human permission** — a `yes/no` at **step 3**. Once `yes` is given, the agent runs the rest autonomously (branch → copy → regenerate index → commit → push → PR link) **with no further human gates**.

The **step 7** checks are **deterministic automatic verifications**: on failure the agent **aborts on its own**, returns to the original branch, and reports why — it does **not** ask for re-approval. Merging the PR into `main` remains a human action in the git host (out of scope here).

## When to use

- **After `/wiki-sync`** on `dev_<app>` — the local sync stays in dev; this skill promotes it to main.
- **After directly editing** any knowledge-layer file on `dev_<app>` (e.g. an ADR, a domain page).
- **When a trio closes** (with `--trio <id>`) — promotes its tasks/plans/executions to main.

## When NOT to use

- On `demo_<app>` / `staging_<app>` — outside the automatic flow (rule §4).
- On `main` directly — main does not promote to itself.
- With uncommitted changes — commit first.
- For code changes (`apps/`, `packages/`) — code has its own flow (`dev → staging → main` via normal PR).

## Argument

- **`<work_id>`** (optional): `YYYY-MM-DD_slug`. If omitted, infer from the most recent execution log or ask.
- **`--all`** (optional): promote the **whole divergence** of the knowledge layer vs `main` (legacy). Without it, the **default is scoped to the work_id** — only files touched by the trio's commits (step 2).
- **`--trio`** (optional): include the 3 trio files (`tasks/`, `plans/`, `executions/`) if `task: done` + `plan: executed` + `execution: done`.

> **Why default-scoped:** `git diff origin/main HEAD` returns the **entire** accumulated divergence (multiple works), not the current one. Under multi-session authoring on `dev_<app>`, that over-reaches. Ideal isolation is one ephemeral branch per work; scoping covers the degraded case of direct authoring on `dev_<app>`. Use `--all` deliberately.

## Steps

### 1. Validate context

- `git branch --show-current` → must be `dev_<app>`. If `demo_*`/`staging_*`/`main`, **abort** with a clear message.
- `git status --short` → must be empty. If dirty, instruct `commit`/`stash`.
- `git fetch origin main` to refresh refs.

### 2. Detect the knowledge-layer files to promote

The canonical knowledge-layer paths (rule §2) are the **mask** in both modes. Adapt this list to the project's actual filenames at install time:

```bash
KL_PATHS=".agents/ .claude/skills/ <per-agent config> .mcp.json \
  CLAUDE.md GEMINI.md AGENTS.md README.md <workspace file> \
  {{project}}_wiki/_meta/ {{project}}_wiki/apps/ {{project}}_wiki/packages/ \
  {{project}}_wiki/cross-cutting/ {{project}}_wiki/decisions/ {{project}}_wiki/sources/ \
  {{project}}_wiki/overview.md {{project}}_wiki/.obsidian/ \
  scripts/ <CI pipeline config> <root workspace manifest> qa/"
```

**Default mode — scoped to `<work_id>`** (only files touched by the trio's commits):

```bash
# commits that touched ANY trio file for this work_id
FILES=$(git log --format=%H -- \
    "{{project}}_wiki/work/tasks/${WORK_ID}.md" \
    "{{project}}_wiki/work/plans/${WORK_ID}.md" \
    "{{project}}_wiki/work/executions/${WORK_ID}.md" \
  | while read -r c; do git show --name-only --format= "$c"; done \
  | sort -u | grep -E '<KL path regex adapted to this project>')
# NB: `git log … | while read` (not `for c in $COMMITS`) — robust under bash AND zsh;
# zsh does not word-split an unquoted variable, which would break the loop.
```

If no commits touched the trio → **abort** with instructions (never fall silently into the total divergence).

**`--all` mode — total divergence vs `main`** (legacy):

```bash
git diff --name-only origin/main HEAD -- $KL_PATHS
```

If `--trio <id>`, add (either mode):

```bash
{{project}}_wiki/work/tasks/<id>.md
{{project}}_wiki/work/plans/<id>.md
{{project}}_wiki/work/executions/<id>.md
# NB: {{project}}_wiki/work/_index.md is REGENERATED in step 6b — do not copy by hand.
```

**Filter gitignored** explicitly (do not promote): local agent settings, `.claude/projects/`, `.claude/todos/`, `{{project}}_wiki/.obsidian/workspace*.json`.

**Edge cases:**
- **Work with no trio** (default) → abort with instructions.
- **Work spread across commits** → `git log -- <trio>` already catches every commit that touched the trio; the union covers the work.
- **A knowledge file touched in a commit that did NOT touch the trio** → out of scope; the gate (step 3) shows the list and the human may request `--all` or name the range.

**If the list is empty** → report "nothing to promote" and stop.

### 3. Single gate — prior permission (yes/no)

**This is the skill's only human gate.** List the files to promote with diff size and ask for a `yes/no`:

```
I will promote N knowledge-layer files to main:
  - .agents/rules/foo.md (modified, +12/-3)
  - {{project}}_wiki/decisions/2026-05-20_bar.md (new, +89)
  - ...
Ephemeral branch: docs/<work_id>__knowledge
Confirm? (y/n)
```

- Without an explicit `y` → **abort** (nothing created/pushed).
- With `y` → the agent runs **all following steps autonomously**, through push and the PR link, **without asking again**.

### 4. Resolve `work_id`

> **Order:** in **default (scoped) mode** the `work_id` is a prerequisite of step 2 — resolve it **before** detecting files. In `--all` mode it is only needed to name the branch (step 5) and may be resolved here.

If the argument is absent: look at `{{project}}_wiki/work/executions/` and take the most recent execution (`in_progress` or `done`). If ambiguous, ask. Validate the `YYYY-MM-DD_slug` format.

### 5. Create the ephemeral branch

```bash
SRC_BRANCH=$(git branch --show-current)
git checkout main
git pull --ff-only origin main
git checkout -b docs/<work_id>__knowledge
```

### 6. Apply the knowledge-layer files

> ⚠️ `{{project}}_wiki/work/_index.md` and `{{project}}_wiki/work/archive/*` are **GENERATED** (the `work-index` skill). **Never copy or hand-edit the index** — it is **regenerated** in step 6b. This eliminates by construction the multi-agent clobber that once required insert-only logic + an additions-only gate.

**6a. Copy the knowledge-layer files EXCEPT the index** (trio task/plan/execution + knowledge pages), **excluding** `{{project}}_wiki/work/_index.md` and `{{project}}_wiki/work/archive/*`:

```bash
git checkout "$SRC_BRANCH" -- <detected list WITHOUT _index.md and archive/*>
```

**6b. Regenerate the index from frontmatter:**

```bash
python3 .claude/skills/work-index/generate.py --root .
git add {{project}}_wiki/work/_index.md {{project}}_wiki/work/archive/
```

The branch was cut from `main` (step 5) → it already contains **all trios of all apps**. The generator reads every frontmatter + the freshly copied trio, so the output **includes every app's entries** — clobber is impossible. (Prerequisite: the promoted trio must have `summary`/`topic` in frontmatter, else the generator falls back to `title`.)

### 7. Verify the staged diff

```bash
git status --short
git diff --cached --stat
```

- In `_index.md`/`archive/*`, the change must be **only the promoted `<work_id>`'s line(s)** (+ a possible roll into `archive/` on a quarter boundary). If **another** app lost a line, its trio lacks `summary`/`topic` in `main` yet — reconcile before committing.
- Deterministic sanity: `python3 .claude/skills/work-index/generate.py --check --root .` must exit `0` after `git add`.

**Automatic check (no human gate).** This step does **not** ask for approval — permission was granted at step 3. If `--check` exits `≠ 0`, or another app lost an index line, the agent **aborts automatically**, returns to `$SRC_BRANCH` (step 11), and reports why. If the checks pass, proceed straight to commit.

### 8. Commit

```bash
git commit -m "docs(knowledge): promote <work_id> from <SRC_BRANCH>

Promotion of the knowledge layer from <SRC_BRANCH> to main per
.agents/rules/knowledge_source_of_truth_rule.md §3.2.

Files:
- ...
"
```

### 9. Push

```bash
git push -u origin docs/<work_id>__knowledge
```

### 10. Instruct PR opening

Print the git host's "new PR" URL for `docs/<work_id>__knowledge → main`. Remind the human: the PR targets `main` (not dev/staging), and merging it is their action.

### 11. Return to the original branch

```bash
git checkout "$SRC_BRANCH"
```

### 12. Suggest `/sync-knowledge` on sibling `dev_<app>`

If another `dev_<app>` is active, suggest: "After the PR merges, run `/sync-knowledge` on `dev_<other>` to receive it." (In this setup the CI broadcast usually delivers it automatically — a manual sync is only a fallback.)

## Anti-patterns

- ❌ Skipping the single gate (step 3).
- ❌ Introducing a second human gate (e.g. re-asking at step 7) — step 7 is a deterministic self-check.
- ❌ Promoting from `demo_*`/`staging_*` — the skill aborts at step 1.
- ❌ A branch name other than `docs/<id>__knowledge`.
- ❌ Including code changes (`apps/`, `packages/`, manifests) in the promoted diff — the skill **must** filter them out.
- ❌ Promoting `open`/`draft`/`in_progress` trios via `--trio`.
- ❌ Promoting the **total** divergence by default (over-reach). The default is scoped to the `work_id`.

## Cross-references

- `.agents/rules/knowledge_source_of_truth_rule.md` — the rule this skill implements.
- `.agents/rules/git_branching_rule.md` §4.1 — the allowed `__knowledge` scope.
- `.claude/skills/sync-knowledge/SKILL.md` — counterpart (pulls from main).
- `.claude/skills/wiki-sync/SKILL.md` — the typical generator of knowledge-layer changes.
