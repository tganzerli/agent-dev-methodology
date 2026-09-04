# Writing module — long-form prose as a first-class deliverable

Install when the project's output includes **prose written for people outside the repo** — a thesis or dissertation, a paper, a technical article, a talk, release-facing posts — and that prose is derived from what the project's work and knowledge layers already proved.

| Piece | Installs to | What it does |
|---|---|---|
| `templates/content-entrypoint.md` | `content/CLAUDE.md` (and/or `content/AGENTS.md`) | The **directory-scoped override** (METHODOLOGY §4.6) that swaps the trio cycle for a writing cycle inside `content/`, and states which safeguards survive the swap. |
| `skills/write-academic/` | `.claude/skills/write-academic/` | Human-gated skill for formal academic text under a declared style authority. |
| `skills/write-article/` | `.claude/skills/write-article/` | Human-gated skill for a long technical article. |
| `skills/write-post/` | `.claude/skills/write-post/` | Human-gated skill for a short platform post. |
| `conventions-extension.md` | appended into `{{project}}_wiki/_meta/conventions.md` | The `⚠ source needed` seal and the `content/` frontmatter fields. |

## Why prose needs a module and not just a folder

Three failure modes, none of which a folder fixes.

**1. The cycle does not fit.** `task → plan → execution` is calibrated for changes to product code: a discrete unit, a branch, a reviewable diff, a gate. A chapter is none of those. Forced through the trio, writing produces ceremony with no protective value — a plan nobody reads, a branch per paragraph — and the predictable response is that the author stops using the methodology inside `content/` at all, silently. The override makes the lighter cycle **explicit and local** instead of de facto and undocumented.

**2. The safeguards still apply, and they are the ones that matter most.** Prose is where an unanchored claim does its real damage: it leaves the repo. A number in a chapter is read by an examiner, a reviewer, a conference audience — people with no `grep` access and no way to check. So the citation discipline, the empirical-claim discipline, and the language rules survive the override intact, and the module adds the seal prose needs and code does not: **`⚠ source needed`**, for a bibliographic assertion with no real source behind it.

**3. Fabricated citations are the failure mode of this material.** Not a hypothetical risk: an LLM asked for an author-year reference will produce a plausible one. `⚠ source needed` exists to make that impossible to do quietly — every citation resolves to an ingested source page or to something the human supplied in the conversation, and anything else is marked and surfaced rather than written.

## The writing cycle

**outline → draft → review → polish → deliver**

- **Outline** — one or two lines per paragraph: which idea it defends, which source anchors it. Approved by the human before any prose is written. This is the analogue of the plan gate, and it is the only gate in the cycle that is worth its cost.
- **Draft** — write the whole piece against the approved outline.
- **Review** — iterate with the human. Feedback about a paragraph changes that paragraph; rewriting the whole piece in response to local feedback is the anti-pattern, and it is the one that gets a text worse over time by discarding revisions the human already made.
- **Polish** — resolve every `⚠ source needed` / `⚠ unverified <metric>`, check citation format, strip repo-only markup that will not survive the destination format (wikilinks, callouts).
- **Deliver** — move from `drafts/` to `published/`, record where it went.

## What survives the override

Named explicitly in the entry-point template, because an override that does not say what it keeps is read as an override of everything:

- The **knowledge language** for the content that has one.
- **`file:line` citations** whenever the text refers to the project's own code.
- **No quantitative claim without its evidence page** (benchmarks module) — in prose the seal is `⚠ unverified <metric>`, exactly as in the wiki.
- **No bibliographic claim without a real source** — `⚠ source needed`.
- **Writing does not write to the wiki.** If drafting reveals a gap in the knowledge layer, the agent **signals it** and the human decides; the fix goes through the normal cycle or `/ingest-source`. Prose is downstream of knowledge, never a side door into it.

## `_norms/` vs `sources/` — the distinction that keeps recurring

Two piles of documents that look alike and behave nothing alike:

- **`content/_norms/`** — documents that govern **how to write**: a style manual, an institution's template, a journal's author guide, a venue's submission rules. They are **not cited** in the bibliography. Drop the file in; no ingest needed.
- **`{{project}}_wiki/sources/`** — documents that **support what the text asserts**. They **are cited**. They enter through `/ingest-source`.

The test: does it govern the **form** or support the **content**? Form → `_norms/`. Content → a source.

## Institutional norms and author overrides

Academic and professional writing frequently arrives with an **institutional rulebook** — what an AI may and may not do, what must be declared, who may be credited. That rulebook and the author's own instructions **will** conflict, and the module takes a position:

**The author's instruction prevails, and the override is written down with its safeguard.** `write-academic` carries a table with one row per overridden rule: what the institution says, what the author decided instead, and **the safeguard that keeps the override honest**. Not as a footnote — as a rule the skill executes.

The reason for the table rather than case-by-case judgement: an agent that silently follows the institution surprises the author, and an agent that silently follows the author strips a safeguard nobody agreed to drop. The table makes both visible, and it is auditable months later, when the conversation that produced the decision is gone.

Two rules never move, whatever the author says: **the AI is not an author or co-author**, and **it does not invent a reference**.

## Install

See `INSTALL.md` §5-sexies. In short: copy the three skills, install the entry-point template into `content/`, append the conventions extension, create the `content/` tree, and register the skills as **manual-only** in the skills index.

## Honesty about maturity

The **override shape** and the **`_norms`/`sources` split** were run for months in the project this kit came from, on a thesis written against an institutional manual, and both were revised in use — this is the mature form, not the first one. The **institutional-override table** likewise came from a real conflict with a real rulebook.

What is a **generalization**: everything that de-specifies them. The original skills named one citation standard, one language, one institution's manual, and one project's domain. Stripping those left a shape that should hold for other venues and standards, but has not yet been exercised against a second one. Expect the `write-academic` skill in particular to need a project-local pass: its style section is a scaffold to replace with the actual style authority, not a rulebook to obey as shipped.
