---
name: promote-knowledge
description: Promote knowledge-layer changes from the current branch (dev_<app>) to main via an ephemeral docs/<id>__knowledge branch. Detects knowledge-layer files that diverge from main (scripts/promote_detect.py), creates a branch off main, copies the files, pushes, and instructs the human to open the PR. Use after /wiki-sync or after commits touching wiki/methodology. Agent-invocable; requires a single prior permission (yes/no).
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
- **`--all`** (optional): promote the **whole divergence** of the knowledge layer vs `main` — `DIVERGENT`, orphans included (step 2). Without it, the **default is scoped to the work_id** — `ATTRIBUTED` only, with the orphans still shown at the gate.
- **`--trio`** (optional): include the 3 trio files (`tasks/`, `plans/`, `executions/`) if `task: done` + `plan: executed` + `execution: done`.

> **Why default-scoped:** `git diff origin/main HEAD` returns the **entire** accumulated divergence (multiple works), not the current one. Under multi-session authoring on `dev_<app>`, that over-reaches. Ideal isolation is one ephemeral branch per work; scoping covers the degraded case of direct authoring on `dev_<app>`. Use `--all` deliberately.

## Steps

### 1. Validate context and resolve `work_id`

- **Resolve `<work_id>` first** — it is a prerequisite of the scoped detection in step 2. If the argument is absent, take the most recent execution in `{{project}}_wiki/work/executions/` (`in_progress` or `done`); if ambiguous, ask. Validate the `YYYY-MM-DD_slug` format.
- `git branch --show-current` → must be `dev_<app>`. If `demo_*`/`staging_*`/`main`, **abort** with a clear message.
- `git status --short` → must be empty. If dirty, instruct `commit`/`stash`.
- `git fetch origin main` to refresh refs.
- `python3 scripts/check-knowledge-paths.py` → must print `ok`. If it fails, **abort**: the mask below has drifted from rule §2, and a drifted mask promotes the wrong set silently (rule §9.1).

### 1-bis. 🔒 The source branch must not be behind its own remote — aborts

Step 6a copies from **`$SRC_BRANCH` as it exists locally**. A local `dev_<app>` that is behind
`origin/dev_<app>` promotes content that is already superseded, and nothing downstream notices: the
diff is clean, the index regenerates, CI is green.

```bash
git fetch origin "$SRC_BRANCH"
BEHIND=$(git rev-list --count "$SRC_BRANCH..origin/$SRC_BRANCH")
[ "$BEHIND" -gt 0 ] && echo "ABORT: $SRC_BRANCH is $BEHIND commit(s) behind origin/$SRC_BRANCH"
```

**Any output → abort**, tell the human to `git pull --ff-only` on the source branch, and stop. Do not
promote "the part that is current".

> **Found in use, 2026-09-12, in an installation of this module.** Step 1 fetches `origin main` only —
> it refreshes the **target** of the promotion and never the **source**. A local `dev_backend` sitting
> 2 commits behind its remote carried a stale CI workflow, which step 5-bis then flagged as a revert.
> Two gaps compounding: this one creates the hazard, that one catches it.

### 2. Detect the knowledge-layer files to promote

The canonical knowledge-layer paths (rule §2) are the **mask** in both modes, passed to the detector below. Adapt this list to the project's actual filenames at install time; it must stay **equal** to rule §2 (rule §9.1 — `scripts/check-knowledge-paths.py` verifies it):

```bash
KL_PATHS=".agents/ .claude/skills/ .claude/agents/ .claude/hooks/ .claude/settings.json \
  <per-agent-config> .mcp.json <workspace-file> <root-manifest> \
  scripts/ <ci-config> qa/ .gitattributes \
  CLAUDE.md GEMINI.md AGENTS.md README.md \
  {{project}}_wiki/_meta/ {{project}}_wiki/apps/ {{project}}_wiki/packages/ \
  {{project}}_wiki/cross-cutting/ {{project}}_wiki/decisions/ {{project}}_wiki/sources/ \
  {{project}}_wiki/benchmarks/ {{project}}_wiki/postmortems/ \
  {{project}}_wiki/overview.md {{project}}_wiki/.obsidian/"
```

**Call the mechanism. Do not re-specify the detection in shell.**

```bash
python3 scripts/promote_detect.py "$WORK_ID" --mask "$KL_PATHS"                 # text blocks
python3 scripts/promote_detect.py "$WORK_ID" --mask "$KL_PATHS" --format=json   # for programs
```

`--mask "$KL_PATHS"` is quoted on purpose: the script splits it, so the call behaves the same under
bash and zsh. The script prints **four partitions**:

