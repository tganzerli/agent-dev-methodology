---
name: sync-knowledge
description: Sync the current branch's (dev_<app>) knowledge layer with main. Applies knowledge-layer updates made on main since the last merge, without touching apps/, packages/, or {{project}}_wiki/work/. Use at the start of a session or when you detect divergence. Human gate before commit. Manual fallback for the CI main→dev broadcast.
argument-hint: ""
disable-model-invocation: true
allowed-tools: Bash(git *), Read
---

# Sync Knowledge

Pulls **knowledge-layer** updates from `main` into the current branch (`dev_<app>`), implementing `.agents/rules/knowledge_source_of_truth_rule.md` §3.3.

> **Monorepo module skill — manual fallback.** In normal operation the CI broadcast (`scripts/broadcast-main.sh`) delivers main → dev automatically; use this skill only when CI failed, the pipeline is down, or you want to pull ahead. In a single-repo project this skill does not apply and must not be installed.

## When to use

- **Start of a session** on `dev_<app>` after days away — refreshes context.
- **When you suspect divergence** (e.g. a just-merged ADR does not show up in your refs).
- **Before starting work** that will touch domain pages — avoids future `/wiki-sync` conflicts.

## When NOT to use

- On `demo_<app>` / `staging_<app>` — outside the automatic flow (rule §4).
- On `main` directly — main does not pull from itself.
- With uncommitted changes — commit or stash first.

## Steps

### 1. Validate context

- `git branch --show-current` → must be `dev_<app>`. If `demo_*`/`staging_*`/`main`, **abort** with a clear message.
- `git status --short` → must be empty. If dirty, instruct `commit`/`stash`.
- `git fetch origin main`.

### 2. Detect divergence

Compare `HEAD` vs `origin/main` for the knowledge-layer paths (adapt to the project's actual filenames):

```bash
git diff --name-only HEAD origin/main -- \
  .agents/ .claude/skills/ <per-agent config> .mcp.json \
  CLAUDE.md GEMINI.md AGENTS.md README.md <workspace file> \
  {{project}}_wiki/_meta/ {{project}}_wiki/apps/ {{project}}_wiki/packages/ \
  {{project}}_wiki/cross-cutting/ {{project}}_wiki/decisions/ {{project}}_wiki/sources/ \
  {{project}}_wiki/overview.md {{project}}_wiki/.obsidian/ \
  scripts/ <CI pipeline config> <root workspace manifest> qa/
```

**Exclude gitignored** explicitly: local agent settings, `.claude/projects/`, `.claude/todos/`, `{{project}}_wiki/.obsidian/workspace*.json`.

**If empty** → report "Knowledge layer is already aligned with main" and stop.

### 3. Present the plan (gate)

List the files with change type (modify/add/delete):

```
I will sync N knowledge-layer files from origin/main:
  - .agents/rules/foo.md (will be modified)
  - {{project}}_wiki/decisions/2026-05-20_bar.md (new)
  - ...
Confirm? (y/n)
```

Without an explicit `y` → abort.

### 4. Check for potential conflicts

If the current branch also has local knowledge-layer changes (committed but not yet promoted to main), warn:

```
⚠ You have N knowledge-layer files modified locally on this branch
  that are NOT in main:
    - <list>
  Applying main will overwrite these local files. Consider running
  /promote-knowledge first to preserve your edits. Continue anyway? (y/n)
```

### 5. Apply main's updates

```bash
git checkout origin/main -- <detected file list>
```

### 6. Verify the staged diff

```bash
git status --short
git diff --cached --stat
```

Present a summary.

### 7. Commit

```bash
git commit -m "sync-knowledge: pull N files from origin/main

Knowledge-layer sync of the current branch with main per
.agents/rules/knowledge_source_of_truth_rule.md §3.3.
"
```

### 8. Push (optional)

Ask: `Knowledge synced. Push to origin/<branch>? (y/n)`. If `y` → `git push origin <branch>`.

## Anti-patterns

- ❌ Running on `demo_*`/`staging_*`/`main` — the skill aborts at step 1.
- ❌ Applying without reviewing the list (skipping step 3) — risk of overwriting local changes.
- ❌ Forcing with a dirty working tree.

## Cross-references

- `.agents/rules/knowledge_source_of_truth_rule.md` — the rule this skill implements.
- `.claude/skills/promote-knowledge/SKILL.md` — counterpart (pushes to main).
- `scripts/broadcast-main.sh` — the automatic CI counterpart this skill backs up.
