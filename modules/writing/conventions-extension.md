# Conventions extension — writing module

> **Installer:** append the section below (everything between the two `⟪…⟫` markers) into
> `{{project}}_wiki/_meta/conventions.md`, as a new top-level section after §4 "Page types".
> Do **not** create a separate file in the target project — these belong in the one canonical
> conventions doc so every agent finds them there. Remove the `⟪…⟫` markers when pasting.
>
> This extension is only installed when the **writing module** is active (INSTALL.md §5-sexies).
> It adds the `⚠ source needed` seal and the `content/` frontmatter fields.

---

⟪ BEGIN drop-in section — paste into {{project}}_wiki/_meta/conventions.md ⟫

## Prose deliverables (writing module)

A project that installs the writing module produces **prose written for people outside the repo** — a thesis, a paper, an article, a post. That prose lives under `content/`, **outside the vault**, governed by the directory-scoped override in `content/CLAUDE.md` (METHODOLOGY §4.6). It is not cataloged in `_meta/index.md`: it is a deliverable, not knowledge.

The vault relationship runs **one way**. Prose *reads* from `sources/`, `benchmarks/`, `decisions/`, and `work/executions/`; it never writes back. A gap discovered while drafting is **signaled** to the human and fixed through the normal cycle or `/ingest-source`.

### The `⚠ source needed` seal

A third axis of uncertainty, alongside the two the vault already uses:

| Marker | Means | Cleared by |
|---|---|---|
| `⚠ unverified` (base) | **No citation yet** — a technical claim with no `file:line` anchor. | Adding the `file:line` citation. |
| `⚠ unverified <metric>` (benchmarks module) | **A number with no reproducible page.** | Publishing the evidence page and citing it. |
| `⚠ source needed` (writing module) | **A bibliographic assertion with no real source behind it** — an author-year citation that resolves to nothing under `sources/`, and was not supplied by the human. | Ingesting the real source, or removing the assertion. |

Written as `⚠ source needed: <the assertion>`, in place, so the polish pass finds it.

**Why prose needs its own seal.** The other two axes catch claims about *this repo*, which a reader can check. A fabricated reference is different: it is the failure mode an LLM produces most readily and a reader detects least easily, and by the time the text reaches an examiner or a reviewer, nobody in the loop can `grep` for it. The rule is absolute — **never invent an author, a year, or a title** — and the seal is what makes complying with it visible instead of silent.

**No prose is delivered with an open seal.** Polish resolves every `⚠ source needed` and every `⚠ unverified <metric>`, or the claim comes out.

### `_norms/` vs `sources/`

Two document piles that look alike and behave differently:

| | `content/_norms/` | `{{project}}_wiki/sources/` |
|---|---|---|
| **What it is** | Style manuals, institutional templates, venue author guides. | Papers, RFCs, technical docs, internal records. |
| **What it governs** | **How** to write — the form. | **What** the text asserts — the content. |
| **Cited in the bibliography** | No. | Yes. |
| **How it enters** | Drop the file in. | `/ingest-source <path-or-url>`. |

The test: form or content? Form → `_norms/`. Content → a source.

### `content/` frontmatter

Prose files are **not** vault pages and do not carry `type`/`scope`/`related`. Articles and posts carry a minimal publication frontmatter instead:

```yaml
---
title: "..."
target: medium | dev.to | blog | newsletter     # articles
platform: linkedin | x | threads | mastodon     # posts
language: <target language>
status: draft | review | published
created: YYYY-MM-DD
updated: YYYY-MM-DD
links:
  published_url: ""          # filled in at publication, in the same change as the move
  repo_commit: ""            # the commit that reproduces the examples
  related_evidence: []       # wikilinks to the pages behind any numbers
references: []               # wikilinks to ingested sources
---
```

Academic files may omit frontmatter entirely — their destination is usually a word processor or PDF, and frontmatter does not survive the trip.

`status` moves `draft → review → published`. **Publication is one change**: the file moves from `drafts/` to `published/` and `published_url` is filled in together, so a published piece never leaves its only record in a draft.

⟪ END drop-in section ⟫
