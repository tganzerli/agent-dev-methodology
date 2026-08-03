---
name: work-audit
description: Audit consistency between the declared state of the trios (work/tasks/, work/plans/, work/executions/) and the state reflected in {{project}}_wiki/work/_index.md. Detects closed tasks still listed as open, trios missing from the index, executions with a placeholder Commits field, intra-trio inconsistency, stagnant open tasks. Read-only by default; --fix applies trivial corrections (fill missing hashes, normalize dates). Use at the start of a session, before /commit, or when you suspect drift between the wiki and the real code.
argument-hint: "[--days N] [--code-check] [--fix] [--section <name>]"
allowed-tools: Bash(git *), Bash(grep *), Bash(ls *), Bash(find *), Bash(awk *), Read
---

# Work Audit

Audit of the work cycle: compares each trio's frontmatter with the human-facing showcase in `{{project}}_wiki/work/_index.md` and reports drift.

## When to use

- **Start of a session** — catches drift accumulated between sessions.
- **Before `/commit`** — ensures the index reflects the real state of the trios.
- **Periodic** (weekly/biweekly) — flags stagnant `open` tasks that deserve re-validation against code.

## When NOT to use

- To validate production code — that is the validation phase of `work-cycle`, not this audit's scope.
- *(Monorepo module only)* On a permanent branch that has no active work cycle (e.g. `demo_*` / `staging_*`) — abort there.

## Arguments

| Flag | Default | Effect |
|---|---|---|
| `--days N` | 14 | Tasks `open` for more than N days enter 🟢 INFO. |
| `--code-check` | off | Validates each `📎 path:line` in open tasks (costly — `wc -l`/`test -f` per ref). |
| `--fix` | off | Applies trivial corrections (fill `## Commits` placeholders via `git log --grep`, normalize `updated:`). |
| `--section <name>` | all | Restricts to one index section. |

`--fix` regenerates the index (`/work-index`) when there is drift and fills trivial metadata (commit placeholders, dates). It **never** modifies `status:` in the frontmatter (only a human closes a trio) and never hand-edits `_index.md`/`archive/*` (they are generated).

## Steps

### 1. Validate context

- `git branch --show-current`. *(Monorepo module only)* **Abort** on `demo_*` / `staging_*` (no active work cycle). In a single-repo project, run on whatever the working branch is.
- `git status --short` → does not require a clean tree (the audit is read-only), but **warn** if there are uncommitted changes under `{{project}}_wiki/work/` (those escape the scan).

### 2. Collect inventory

```bash
ls {{project}}_wiki/work/tasks/*.md
ls {{project}}_wiki/work/plans/*.md
ls {{project}}_wiki/work/executions/*.md
```

Skip legacy files (no `YYYY-MM-DD_slug.md` pattern) — pre-methodology work keeps legacy names and does not enter this audit.

### 3. Parse frontmatter

For each collected file, extract:

- `work_id`
- `status`
  - task: `open | in_progress | done`
  - plan: `draft | approved | executed`
  - execution: `in_progress | done`
- `updated` (date)
- `related[]` (wikilinks)
- `last_verified` (optional — if present, used by R6)

Build a `work_id × {task, plan, execution}` matrix.

### 4. Index consistency — delegated to `/work-index`

> `{{project}}_wiki/work/_index.md` and `work/archive/*` are **generated** from the frontmatter, not hand-edited. A closed task listed as open, a trio missing from the index, or an entry in the wrong section **cannot exist** — section and listing derive from the trio's own `status:`. So the index audit becomes **one** deterministic check:

```bash
python3 .claude/skills/work-index/generate.py --check --root .
```

- Exit `0` → index in sync with the frontmatter. **No drift possible.**
- Exit `1` → index **out of date** (someone changed `status`/`summary`/`topic` and did not regenerate) → 🔴. `--fix` runs the generator without `--check` to reconcile.
- Warnings on stderr (`topic` outside vocabulary, trio missing `summary`/`title`) → 🟠.

