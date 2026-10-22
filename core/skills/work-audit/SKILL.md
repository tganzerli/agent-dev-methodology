---
name: work-audit
description: Audit consistency between the declared state of the trios (work/tasks/, work/plans/, work/executions/) and the state reflected in {{project}}_wiki/work/_index.md. Detects index drift, trios delivered but not closed (work already on the release line while the execution says in_progress), executions with no traceable Commits, intra-trio inconsistency, incomplete trios, frontmatter the index cannot validate, stagnant open tasks. Read-only by default; --fix applies only deterministic corrections (normalize dates, regenerate the index) and never fills Commits. Use at the start of a session, before /commit, or when you suspect drift between the wiki and the real code.
argument-hint: "[--days N] [--code-check] [--fix] [--section <name>] [--release <branch>]"
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
| `--fix` | off | Applies only **deterministic** corrections (normalize `updated:`, regenerate the index). Never writes `## Commits` — see step 7. |
| `--section <name>` | all | Restricts to one index section. |
| `--release <branch>` | remote default branch | The release line R8 searches for delivered commits. |

`--fix` regenerates the index (`/work-index`) when there is drift and normalizes dates. It **never** writes `## Commits`, **never** modifies `status:` in the frontmatter (only a human closes a trio) and never hand-edits `_index.md`/`archive/*` (they are generated).

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

Files without the `YYYY-MM-DD_slug.md` pattern (pre-methodology or misnamed) are not parsed by R3–R8, but they are **not silently dropped**: R9 lists each one from the `/work-index` skip warning, so the human decides whether to rename it or leave it as legacy.

### 3. Parse frontmatter

For each collected file, extract:

- `work_id`
- `status`
  - task: `open | in_progress | future | paused | done | cancelled | aborted`
  - plan: `draft | approved | executed | cancelled | aborted`
  - execution: `in_progress | done | aborted`

  Three vocabularies, one per `type` — auditing all three against one list produced hundreds of false positives in one installation.
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
- `✗` lines on stderr (plan without task, plan status contradicting its execution) also exit `1` → 🔴.
- `⚠` warnings on stderr → R9.

The rules below (R3+) remain — they validate the **trios' frontmatter against each other**, which the generator does not check.

### 5. Apply rules

_(R1/R2 removed — covered by `/work-index --check` in step 4.)_ The rules are numbered by age, not by order of application.

#### R3 — Intra-trio inconsistency

- `task.done` + `plan.draft | approved` → 🟠.
- `plan.executed` + `task.open` → 🟠.
- `execution.done` + `task.open` → 🟠.

#### R4 — Execution metadata gap

For each execution `status: done`: can the delivered code be reached from it? The criterion is **traceability**, not a hash.

| Content (searched in the **whole** execution, not only `## Commits`) | Verdict |
|---|---|
| Commit hash(es) | ✅ |
| A named **ephemeral** branch (`<type>/<work_id>__<scope>`) — the host's merge commit names it, so `git log <main> --grep "<branch>"` reaches the code; require **exactly one** match | ✅ |
| An explicit statement that no code was committed (e.g. a diagnosis-only stage) | ✅ |
| `—`, `-`, `TBD`, `<sha>`, `(fill after committing)`, `(pending)`, empty | 🟠 |

⛔ **A permanent branch is not traceability** — `dev` or `main` matches hundreds of merge commits, and an ambiguous match is indistinguishable from a hit if only the first result is read. Look for the branch in the whole document: restricting the search to `## Commits` doubled the false gaps in one installation (51 vs 22), because the branch usually lives in the metadata block.

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

#### R8 — Delivered but not closed

For each trio whose **execution is `in_progress`** (only that status — see the calibration note):

```bash
REL=$(git symbolic-ref --short refs/remotes/origin/HEAD 2>/dev/null || echo origin/main)  # or --release <branch>
git log "$REL" --oneline --grep "<work_id>" | wc -l
```

- ≥1 commit on the release line → 🟠, reporting the count and the trio's age.

The release line is the remote's default branch (`origin/HEAD`), or the branch passed as `--release <branch>` when work is delivered elsewhere (e.g. a `dev` integration branch). If neither resolves, say so and skip R8 — do not report it clean.

