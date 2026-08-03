---
name: wiki-sync
description: Propagate a completed execution log to the wiki's knowledge pages (under {{project}}_wiki/ outside work/ — domains, entities, services, cross-cutting, decisions, etc.). Use when the human invokes /wiki-sync or asks to update the wiki after a finished execution.
argument-hint: "[work_id]"
disable-model-invocation: true
---

# Wiki Sync

Propagates an execution log from `{{project}}_wiki/work/executions/{work_id}.md` to the knowledge pages listed in its "Affected wiki pages" section.

**Mandatory human gate.** Do not run without an explicit invocation from the human (`disable-model-invocation: true` enforces this).

> **Language:** every page created or edited is authored in **{{KNOWLEDGE_LANG}}** (frontmatter keys/tokens stay English).

## Argument

`$ARGUMENTS` = `work_id` (format `YYYY-MM-DD_slug`). If not provided, ask.

## Steps

### 1. Locate and validate the execution log

- Open `{{project}}_wiki/work/executions/$ARGUMENTS.md`.
- Confirm `status: done` in the frontmatter. If it is `in_progress`, stop and ask the human to confirm (a premature sync can propagate incomplete state).
- Confirm the "Affected wiki pages" section exists.

### 2. Iterate over each affected page

For each item in "Affected wiki pages":

- If `(CREATE)`: create the page following `.claude/skills/obsidian-markdown` (frontmatter + structure from `{{project}}_wiki/_meta/conventions.md` §5).
- If `(UPDATE)`: edit surgically. **Do not rewrite the whole page.** Apply `mandatory_planning_rule.md` §3 (surgical edits).
- If `(APPEND)`: append content to the end.

**Important:** every technical claim added needs a `file:line` citation. If the execution log does not carry the reference, infer it from the diff/commit or mark `⚠ unverified` and ask for human verification.

### 3. Update `related[]` in the execution

After syncing, update the execution log's `related[]` frontmatter with wikilinks to every page touched.

### 4. Update indexes

- `{{project}}_wiki/_meta/index.md` — add/update entries for the touched pages.
- `{{project}}_wiki/work/_index.md` — this is **generated**; if the execution changed trio frontmatter, regenerate via `/work-index` rather than editing it by hand.

### 5. Append to the central log

In `{{project}}_wiki/_meta/log.md`:

```markdown
## [YYYY-MM-DD] wiki-sync | {work_id} | N pages touched

- {page1} (CREATE | UPDATE)
- {page2} (CREATE | UPDATE)
- ...
```

### 6. Mark the plan as executed

Update `{{project}}_wiki/work/plans/{work_id}.md` frontmatter to `status: executed`.

### 7. Report to the human

Show a concise summary:
- How many pages created / updated.
- List with wikilinks.
- Flag `⚠ unverified` claims that need human review.

### 8. Promote to the canonical branch — *(monorepo module only)*

If the **monorepo module** is installed and the sync ran on a per-app dev branch, **suggest** promoting the touched knowledge to the canonical branch so it does not fragment across branches:

```
✓ Wiki synced. The touched pages are in the knowledge layer and should
  reach the canonical branch. Next step: /promote-knowledge {work_id}
```

See `.agents/rules/knowledge_source_of_truth_rule.md` (installed by the monorepo module). **Single-repo projects have no second branch — skip this step.**

## Anti-patterns

- ❌ Syncing an `in_progress` execution without confirming.
- ❌ Touching pages not listed in the execution's "Affected wiki pages".
- ❌ Creating pages under `{{project}}_wiki/work/` during the sync (that is managed by the work-cycle, not by wiki-sync).
- ❌ Rewriting existing pages (always edit surgically).
- ❌ Adding a technical claim without a `file:line` citation.
- ❌ Hand-editing `{{project}}_wiki/work/_index.md` (it is generated — use `/work-index`).
