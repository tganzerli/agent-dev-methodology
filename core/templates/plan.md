<!--
  Installs as: {{project}}_wiki/work/plans/_template.md
  See INSTALL.md §3 and .agents/rules/mandatory_planning_rule.md §3–4.

  Authored CONTENT (all prose in this plan) is written in {{KNOWLEDGE_LANG}}.
  Frontmatter keys/values stay English. The section numbering (§4.0–§4.7)
  mirrors mandatory_planning_rule.md exactly — do not renumber or drop
  sections when instantiating a real plan.

  GATE: this plan does not authorize code execution until status: approved
  is set by a human. See METHODOLOGY.md §4.3.
-->
---
title: {YYYY-MM-DD} — {human plan name}
type: plan
work_id: {YYYY-MM-DD_slug}
scope:
  area: []                   # single-repo: free text, e.g. [billing, auth]
  # apps: []                 # monorepo only
  # packages: []             # monorepo only
status: draft                # draft | approved | executed
updated: {YYYY-MM-DD}
summary: One sentence — what this plan delivers. Feeds the generated work catalog.
topic: []                    # controlled vocabulary — see conventions.md §"work frontmatter"
related:                     # wikilinks to knowledge pages this plan touches
  - work/tasks/{ID}
---

# Plan — {Plan title}

> Covers [[work/tasks/{ID}]]. State any prerequisite tasks/plans read beforehand here.

## §4.0. Pre-plan analyses

> Triage decision: were prior analyses needed to shape this plan (the *what*) or how to conduct it (the *how*)? See METHODOLOGY.md §4.2.5.
>
> - **If analyses ran:** synthesize findings here with `file:line` citations. §4.1–§4.7 below must reflect them. A finding without a verifiable citation is `⚠ unverified`.
> - **If waived:** write `analyses: not needed` plus a one-line justification (small, mechanical, or already well-understood task) and move on to §4.1.

analyses: not needed — {one-line justification}

<!-- OR, when analyses ran:

### Question 1: {question}
{Synthesis, with file:line citations.} 📎 [`path/file.ext:NN`](path/file.ext)

### Question 2: {question}
{Synthesis, with file:line citations.}
-->

## §4.1. Summary and understanding

> A highly cohesive, clear, concise summary of what the task asks for. Demonstrate understanding of the underlying goal, not just the surface-level instructions.

## §4.2. Affected files

> Complete list of every file that will be modified, created, or deleted. Full relative paths from repo root.

- `path/to/file.ext` (CREATE | UPDATE | DELETE) — one-line reason.
- ...

## §4.3. Changes and rationale

> For each affected file (or logical group): exactly what changes, and *why* — the technical reasoning behind the approach. Include concrete code snippets/examples demonstrating the intended change (mandatory per mandatory_planning_rule.md §4.3).

### `path/to/file.ext`

{What changes and why.}

```{language}
// concrete snippet illustrating the change
```

## §4.4. Risks and impact

> Potential side effects on the project: architecture, dependencies, performance, breaking changes. One risk per bullet, with mitigation.

1. **{Risk}.** Mitigation: {...}
2. **{Risk}.** Mitigation: {...}

## §4.5. Execution steps

> Complete, ordered, step-by-step checklist. Each step granular enough to run sequentially without ambiguity. The execution log mirrors this checklist.

- [ ] (1) {Step}
- [ ] (2) {Step}
- [ ] (3) {Step}
- ...

## §4.6. Scope

> Declare explicitly what this plan affects.

**Area(s) affected:** `[...]`  (or: none)

<!-- Monorepo only — declare both, call out coupling if a change crosses boundaries:
**Apps affected:** `[...]`   (or: none)
**Packages affected:** `[...]`   (or: none)
-->

## §4.7. Wiki impact

> Every **knowledge** wiki page (under `{{project}}_wiki/<knowledge dirs>/`, `cross-cutting/`, `decisions/`, `sources/`) that will be **created** or **updated** after execution, with a one-line description of what changes. Full relative paths from repo root.
>
> Do **NOT** list `{{project}}_wiki/work/*` paths here — those are managed by the work cycle itself, not by `/wiki-sync`.
>
> This section is the input for `/wiki-sync` after execution.

- `{{project}}_wiki/{path}` (CREATE | UPDATE) — what changes.
- `{{project}}_wiki/_meta/index.md` (UPDATE) — register the new/changed pages.
- `{{project}}_wiki/_meta/log.md` (APPEND) — entry for this execution.