R3–R7 cannot see this: a trio whose whole status fell behind is **internally consistent**. The signal is outside the trio, in the release line's history. In one installation five such trios made a shared resource look locked, and undoing the mistake ate most of a pre-flight — and would have recurred on every following trio.

- ⚠️ **A commit count proves mention, not delivery.** The `work_id` appears in merge, promotion and docs commits. R8 names the candidate; the human confirms by reading the delivered content, and closes the trio — R8 never touches `status:`.
- ⛔ **Do not widen R8 to `task: open`.** Tried and measured: it fired on 23 of 30 open trios, because every live trio's own documents are committed as soon as they are written. Gated on `execution: in_progress` it fired on 5 of 30 — exactly the known cases.
- ⛔ **Do not "fix" it by filtering commit messages** (`docs(…)`, `Merge …`). `--grep` measures mention, not authorship, and a textual filter does not survive real history — the same error that retired the `## Commits` auto-fill (step 7). The discriminator that works is the **status**: `in_progress` declares "started, not finished", which commits on main contradict.

#### R9 — Frontmatter the index does not validate

`/work-index` **warns** but never fails on these (it may run inside other scripts); the gate is here:

```bash
python3 .claude/skills/work-index/generate.py --check --root . 2>&1 >/dev/null | grep '⚠'
```

| Warning | What it is | Severity |
|---|---|---|
| `skipped — name is not YYYY-MM-DD_slug.md` | file **invisible** to the index and to this audit | 🟠 |
| `no frontmatter`, `no status` | status and summary are guessed | 🟠 |
| `status … outside the <type> vocabulary` | typo, or a vocabulary from another type | 🟠 |
| `pending /wiki-sync` | execution `done`, plan still `approved` | 🟡 |
| `updated … is not an ISO date` | the trio never archives | 🟡 |
| `topic outside vocabulary` | label missing from the conventions block | 🟡 |

⛔ **Invisible is not misrepresented.** A wrongly named file is never opened, so validating frontmatter never reaches it — only the skip warning does. One installation had 33 such files, invisible since day one.

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
  - --fix corrects (dates, index only): <list>.
  - Others need a human decision (close trios, etc.).
```

### 7. (Optional `--fix`) Apply deterministic fixes

**Only these corrections are considered safe:**

- **Regenerate the index** (`/work-index`) when step 4 reported drift.
- **Normalize `updated:`** in the frontmatter to `git log -1 --format=%cs <file>`.

**What `--fix` never does:**

- ❌ **Fill `## Commits` from `git log --grep "<work_id>"`.** Removed after measurement: ~12% precision, with one bootstrap commit claimed by four different trios. `--grep` measures mention, not authorship. R4 reports the gap; a human fills it.
- ❌ Hand-edit `_index.md`/`archive/*` (generated — use `/work-index`).
- ❌ Change `status:` in the frontmatter (human close gate) — R8 included.
- ❌ Rewrite `summary:`/`topic:` of a trio (human curation; `--fix` only regenerates the index from them).
- ❌ Edit `related[]` in an execution (depends on wikilinks only the human knows).

After `--fix`, show `git diff --stat` and ask for confirmation. **Does not auto-commit.**

## Anti-patterns

- ❌ *(Monorepo module only)* Running on `demo_*` / `staging_*` (no active work cycle).
- ❌ Treating `--fix` as auto-pilot — always confirm the diff before commit.
- ❌ Applying R3–R8 to a legacy pre-methodology file (no standard name or `status`) — R9 reports it; the human decides.
- ❌ Flagging a drift as 🔴/🟠 without citing the rule (R3-R9) violated.
- ❌ Widening R8 beyond `execution: in_progress`, or filtering commit messages to sharpen it (see R8).
- ❌ Reintroducing a `## Commits` auto-fill by grep (see step 7).

## Cross-references

- `.agents/METHODOLOGY.md` — the task → plan → execution → wiki-sync cycle.
- `.agents/rules/mandatory_planning_rule.md` — plan-before-execution prerequisite.
- `.claude/skills/work-cycle/SKILL.md` — the skill that creates/updates the audited trios.
- `.claude/skills/work-index/SKILL.md` — generates `_index.md`; the deterministic check in step 4.
- `.claude/skills/commit/SKILL.md` — natural "/work-audit && /commit" flow.
