---
name: ingest-source
description: Ingest an external source (article, backend spec, meeting transcript, PDF, web link) into the wiki. Creates a summary under {{project}}_wiki/sources/external/ and updates the affected knowledge pages. Use when the human asks to add/ingest a document or link into the wiki.
argument-hint: "[path-or-url]"
disable-model-invocation: true
---

# Ingest Source

External source ingest per `.agents/METHODOLOGY.md` §6.1.

> **Language:** the summary and any page edits are authored in **{{KNOWLEDGE_LANG}}**, even when the source is in another language.

## Argument

`$ARGUMENTS` = local file path or URL. If not provided, ask.

## Steps

### 1. Collect the source

- **Local file:** read it directly.
- **URL:** use the `defuddle` skill (vendored) to extract clean markdown and save tokens.

### 2. Discuss takeaways with the human

Summarize in 3-5 bullets what the source covers. **Ask for confirmation** before proceeding — the human steers emphasis ("focus on section X").

### 3. Create a summary under `{{project}}_wiki/sources/external/`

Filename: `YYYY-MM-DD_short-slug.md`. Use the installed `{{project}}_wiki/sources/external/_template.md`.

Structure:

```markdown
---
title: {Original source title}
type: source
scope:
  area: []          # single-repo: modules/areas the source informs
  # apps: []        # monorepo module only
  # packages: []    # monorepo module only
status: stable
updated: {YYYY-MM-DD}
sources: []
code_refs: []
related: []
---

# Summary — {Title}

## About this source

- **Origin:** {author / team / publication}
- **Location:** {original path or URL}
- **Date:** {date stated in the source}
- **Type:** {spec | ADR | article | transcript | RFC | etc.}

## What this source covers

{Table or list by section, with usefulness to the project. DO NOT copy raw content.}

## Wiki pages this source feeds

{List, updated as new pages reference it}

## Usage notes

- When to re-read. When to ignore. When to expect a revision.
```

**Golden rule:** the summary points, it does not copy. The Obsidian vault must link to the source, not duplicate it.

### 4. Identify affected pages

From the source content, list existing knowledge pages under `{{project}}_wiki/` (domains, entities, services, cross-cutting, decisions, …) that **should** reference this source.

If the source introduces a concept with no page of its own, propose creating one. Do not create it immediately — list it as a suggestion.

### 5. Update existing pages (human gate)

For each affected existing page, show what will be updated and **ask for approval** before touching it.

Typically:
- Add the source to the frontmatter `sources[]`.
- Update `updated: YYYY-MM-DD`.
- Add a paragraph/section citing the source (`§X.Y` of the summarized source).

### 6. Update `{{project}}_wiki/_meta/index.md`

Register the new source under "Sources → External".

### 7. Append to the log

```markdown
## [YYYY-MM-DD] ingest | {name-of-summary-created}

- Source: {origin}
- Existing pages updated: N
- New pages suggested (not created): N
```

## Points of attention

- **Long documents (>50KB):** consider reading in chunks or jumping straight to the summary, depending on the agent's context budget.
- **`file:line` citations:** if the source cites code from *another* system (e.g. a partner backend cites its own files, not ours), **do not** confuse it with our `code_refs` — only code from this repo enters `code_refs`.

## Anti-patterns

- ❌ Copying raw content from the source into the summary.
- ❌ Creating new domain/entity pages without human approval.
- ❌ Editing affected pages without showing the diff first.
- ❌ Forgetting to update `{{project}}_wiki/_meta/index.md`.