The rules below (R3+) remain — they validate the **trios' frontmatter against each other**, which the generator does not check.

### 5. Apply rules

_(R1/R2 removed — covered by `/work-index --check` in step 4.)_

#### R3 — Intra-trio inconsistency

- `task.done` + `plan.draft | approved` → 🟠.
- `plan.executed` + `task.open` → 🟠.
- `execution.done` + `task.open` → 🟠.

#### R4 — Execution metadata gap

For each execution `status: done`: parse the `## Commits` section.

- If the content reduces to `—`, `-`, `TBD`, `(fill after committing)`, or a blank line → 🟠.

#### R5 — Code-check (optional, `--code-check`)

For each task `status: open`:

- Find `📎 <path>:<line>` refs in the body.
- For each ref: `test -f <path> && [ $(wc -l < <path>) -ge <line> ]`. Failure → 🟡.

Reason: a ref may have been invalidated by a refactor. Tasks pointing at nonexistent code deserve re-investigation.

#### R6 — Stagnation

For each task `status: open`:

- `commit_date = git log --diff-filter=A --format=%cs -- <task_file> | tail -1` (creation date).
- If `(today - commit_date) > --days N` AND no recent `last_verified` (same window) → 🟢.

#### R7 — Incomplete trio

- Task with no matching plan AND the task is not a "seed" (short body, no `## Acceptance criteria`) → 🟡.
- Plan `executed` with no matching execution `done` → 🟠.
- Execution with no plan → 🔴 (real inconsistency).

### 6. Emit report

Readable markdown, grouped by descending severity:

```
Work-cycle audit — branch: <branch> — <date>

🔴 CRITICAL (N)
  - <work_id> — <rule violated>
  - ...

🟠 HIGH (N)
  - ...

🟡 MEDIUM (N)
  - ...

🟢 INFO (N — open for > --days days)
  - ...

Summary: <total> drifts.
Recommendation:
  - Handle 🔴/🟠 before the next commit.
  - --fix auto-corrects: <list>.
  - Others need a human decision (close trios, etc.).
```

### 7. (Optional `--fix`) Apply trivial fixes

**Only these corrections are considered safe:**

- **Fill `## Commits` placeholder** of a `done` execution:
  - Search via `git log --all --grep "<work_id>" --oneline`.
  - Insert the found hashes into the `## Commits` field.
  - If no commit greps, **do not invent** — leave the placeholder + a separate flag.
- **Normalize `updated:`** in the frontmatter to `git log -1 --format=%cs <file>`.

**What `--fix` never does:**

- ❌ Hand-edit `_index.md`/`archive/*` (generated — use `/work-index`).
- ❌ Change `status:` in the frontmatter (human close gate).
- ❌ Rewrite `summary:`/`topic:` of a trio (human curation; `--fix` only regenerates the index from them).
- ❌ Edit `related[]` in an execution (depends on wikilinks only the human knows).

After `--fix`, show `git diff --stat` and ask for confirmation. **Does not auto-commit.**

## Anti-patterns

- ❌ *(Monorepo module only)* Running on `demo_*` / `staging_*` (no active work cycle).
- ❌ Treating `--fix` as auto-pilot — always confirm the diff before commit.
- ❌ Auditing a legacy pre-methodology trio (no standard `status` frontmatter).
- ❌ Flagging a drift as 🔴/🟠 without citing the rule (R3-R7) violated.

## Cross-references

- `.agents/METHODOLOGY.md` — the task → plan → execution → wiki-sync cycle.
- `.agents/rules/mandatory_planning_rule.md` — plan-before-execution prerequisite.
- `.claude/skills/work-cycle/SKILL.md` — the skill that creates/updates the audited trios.
- `.claude/skills/work-index/SKILL.md` — generates `_index.md`; the deterministic check in step 4.
- `.claude/skills/commit/SKILL.md` — natural "/work-audit && /commit" flow.
