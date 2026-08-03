<!--
  Installs as: {{project}}_wiki/_meta/_page_template.md
  Generic template for any KNOWLEDGE page (type: entity | service | flow |
  domain | contract | page | adr | discovery). See conventions.md §1, §5.
  For `type: source` use source.md instead; for `type: overview` use
  the seed at core/vault/overview.md.

  Authored CONTENT is written in {{KNOWLEDGE_LANG}}. Frontmatter keys/values
  stay English. Every technical claim needs a `file:line` citation
  (conventions.md §2) — a claim without one must be marked `⚠ unverified`.
-->
---
title: {Human page name}
type: entity                    # entity | service | flow | domain | contract | page | adr | discovery
scope:
  area: []                      # single-repo: free text, e.g. [billing, auth]
  # apps: []                    # monorepo only — e.g. [web, mobile]
  # packages: []                # monorepo only — e.g. [core, ui]
status: stub                    # stub | draft | stable | stale
updated: {YYYY-MM-DD}
sources: []                     # links to sources/ pages backing this content
  # - sources/external/{YYYY-MM-DD}_{slug}.md
code_refs: []                   # repo files this page describes — used by lint to detect `stale`
  # - path/to/file.ext
related: []                     # wikilinks
  # - services/{related-service}
  # - entities/{related-entity}
---

# {Title}

## Summary
1-3 sentences. What it is, which area/app/package, current status.

## Current state
How the code is today. `file:line` citations for every technical claim.

📎 [`path/to/file.ext:NN`](path/to/file.ext)

## Touch points
- Related entities: [[...]]
- Consuming services: [[...]]
- Backend/partner contracts: [[...]]

## Decisions and trade-offs
If any. Point to an ADR in `decisions/` if the reasoning is large enough to deserve its own record.

## Open items and gaps
What is still missing to document/implement/decide. Mark unverified claims with `⚠ unverified` here if they haven't been anchored yet.