| Block | What it is | What to do |
|---|---|---|
| `DIVERGENT` | knowledge files that differ from `origin/main` (three-dot: against the merge-base) | **everything** there is to promote |
| `ATTRIBUTED` | the subset touched by commits that also touched this `work_id`'s trio | the current work — the **default mode** promotes this |
| `ORPHAN` | `DIVERGENT − ATTRIBUTED` | ⚠ **show at the gate; never drop silently**. `--all` promotes these too |
| `DIVERGENT_TRIOS` | trios that differ from the base, **of any `work_id`** | trio drift; decide at the gate (`--trio` adds this work's own) |

> ⛔ **Why this way, and why the earlier step left.** This step used to infer "this work's files" from
> "files committed together with the trio". That is a **proxy, not the truth**, and in the
> installation that replaced it, it was wrong 3 times out of 3 in one day — once losing the **central
> ADR** of a trio. A controlled experiment showed the old shell block failing **both** ways at once: it
> lost an ADR committed apart from the trio **and** brought in a file from a commit **already on
> `main`**, which did not even diverge. Comparing **end states** instead of paths makes omission
> **impossible by construction**: a file is left out only if it does not diverge, and then there is
> nothing to promote. Attribution stops filtering and starts annotating.
>
> ⚠ **`{{project}}_wiki/work/` was never in the mask**, not even in `--all`; a divergent trio field
> once stayed invisible for months. That is what `DIVERGENT_TRIOS` covers.
>
> ⚠ Prose was not enough here: a shell block the agent **retypes on every run** went wrong 3 of 3. The
> mechanism is `scripts/promote_detect.py`, with a self-test in `scripts/test_promote_detect.sh` that
> includes a **negative proof** — it fails the old logic on the same scenario.

**Useful flags:** `--base <ref>` (default `origin/main`) and `--source <ref>` (default `HEAD`) audit a
historical scenario without rebuilding a branch.

**Cross-check by hand** (optional) — the same divergence, straight from git:

```bash
# `$KL_PATHS` unquoted does NOT word-split under zsh: the whole mask becomes ONE
# pathspec that matches nothing, and the command reports 0 files while a real
# divergence exists (found in use: 0 reported against 19 real). Pipe through
# xargs so the split is explicit and identical under bash and zsh.
echo "$KL_PATHS" | xargs git diff --name-only origin/main...HEAD --
```

If `--trio <id>`, add (either mode) the trio files, from `DIVERGENT_TRIOS`:

```bash
{{project}}_wiki/work/tasks/<id>.md
{{project}}_wiki/work/plans/<id>.md
{{project}}_wiki/work/executions/<id>.md
# NB: {{project}}_wiki/work/_index.md is REGENERATED in step 6b — do not copy by hand.
```

The script already filters gitignored/volatile paths (local agent settings, `.claude/projects/`, `.claude/todos/`, `{{project}}_wiki/.obsidian/workspace*.json`).

**Edge cases:**
- **No `work_id` commit touched the trio** → `ATTRIBUTED` is empty and everything divergent is an orphan. ⚠ The typical case is a trio that is **real but lives on `main`** while the code lives on `dev_<app>`: attribution runs `git log` on the *current* branch, so a trio authored on `main` is invisible to it. The files are not lost — they show up as `ORPHAN` — but do not reach for `--all` reflexively; promote the named files the human picks at the gate.
- **A knowledge file touched in a commit that did NOT touch the trio** → `ORPHAN`; the human decides at step 3.

**If `DIVERGENT`, `ORPHAN` and `DIVERGENT_TRIOS` are all empty** → report "nothing to promote" and stop.

### 3. Single gate — prior permission (yes/no)

**This is the skill's only human gate.** List the files to promote with diff size and ask for a `yes/no`:

```
I will promote to main:

  ATTRIBUTED to <work_id> (N):
    - .agents/rules/foo.md (modified, +12/-3)
    - {{project}}_wiki/decisions/2026-05-20_bar.md (new, +89)

  ORPHAN — diverge from main and are NOT attributable to this work_id (M):
    - {{project}}_wiki/apps/web/_index.md (modified, +4/-1)

  DIVERGENT TRIOS (P):
    - {{project}}_wiki/work/tasks/2026-07-08_other-work.md

Ephemeral branch: docs/<work_id>__knowledge
Confirm? (y/n)
```

⚠ **Orphans and divergent trios are ALWAYS shown**, even when M and P are zero — it is the moment the
human sees what the machine could not attribute. Omitting them reintroduces exactly the failure this
design exists to kill.

- Without an explicit `y` → **abort** (nothing created/pushed).
- With `y` → the agent runs **all following steps autonomously**, through push and the PR link, **without asking again**.

The confirmed list, one path per line, is `$FILES` in the steps below.

### 4. Confirm `work_id`

`work_id` is resolved in **step 1** — it is a prerequisite of the scoped detection in step 2, and in `--all` mode it is only needed to name the branch (step 5). Confirm the resolved value before creating the branch; nothing more to do here if step 1 already resolved it. (This heading is retained so steps 5–12 and their cross-references keep their numbers.)

### 5. Create the ephemeral branch

```bash
SRC_BRANCH=$(git branch --show-current)
git checkout main
git pull --ff-only origin main
git checkout -b docs/<work_id>__knowledge
```

### 5-bis. 🔒 Direction check — MANDATORY, BOTH MODES, aborts

> **This is a gate, not advice.** It runs after step 5 and **before any file is copied**, in scoped
> mode and in `--all` alike. On any hit the agent **aborts on its own** — no re-approval, no "confirm
> anyway" — returns to `$SRC_BRANCH`, and reports the list.

Step 6a runs `git checkout "$SRC_BRANCH" -- <list>`, which is **not a merge**: it takes the source
branch's version whatever its age. A file that is **newer on `main`** is overwritten with the older
`dev_<app>` version, and the promotion lands as a silent revert. `git diff --name-only` (the `--all`
detector) lists files that **differ**, in either direction; the scoped detector bounds *how many* files
the hazard can reach, never *which direction* they travel.

Run this over the **detected list** (the one the step-3 gate showed), not over the whole mask:

```bash
printf '%s\n' "$FILES" | while read -r f; do
  [ -z "$f" ] && continue
  # Content first: identical content cannot be a revert, whatever the timestamps say.
  git diff --quiet origin/main "$SRC_BRANCH" -- "$f" && continue
  LM=$(git log -1 --format=%ct origin/main -- "$f" 2>/dev/null)
  LD=$(git log -1 --format=%ct "$SRC_BRANCH" -- "$f" 2>/dev/null)
  [ -n "$LM" ] && [ "${LM:-0}" -gt "${LD:-0}" ] && echo "NEWER ON MAIN — would be reverted: $f"
done
```

**Any line printed → abort.** Then either drop those files from the list and re-run, or name the
promoted files explicitly. Never "promote anyway".

> ⚠ **The content test is not an optimisation; without it the check cries wolf.** Commit time moves for
> reasons content does not — a file carried along by an unrelated merge is newer on `main` and
> byte-identical. Exercised on 2026-09-12, the check produced two hits and one was exactly that.
> **A gate that aborts on harmless hits is a gate people learn to override.**

> **Two measurements from one installation.**
>
> **2026-09-11, `--all`, 19 files: 16 were newer on `main`** — every rule, ADR and page written that
> day. One commit would have reverted a day of work.
>
> **2026-09-12, scoped mode:** promoting a two-file sub-trio, the scoped detection also proposed
> `.github/workflows/checks.yml`, because one commit of that sub-trio had touched it. Copying it would
> have **deleted a CI step** together with the comment explaining it. Caught by hand only because the
> list was short enough to read.
>
> 🔑 **Scoped mode is narrower, not safer.** A check written as a precondition of one mode does not
> protect the other.

### 6. Apply the knowledge-layer files

> ⚠️ `{{project}}_wiki/work/_index.md` and `{{project}}_wiki/work/archive/*` are **GENERATED** (the `work-index` skill). **Never copy or hand-edit the index** — it is **regenerated** in step 6b. This eliminates by construction the multi-agent clobber that once required insert-only logic + an additions-only gate.

**6a. Copy the knowledge-layer files EXCEPT the index** (trio task/plan/execution + knowledge pages), **excluding** `{{project}}_wiki/work/_index.md` and `{{project}}_wiki/work/archive/*`:

```bash
# xargs, not an unquoted $FILES: zsh would pass the whole list as one path.
printf '%s\n' "$FILES" | grep -v -e '/work/_index\.md$' -e '/work/archive/' | xargs git checkout "$SRC_BRANCH" --
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

- ❌ Skipping step 1-bis or step 5-bis, or treating either as advice. They abort; they do not warn.

- ❌ Skipping the single gate (step 3).
- ❌ Introducing a second human gate (e.g. re-asking at step 7) — step 7 is a deterministic self-check.
- ❌ Promoting from `demo_*`/`staging_*` — the skill aborts at step 1.
- ❌ A branch name other than `docs/<id>__knowledge`.
- ❌ Including code changes (`apps/`, `packages/`, manifests) in the promoted diff — the skill **must** filter them out.
- ❌ Promoting `open`/`draft`/`in_progress` trios via `--trio`.
- ❌ Promoting the **total** divergence by default (over-reach). The default is scoped to the `work_id`.
- ❌ Re-specifying the detection in shell instead of calling `scripts/promote_detect.py`, or hiding the `ORPHAN` / `DIVERGENT_TRIOS` blocks from the gate.

## Cross-references

- `.agents/rules/knowledge_source_of_truth_rule.md` — the rule this skill implements.
- `.agents/rules/git_branching_rule.md` §4.1 — the allowed `__knowledge` scope.
- `.claude/skills/sync-knowledge/SKILL.md` — counterpart (pulls from main).
- `.claude/skills/wiki-sync/SKILL.md` — the typical generator of knowledge-layer changes.
