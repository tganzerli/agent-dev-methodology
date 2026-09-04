# {{PROJECT}} — content area (writing mode)

> **Directory-scoped override.** This file is local to `content/` and replaces the project's development cycle **while you are working inside this directory** (METHODOLOGY §4.6). Everywhere else in the repo, the full cycle in `.agents/METHODOLOGY.md` applies unchanged.

## Writing mode ≠ development mode

`task → plan → execution → wiki-sync` governs changes to **product code**. A chapter is not a diff: it has no branch worth cutting, no reviewable unit smaller than a section, and no gate that pays for itself except the outline. Inside `content/` the cycle is:

**outline → draft → review → polish → deliver**

**Suspended here:**

- No trio (`work/tasks|plans|executions/`) for a piece of writing.
- No ephemeral branch per piece. Work on the project's integration branch, or on a single `docs/*` branch if you want the text isolated.
- No "approved plan" before drafting a paragraph. The **outline** is the gate, and it is approved by the human before prose is written.

**Still in force, without exception:**

- **Knowledge language** — {{KNOWLEDGE_LANG}} for the content that has one; code, identifiers, and inline comments in English.
- **`file:line` citations** whenever the text refers to this project's code. Open the file and check the line before citing it; line numbers move.
- **No quantitative claim without its evidence page.** If the text says "X is faster / cheaper / more accurate than Y", it points at the page that measured it. Otherwise mark `⚠ unverified <metric>` and raise it.
- **No bibliographic claim without a real source.** Every author-year citation resolves to a page under `{{project}}_wiki/sources/` or to something the human supplied in this conversation. Anything else is marked `⚠ source needed` and surfaced. **Never** invent an author, a year, or a title.
- **Human gates.** Outline approval and delivery are the human's, as everywhere else.

## Directory layout

```
content/
  CLAUDE.md          ← this file
  _index.md          ← catalog of everything in content/
  academic/          ← thesis, papers, submissions
  articles/
    drafts/          ← in production
    published/       ← final published version (with its URL)
  posts/
    drafts/
    published/
  _norms/            ← style manuals, institutional templates — they govern HOW to write
  _drafts/           ← abandoned drafts (archived, not deleted)
  _assets/           ← images, charts exported from evidence pages
```

## Skills

| Skill | For |
|---|---|
| `/write-academic` | Formal academic text under a declared style authority. Reads `_norms/`. |
| `/write-article` | Long technical article (1500-3000 words), didactic, code embedded. |
| `/write-post` | Short platform post. One idea, strong hook. |
| `/ingest-source` | (core) Bring an external source into `{{project}}_wiki/sources/external/`. Use when the document is **citable**. |

## Where the inputs come from

The text produced here is the **final product**. Its inputs live elsewhere in the repo:

| What you need | Where it is |
|---|---|
| Citable sources (papers, RFCs, external technical docs) | `{{project}}_wiki/sources/external/` |
| Internal documents (research proposal, meeting notes) | `{{project}}_wiki/sources/internal/` |
| Quantitative results | `{{project}}_wiki/benchmarks/` *(benchmarks module)* |
| Architectural decisions | `{{project}}_wiki/decisions/` |
| Development process log | `{{project}}_wiki/work/executions/` |
| Consolidated knowledge | the vault's knowledge directories |
| Formatting rules | `content/_norms/` |

## `_norms/` vs `sources/`

- **`content/_norms/`** — manuals and templates that say **how to write**: style manual, institutional template, journal author guide. **Not cited** in the bibliography. Put the file here directly.
- **`{{project}}_wiki/sources/external/`** — sources that support technical assertions in the text. **Cited** in the bibliography. Ingested via `/ingest-source <path-or-url>`.

When in doubt: does it govern the **form** or support the **content**? Form → `_norms/`. Content → `/ingest-source`.

## Link back to the wiki

If, while writing, you find something that deserves to become permanent project knowledge (an undocumented decision, an insight from an external source, a gap in the vault):

1. **Do not write it into the wiki from here.** Writing mode does not touch the knowledge directories.
2. **Signal it to the human:** "this deserves a page at `{{project}}_wiki/X/Y.md`", or "this source should be ingested".
3. If they agree: a new external source → `/ingest-source <url>`; knowledge derived from work already done → the normal `task → plan → execution → wiki-sync` cycle.

Prose is **downstream** of knowledge. It is never a side door into it.

## File conventions

- File names in `kebab-case.md` (or `snake_case.md`) — consistent within each subdirectory.
- Minimal frontmatter for articles and posts: `title`, `target` (venue/platform), `status: draft | review | published`, `created`, `updated`, `links`.
- For academic text, frontmatter is optional — the destination is often a word processor or PDF, and frontmatter does not travel.
