---
name: write-article
description: Write a long technical article (Medium, dev.to, company blog, newsletter) about the project — its architecture, performance findings, hard-won lessons. Didactic tone, embedded code, hook → problem → approach → results → lesson. Draws on ingested sources and evidence pages from the vault. Produces files under content/articles/drafts/. Invoke when the human asks for /write-article or an equivalent ("write an article about X", "a long blog post on Y").
disable-model-invocation: true
---

# Write Article

**Manual skill** (writing module). A long technical article (roughly 1500-3000 words), didactic, written for practitioners.

## Prerequisites

- A destination file exists under `content/articles/drafts/` (create it if needed).
- Operate in writing mode: **no** `task → plan → execution` trio (see `content/CLAUDE.md`).

## Flow

1. **Topic and thesis.** The central idea in **one** sentence. Who is the reader (a newcomer to the stack, a veteran engineer, someone curious about the performance angle)? Which venue?
2. **Hook.** The first paragraph earns the rest: a provocative question, a contradiction of the received wisdom, a surprising number, a concrete failure.
3. **Structure.**
   - **Hook + context** (2 ¶) — the problem, and why it matters.
   - **Why it is hard** (1-2 ¶) — the tension; prior approaches and their limits.
   - **The approach** (the body, with code) — what you did, step by step.
   - **Results** (1-2 ¶) — real numbers, from the project's evidence pages.
   - **Trade-offs and limits** (1 ¶) — honesty buys credibility.
   - **The lesson** (1 ¶) — what the reader takes away.
   - **Links** — repo, references, what comes next.
4. **Embedded code.** Complete but minimal excerpts. Never paste whole files; show only what carries the argument. Comments in English.
5. **Charts.** With quantitative data, export the chart from the evidence page into `content/_assets/` and embed it.
6. **Call to action, optional.** An invitation to discuss, the repo, the next piece in a series. Do not force one.

## Style

- **Person** — first person, singular or plural ("we found", "I hit a pattern"). More personal than academic writing.
- **Short paragraphs** (2-4 lines). Reading on a screen is not reading on paper.
- **Generous subheadings.** Readers skim before they commit.
- **Define the jargon at first use.** An article about your stack for someone from another one has to.
- **Short sentences.** Long subordinate chains kill the rhythm.
- **Active voice, present tense.**

## Quality rules

- **Performance results always point at the evidence page** that produced them. No page, no claim.
- **Technical honesty.** State the trade-offs, the limits, and when *not* to use the approach.
- **Reproducibility.** Where possible, link the commit or tag that reproduces the numbers.
- **Attribution.** If the idea came from a paper, post, or RFC, cite and link it.
- **Language** — {{KNOWLEDGE_LANG}} by default; another if the human wants a different reach.

## Anti-patterns

- ❌ Listing seven takeaways instead of going deep on one.
- ❌ Whole files pasted in with no signal about what matters.
- ❌ "The benchmark shows X is 10× faster" with no link to the benchmark or its environment.
- ❌ Closing with "let me know what you think" and no actual point of discussion.
- ❌ Hype with no trade-off.

## Suggested frontmatter

```yaml
---
title: "Article title"
target: medium | dev.to | blog | newsletter
audience: "who this is for"
status: draft | review | published
created: YYYY-MM-DD
updated: YYYY-MM-DD
links:
  published_url: ""        # fill in on publication
  repo_commit: ""          # the commit that reproduces the examples
  related_evidence: []     # wikilinks to the pages behind the numbers
references: []             # wikilinks to ingested sources
---
```

## Output

- `content/articles/drafts/{slug}.md` while in progress.
- Moves to `content/articles/published/` when the human says it went out — filling in `published_url` in the same change, so the draft never becomes the only record of where it landed.
