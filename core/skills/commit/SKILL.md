---
name: commit
description: Close a work cycle — sync pending executions to the wiki and generate commits grouped by work_id and by type (docs/feat/fix). Use when the human invokes /commit or asks to "close and commit" the current work.
argument-hint: "[work_id?]"
disable-model-invocation: true
allowed-tools: Bash(git *) Read Edit Write Grep
---

# Commit

Closes one or more finished work cycles: fires `wiki-sync` for pending executions and generates commits grouped by `work_id` and by change type.

**Mandatory human gate.** `disable-model-invocation: true` forces explicit invocation. The `/commit` invocation itself is the gate for the sync phase — within it, the human may still confirm ID-by-ID or release in bulk.

## Pre-flight (optional) — knowledge-layer sync *(monorepo module only)*

Skip this pre-flight in a **single-repo project** — there is no second branch to diverge from.

*(Monorepo module only)* If you are the **first** work of the session on a per-app dev branch (cold session) or other agents/devs may have promoted knowledge to the canonical branch since, **suggest** the human run `/sync-knowledge` before `/commit`. See `.agents/rules/knowledge_source_of_truth_rule.md` (installed by the monorepo module). This sub-routine is non-destructive and does not block `/commit`.

## Argument

`$ARGUMENTS` is optional:

- Empty → scan all pending executions.
- `{work_id}` → operate only on that piece of work.

## Detection convention

The canonical signal of "pending sync" is the artifact state, **not** a new field:

- `executions/{ID}.md` with `status: done` **+** `plans/{ID}.md` with `status: approved` → **pending sync**.
- `plans/{ID}.md` with `status: executed` → sync already done (enters only the commit phase, skips phase 2).
- `executions/{ID}.md` with `status: in_progress` → **ignore** (not part of this flow).

This contract is maintained by step 6 of the `wiki-sync` skill (`.claude/skills/wiki-sync/SKILL.md`), which marks the plan `executed` at the end.

## Phase 1 — Discovery

1. Run `git status --short` (without `-uall`) and `git diff --name-only HEAD` to list uncommitted files (modified + untracked).
2. List `{{project}}_wiki/work/executions/*.md`, filtering those with `status: done`.
3. For each `done` execution, read the matching `plans/{ID}.md` and classify by `plan.status` (rule above).
4. Cross-reference uncommitted files ↔ `work_id` using, in this order:
   - §4.2 of the plan ("Affected files").
   - The execution's "Affected wiki pages" section.
   - Path prefix `{{project}}_wiki/work/{tasks,plans,executions}/{ID}.md`.
5. Uncommitted files that match no `work_id` → **misc** bucket.

**Report to the human** a table:

| work_id | execution status | sync? | uncommitted files |
|---|---|---|---|

Plus the **misc** bucket file list, and the ignored `in_progress` executions (for transparency).

## Phase 2 — Pending sync (gate per ID or in bulk)

For each `work_id` with a pending sync, in chronological `work_id` order:

1. Show a short summary: execution title + "Affected wiki pages" list.
2. Ask:
   - `y` → invoke the `wiki-sync` skill for this ID.
   - `n` → skip this ID (it also skips phase 3).
   - `bulk` / `all` → approve this one and **all remaining pending** in sequence, no further prompt.
3. After each sync, record which wiki pages were touched to include in phase 3 commits (`wiki-sync` lists them in its final report).

Additional filters:

- Do not invoke `wiki-sync` on an `in_progress` execution.
- If a `done` execution has no "Affected wiki pages" section or it is empty, record it and move on — `wiki-sync` covers this case (`plan.status` becomes `executed` even with no pages touched).

## Phase 3 — Commit grouping

Central rule: **one commit per `work_id` per category**. Never mix `docs(wiki):` with `feat:` in the same commit.

### Categories by path

