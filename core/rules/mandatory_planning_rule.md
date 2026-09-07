---
trigger: always_on
---

# Mandatory Pre-Execution Planning Rule

## 1. Core Directive
**STOP.** Before executing any code modification, file creation, or system command, you MUST generate a comprehensive execution plan. Do not write or alter any project code until this plan has been fully drafted, reviewed, and approved. The plan is the absolute source of truth for your execution.

## 2. Language Requirement
While this rule is written in English, the generated **plan document** MUST be written in **{{KNOWLEDGE_LANG}}** — the knowledge-content language chosen for this project at install time (the same language as the wiki). Code and identifiers remain in English. If `{{KNOWLEDGE_LANG}}` is unset, ask the human before writing the plan.

## 3. Storage and Workflow Rules
- **Location:** the plan lives in `{{project}}_wiki/work/plans/`. Filename follows the work-ID convention: `{{project}}_wiki/work/plans/{YYYY-MM-DD}_{slug}.md`.
- **Trio companion:** every plan has a matching task at `{{project}}_wiki/work/tasks/{ID}.md` (same ID). After execution, an execution log at `{{project}}_wiki/work/executions/{ID}.md` completes the trio.
- **Frontmatter:** the plan starts with YAML frontmatter declaring at least `type: plan`, `work_id`, `scope`, `status` (`draft|approved|executed`), `related[]`.
- **Iterative refinement:** the plan is a living document, refined until there is complete and precise understanding of the task.
- **Punctual edits (strict):** when the human requests adjustments, perform **targeted, punctual edits** to the existing file. Modify ONLY the requested sections. **DO NOT** rewrite the whole file from scratch.
- **Execution gate:** you are strictly forbidden from executing the plan until it completely and accurately covers every requirement of the task, and the human has approved it.

## 4. Plan Structure

### 4.0. Pre-plan analyses
- Before drafting §4.1–§4.7, a **triage** decides whether prior analyses would improve the plan or how to conduct it (see `.agents/METHODOLOGY.md` §4.2.5 and the `work-cycle` skill).
- When analyses ran, this section holds their **synthesis** with `file:line` citations, and §4.1–§4.7 must reflect the findings. When triage waived them, write `analyses: not needed` with a one-line justification.
- This section lives **inside the plan document** (right after the frontmatter, before §4.1) — no separate artifact; the task/plan/execution trio stays intact.

### 4.1. Summary and understanding
A cohesive, concise summary of what the task requested. Prove you understand the underlying goal, not just the surface instructions.

### 4.2. Affected files
A complete list of every file to be modified, created, or deleted. Include full relative paths.
- 🔒 **Rules affected.** State explicitly **which rule describes the behaviour this plan changes** — or `none`, said as such. If the plan alters what an `always_on` rule asserts, **that rule belongs in the file list above**, and updating it is part of this work, not a follow-up.

  *Why this line exists.* In the project this kit came from, a trio changed how a generated index was reconciled. It updated the code, the skill, the ADR and the session memory — and never listed the rule that described the old mechanism. **That rule went on asserting a dead invariant for two months**, while seven later commits touched the same file for other reasons and none revisited the block. Nothing was broken by malice or haste; the plan simply never asked the question. This is that question.

- 🔒 **ADRs affected.** State explicitly **which ADRs govern the area this plan implements**, and for each one whether this work leaves it **confirmed**, **refined** or **superseded** — or `none`, said as such. An ADR that this plan refines or supersedes **belongs in the file list above**, and updating it is part of this work, not a follow-up.

  *Why this line exists.* An ADR is written **before** the code it governs, so it decides principles and defers concrete shape — the signature, the format, the field list. The status that means "decided" (`accepted`) is also the status that means "nothing to look at here", so the implementation that finally holds the evidence has no reason to open it. The deferred half then ages in silence, indistinguishable from a settled one. Origin: an installation wrote nine phase-0 ADRs and its author, reading them, observed they decided less than they appeared to. The observation was right, and the fix was **not** to decide more up front — it was to guarantee the return. The companion half lives in the ADR template: a `revisit_when` field and a **Planned revision** section that states the question, not the answer.

### 4.3. Changes and rationale
- Detail exactly what changes each file gets.
- Give the technical reasoning (*why* it is done this way).
- **Mandatory:** include concrete code snippets/examples of the intended changes.

### 4.4. Risks and impact
List potential side effects: architecture, dependencies, performance, breaking changes.

### 4.5. Execution steps
A complete, ordered, granular checklist executable without ambiguity.

### 4.6. Scope
Declare explicitly what the work affects.
- **Single-repo project:** the modules/areas touched.
- **Monorepo project:** which `apps/*` and which `packages/*` (format: `Apps: [...]` / `Packages: [...]`, or `none`). If a change crosses boundaries, call it out and explain the coupling.

### 4.7. Wiki impact
- List every **knowledge** wiki page (under `{{project}}_wiki/` outside `work/`) to be **created** or **updated** after execution, with full relative paths and a one-line description each.
- **Do NOT** list `{{project}}_wiki/work/*` paths here — those are managed by the work-cycle itself, not by `/wiki-sync`.
- This section is the input for `/wiki-sync` after execution.

## 5. Cross-reference
This rule is part of the broader methodology in `.agents/METHODOLOGY.md`. On conflict between this file and the methodology, **this file prevails for the planning phase**; the methodology prevails for everything else (full cycle, wiki, execution log).
