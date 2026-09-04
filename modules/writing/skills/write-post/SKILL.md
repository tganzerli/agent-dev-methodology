---
name: write-post
description: Write a short post for a social or micro-blog platform (LinkedIn, X, Threads, Mastodon, short blog). One central idea, strong hook, optional call to action, length per platform. May be a snippet drawn from a long article or a standalone idea. Produces files under content/posts/drafts/. Invoke when the human asks for /write-post or an equivalent ("a post about X", "something for LinkedIn", "a short one on Y").
disable-model-invocation: true
---

# Write Post

**Manual skill** (writing module). A short post. One idea. High density.

## Prerequisites

- Know the **platform** — it determines length, tone, and formatting.
- A destination file exists under `content/posts/drafts/` (create it if needed).

## Flow

1. **Platform and limit.**
   - **LinkedIn** — ~1300 characters before the "see more" fold; 3000 maximum. Generous line breaks.
   - **X** — 280 characters per post; beyond that, a numbered thread.
   - **Threads** — ~500 characters.
   - **Mastodon** — 500 by default, varies by instance.
   - **Short blog** — 300-600 words, with a title.
   - Verify the current limit if it matters; platform limits change.
2. **One idea.** Resist listing five takeaways. Take one and go at it. The others are other posts.
3. **Hook.** The first line has to stop the scroll: a provocative question, a contradiction of the received wisdom, a concrete surprising number, a one-sentence story that opens a loop.
4. **Lean body.** Every sentence earns its place. If removing it leaves the post intact, remove it.
5. **Call to action, optional.** A question for the comments, a link to the long piece, a link to the repo. Do not force one.

## Style by platform

- **LinkedIn** — generous line breaks (one sentence per line, paragraphs of one to three). Professional but with a voice; it is a conversation, not a résumé. Two to four relevant hashtags at the end. Close with a question or a link.
- **X** — a single sentence, or a numbered thread. Zero to two hashtags. Extreme brevity; every character counts.
- **Threads** — more casual than LinkedIn. No hashtags — that is the platform's culture.
- **Short blog** — title plus body, optional subheadings, a one-to-two-minute read.

## Rules

- **No emoji** unless the human asks.
- **No motivational cliché.** "Hard work pays off" says nothing.
- **Honesty.** If the post cites a result, link its source — the commit, the evidence page, the repo.
- **Active voice, present tense, first person.**
- **Language** — the target platform's audience decides, not the repo's default.

## Anti-patterns

- ❌ "7 things I learned doing X that will change your life."
- ❌ Hashtag spam.
- ❌ Decorative emoji on every bullet.
- ❌ "Agree? Comment below!" with no real point of discussion offered.
- ❌ Recycling a whole paragraph from the long article without rewriting it for the short form.

## Suggested frontmatter

```yaml
---
title: "Hook / working title"
platform: linkedin | x | threads | mastodon | short-blog
language: <target language>
status: draft | review | published
created: YYYY-MM-DD
updated: YYYY-MM-DD
char_count: 0
links:
  published_url: ""        # fill in on publication
  related_article: ""      # if this is a snippet of a long piece
  related_evidence: ""     # if it cites a measured result
---
```

## Output

- `content/posts/drafts/{YYYY-MM-DD}_{platform}_{slug}.md` while in progress.
- Moves to `content/posts/published/` when the human says it went out, with `published_url` filled in.

## Pattern: a snippet of a long article

The common case — an article was published and needs a post to carry people to it.

1. Read the article.
2. Extract the strongest hook: one sentence, one number, one contradiction.
3. **Rewrite** it for the platform's form. Do not copy.
4. Close with the link.

It is bait for the article, not a summary of it.
