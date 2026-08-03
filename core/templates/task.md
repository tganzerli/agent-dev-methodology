<!--
  Installs as: {{project}}_wiki/work/tasks/_template.md
  See INSTALL.md §3. Copy verbatim into a fresh vault (do not de-template
  the `{...}` placeholders below — those are per-task fill-ins, distinct
  from the kit-wide `{{...}}` placeholders resolved at install time).

  Authored CONTENT (the task body) is written in {{KNOWLEDGE_LANG}}.
  This scaffold's prose is in English only as an authoring aid; translate
  the section labels too when instantiating in a non-English project if
  that better serves the team — the frontmatter keys/values stay English.
-->
---
title: {YYYY-MM-DD} — {human task name}
type: task
work_id: {YYYY-MM-DD_slug}
scope:
  area: []                   # single-repo: free text, e.g. [billing, auth]
  # apps: []                 # monorepo only — e.g. [web, mobile]
  # packages: []             # monorepo only — e.g. [core, ui]
status: open                 # open | in_progress | done | cancelled | aborted
updated: {YYYY-MM-DD}
summary: One sentence — what this task asks for. Feeds the generated work catalog.
topic: []                    # controlled vocabulary — see conventions.md §"work frontmatter"
related: []                  # wikilinks. Filled by the human; the LLM may propose additions.
---

# {Task title}

> **Human-authored.** The LLM only edits this task when the human explicitly requests it and approves the proposed change. See METHODOLOGY.md §4.2.
> Keep `status`, `updated`, and `related[]` current as the work progresses.

## Context

> 1–4 paragraphs. What this is, why it is being requested, and any background the LLM needs to understand the ask. Important points to call out here: business rules, product constraints, decisions already made.

## Acceptance criteria

> What needs to be true for this task to be considered done. Use `[ ]` for verifiable items.

- [ ] ...
- [ ] ...

## Declared scope

**Area(s) affected:** `[...]`
<!-- Monorepo only:
**Apps affected:** `[...]`
**Packages affected:** `[...]`
-->

## Related sources

> Optional. Remove this section if there are none.

### External
- Link/path — short description.

### Internal (already in the repo)
- `path/in/repo` — short description.
- Prior tasks/plans in `{{project}}_wiki/work/` that help frame this request.

## Constraints / discipline

> Optional. Hard limits the execution must not cross (e.g. "do not change interface X", "keep backward compatibility with older versions", "no code in this task — documentation only").

- ...

## Stages

> Optional. Use when the task is large or spans more than one action.
> Each stage can have its own plan/execution, sharing the same `work_id` with a suffix, e.g. `{ID}_step1`.
> Additional stages may be proposed by the LLM while executing an earlier stage — always gated on human approval before being written (§4.2). Expect this task to be updated fairly often as the work progresses.

### Stage 1: {stage name} (open)

Short description of this stage's scope.

#### Plan executed
- `—` (fill in once the corresponding plan is approved and executed)

### Stage 2: {stage name} (open)

...

## Success

> Optional. A sentence or short paragraph describing the desired end state — "how we'll know this worked" from the human/product point of view.