| Path | Commit type |
|---|---|
| Application/library source (your code dirs) | `feat:` / `fix:` / `refactor:` / `perf:` / `test:` per the nature of the plan (§4.3) |
| Knowledge pages under `{{project}}_wiki/` outside `work/` (`_meta/`, `overview.md`, domains/entities/services/cross-cutting/decisions/sources/…) | `docs(wiki):` |
| `{{project}}_wiki/work/tasks/**`, `.../plans/**`, `.../executions/**`, `{{project}}_wiki/work/_index.md` | `docs(work):` |
| `.agents/**`, `.claude/**`, agent entry-points (`CLAUDE.md`, `GEMINI.md`, `AGENTS.md`) | `chore(agents):` (tooling) or `docs(agents):` (rule/methodology) |
| Root config (lockfiles, linter config, etc.) | Alongside the `feat:` that motivated it, or the misc bucket |

### Commit messages

- **Conventional commits**, following the pattern of recent commits (`git log --oneline -20`).
- Line 1 ≤72 chars; language following the dominant pattern of the log.
- Optional body with bullets summarizing the `work_id` and referencing the artifacts:

  ```
  task: {{project}}_wiki/work/tasks/{ID}.md
  plan: {{project}}_wiki/work/plans/{ID}.md
  execution: {{project}}_wiki/work/executions/{ID}.md
  ```

- **No co-authorship footer.** Per `.agents/llm/*`: do not include any `Co-Authored-By: <LLM>` trailer. The author is the human; commits made via an LLM show up only under `git user`.

### Misc bucket

Each file (or small cohesive group) becomes an individual commit with the appropriate type (`chore:`, `fix:`, `docs:`). If a misc file seems to belong to a `work_id` but the mapping did not detect it, **ask** before committing.

## Phase 4 — Execution

1. Present a **final table** of the proposed commits:

   | # | type | message (line 1) | files |
   |---|---|---|---|

2. Ask for approval:
   - `y` → execute all in sequence.
   - `n` → abort (do nothing).
   - `1,3,5` → execute only the listed indices.
3. For each approved commit, in sequence:
   - `git add` **only that commit's files** (never `git add -A` or `git add .`).
   - `git commit -m "$(cat <<'EOF' ... EOF)"` with a HEREDOC to preserve formatting.
   - Report `<short hash> <line 1>`.
4. At the end, run `git status --short` and report the remainder (should be only unapproved misc).

## Phase 5 — Promote to the canonical branch *(monorepo module only)*

Skip entirely in a **single-repo project**. *(Monorepo module only)* If a commit touched the knowledge layer on a per-app dev branch, **suggest** (never auto-run) `/promote-knowledge {work_id}` so the knowledge reaches the canonical branch. See `.agents/rules/knowledge_source_of_truth_rule.md` and the `promote-knowledge` skill (both installed by the monorepo module). `/commit` never executes `/promote-knowledge` itself — promotion requires an explicit human gate.

## Anti-patterns

- ❌ `git add -A` or `git add .` (risk of including `.env`, unwanted lockfiles, unrelated WIP).
- ❌ Mixing `docs(wiki):` with `feat:` in the same commit (loses traceability of code vs. knowledge).
- ❌ Skipping phase 2 — committing while the wiki does not yet reflect the execution publishes outdated knowledge.
- ❌ Running `wiki-sync` on an execution with `status: in_progress`.
- ❌ Committing without showing the final table to the human (phase 4 gate).
- ❌ `--no-verify`, `--amend`, or `git reset` without an explicit request.
- ❌ Automatic `git push`. `/commit` does **not** push — the human decides when.
- ❌ Creating a PR from this flow. A PR is a separate human decision.
- ❌ Adding a `Co-Authored-By: <LLM>` footer — forbidden per `.agents/llm/*`.

## Cross-references

- `.claude/skills/wiki-sync/SKILL.md` — invoked in phase 2.
- `.claude/skills/sync-context/SKILL.md` — broader ingress sub-routine (not called by `/commit`).
- `.agents/rules/mandatory_planning_rule.md` — complementary rule respected throughout the flow.
- *(Monorepo module only)* `.claude/skills/promote-knowledge/SKILL.md`, `.claude/skills/sync-knowledge/SKILL.md`, `.agents/rules/knowledge_source_of_truth_rule.md`.
