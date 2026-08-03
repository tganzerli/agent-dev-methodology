<!--
  Installs as: {{project}}_wiki/sources/external/_template.md
  Also usable (copy alongside) for {{project}}_wiki/sources/internal/.
  See METHODOLOGY.md §6.1 and conventions.md §4 (`type: source`).

  GOLDEN RULE: summarize, link, never copy raw. This page is a pointer +
  distillation of an external artifact (a spec, a partner handoff, a user
  guide, a design doc) — not a copy of it. Long excerpts belong in the
  original file, not here.

  Authored CONTENT is written in {{KNOWLEDGE_LANG}}. Frontmatter keys/values
  stay English.
-->
---
title: {origin path or name} — {short description}
type: source
scope:
  area: []                      # single-repo: free text
  # apps: []                    # monorepo only
  # packages: []                # monorepo only
status: draft                   # stub | draft | stable | stale
updated: {YYYY-MM-DD}
related: []                     # wikilinks to knowledge pages this source feeds
---

# Summary — `{origin path or name}`

## About this source

Raw artifact: [`{origin path or name}`]({relative/link/or/URL}) — one or two sentences on what it is, who produced it, and in what language/format it originally exists.

## What it covers

- {Topic 1}
- {Topic 2}
- ...

### Not covered

- {Explicitly out of scope, so readers don't assume it}

## Wiki pages it feeds

- **[[{path/to/page}]]** — how this source's content is used there.
- **[[{path/to/other-page}]]** — how this source's content is used there.

## Usage notes

> Caveats, inconsistencies detected, translation notes, or anything a future reader needs before trusting this source at face value.

- ⚠ {caveat, if any}

## History

- {Context on when/why this source was ingested — which task/work_id drove it.}
