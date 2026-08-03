---
name: work-cycle
description: Drive the task → plan → execution → wiki-sync cycle in this repository. Use when the human asks to start new work, create a task, generate a plan, execute an approved plan, or record an execution. Includes pre-plan analysis triage (parallel agents) and a contextual per-role model recommendation. Applies the methodology in .agents/METHODOLOGY.md.
---

# Work Cycle

Encapsulates the 5-step work cycle described in `.agents/METHODOLOGY.md` §4. **Read that file if it is not already in context.**

## Principle

Every piece of work in this repo produces a trio bound by **work_id** (`YYYY-MM-DD_slug`):

- `{{project}}_wiki/work/tasks/{ID}.md` — human request
- `{{project}}_wiki/work/plans/{ID}.md` — generated plan (human gate)
- `{{project}}_wiki/work/executions/{ID}.md` — live log (kept during execution)

> **Language:** the trio content (task/plan/execution) and any wiki page are authored in **{{KNOWLEDGE_LANG}}**. Code and identifiers stay English. If `{{KNOWLEDGE_LANG}}` is unset, ask the human before writing content.

## When to apply

- Human describes a new problem/feature → create a **task** (if none exists) and **recommend a model per role** (§1).
- Before the plan → run the **pre-plan analysis triage** (§1.5); if warranted, dispatch agents in parallel and synthesize.
- Human asks for a plan → follow `.agents/rules/mandatory_planning_rule.md` and generate a **plan** (with the `Pre-plan analyses` section).
- Human approves the plan → start the **execution log** and execute.
- Human asks to close → mark the execution `done` and offer to run `/wiki-sync`.

## Step-by-step flow

### 0. Context pre-flight (optional)

If the session is cold (you did not resume recent work) or other agents/machines may have updated the repo, **suggest** `/sync-context` before starting — it makes sure the LLM reads the latest state of code and wiki. Do not fire the skill automatically; only propose it when the context matches. See `.claude/skills/sync-context/SKILL.md`.

### 1. Task

If there is no task yet, ask the human. If the human described the problem in the conversation, offer to materialize it as a task before proceeding.

Minimal template for `{{project}}_wiki/work/tasks/{ID}.md` (use the installed `{{project}}_wiki/work/tasks/_template.md`):

```markdown
---
title: {Human slug}
type: task
work_id: {YYYY-MM-DD_slug}
scope:
  area: []          # single-repo: modules/areas touched
  # apps: []        # monorepo module only
  # packages: []    # monorepo module only
status: open
updated: {YYYY-MM-DD}
summary: One sentence — what the work delivers.
topic: []
related: []
---

# {Title}

## Context

{What the human wants and why}

## Acceptance criteria

- [ ] {Criterion 1}
- [ ] {Criterion 2}

## Related sources

- {Links to external sources, contracts, etc.}
```

#### Model recommendation (contextual, per role)

When materializing/starting the work, **recommend to the human which model to use** at each of the three decision points — always **contextually**, never from a fixed role→model table:

1. **Create/refine the task** — structured drafting of the request.
2. **Run each pre-plan analysis** (§1.5) — may vary per analysis.
3. **Write the plan** (§2) — reasoning depth and coverage.

**Principle:** the best choice depends on the *specific content* of this work, not the role in the abstract. The same role ("write the plan") may call for different models in different jobs — a deep architectural plan is better served by a strong reasoning model; a mechanical plan by a fast/cheap one.

**Dimensions to weigh** at each point: reasoning depth required, context breadth/size, nature (mechanical vs. exploratory vs. creative), cost/latency sensitivity, and the risk of the change.

**Do not pre-catalog.** The model line-up changes often — new versions ship almost weekly, with different characteristics (a newer generation may supersede the current one). Therefore:

- Map the dimensions above to the **models actually available right now** in the environment, preferring the most capable/recent one suited to each point.
- Treat any model list in `.agents/llm/*` as a **hint that may be outdated** — confirm it against what is actually available and adjust.
- Different analyses of the same triage may call for different models (broad file sweep → fast model; architectural trade-off analysis → deep reasoning model).

**Output:** present the human a short recommendation with **one justification line per point** before proceeding. It is **advisory** — the human may override. Reaffirm the analysis model in §1.5 and the plan model in §2, once more is known about the work.

### 1.5. Triage and pre-plan analyses

Before writing the plan, run a **triage session**: decide whether **prior analyses** would materially improve the plan (the *what*) or how to conduct it (the *how*).

**When analyses are worthwhile** (at least one trigger):

- Current behavior/architecture of the code is uncertain and changes the shape of the plan.
- More than one viable approach exists and the choice depends on investigation.
- Cross-boundary or external-contract impact (in a monorepo, cross-package/cross-app).
- Risky/irreversible change, or an area unknown to the agent.

**When to skip** — record `analyses: not needed` + one justification line and go straight to §2:

- Small, mechanical, or already well-understood task.

**If analyses are needed:**

1. **Decompose into discrete, independent analysis questions** — each self-contained and answerable in isolation. Independence is what enables parallelism; only chain (sequential) when one analysis genuinely depends on another's result.
2. **Dispatch in parallel** — one question per agent, **all `Agent` calls in the same response** (see `.agents/llm/*`). Use a read-only search agent for sweeps and a deeper agent for trade-off analysis. Choose each agent's model per the contextual recommendation above.
3. **Each agent returns findings with `file:line` citations.**
4. **Synthesize on the main thread and validate the citations** — sub-agents do not share your context. A finding without a verifiable citation → `⚠ unverified`.

**Only after analyses close** → write the plan (§2). The synthesis enters the plan as a dedicated **`Pre-plan analyses`** section, right after the frontmatter and before §4.1 (see §2). The human gate remains the plan approval — triage/analysis does **not** waive or pre-empt that gate.

### 2. Plan

Always follow `.agents/rules/mandatory_planning_rule.md` (§4.1 through §4.7), written in **{{KNOWLEDGE_LANG}}**.

The plan must open with a **`Pre-plan analyses`** section (right after the frontmatter, before §4.1 Summary and understanding) containing the synthesis of §1.5 with its `file:line` citations — or the note `analyses: not needed` when triage waived them. §4.1 through §4.7 must reflect what the analyses found. Reaffirm here the model recommended to write the plan.

**Gate:** do not execute any code before the human explicitly approves.

Add frontmatter to the plan:

```yaml
---
title: {Human slug}
type: plan
work_id: {YYYY-MM-DD_slug}
scope: { area: [] }   # or apps/packages in a monorepo
status: draft         # draft → approved → executed
updated: {YYYY-MM-DD}
related: []           # wikilinks to the knowledge pages the plan touches
---
```

### 2.5. Create branch (after plan approved, before executing) — *(monorepo/git-branching module only)*

**Single-repo projects create no per-work branch** — skip this step and go straight to §3. It applies only when the **monorepo/git-branching module is installed** (per-app long-lived branches + ephemeral work branches).

With `plans/{ID}.md` at `status: approved`, create the physical branch **before** starting the execution. Canonical rule: `.agents/rules/git_branching_rule.md` (installed by the monorepo module).

**Mandatory validations before `git checkout -b`:**

1. `{{project}}_wiki/work/plans/{work_id}.md` exists.
2. The plan frontmatter has `status: approved`.
3. The name follows the module's `<type>/<work_id>__<scope>` convention (a single app or a single package as scope — never two).

See `.agents/rules/git_branching_rule.md` for the exact branch types and canonical commands; do not hardcode them here.

**Anti-patterns:**

- ❌ Creating a branch before the plan is `approved` (violates the gate).
- ❌ Committing directly on a permanent branch.
- ❌ Double scope in one branch — split the work instead.

### 3. Execution

When you start executing, create `{{project}}_wiki/work/executions/{ID}.md` from the template in `{{project}}_wiki/work/executions/_template.md`. Keep it **live**: update after each completed step, record divergences from the plan with justification.

Status: `in_progress` → `done` or `aborted`.

### 4. Human review

When the execution closes, flag it and wait for review before touching the wiki.

### 5. Wiki sync

After human approval, invoke `/wiki-sync {ID}` — propagates the changes to the knowledge pages (`{{project}}_wiki/<knowledge dirs>/`, `cross-cutting/`, etc.). See the `wiki-sync` skill.

### 6. Promote knowledge — *(monorepo module only)*

If the **monorepo module** is installed and the current branch is a per-app dev branch, invoke `/promote-knowledge {ID}` after `/wiki-sync` to bring the touched knowledge layer to the canonical branch. See `.agents/rules/knowledge_source_of_truth_rule.md` and the `promote-knowledge` skill (both installed by the monorepo module). **Single-repo projects have no second branch to promote to — skip.**

## Anti-patterns

- ❌ Skipping the plan-approval gate.
- ❌ Writing directly into knowledge pages without going through `/wiki-sync`.
- ❌ Adding `{{project}}_wiki/work/` pages to `{{project}}_wiki/_meta/index.md` (use `{{project}}_wiki/work/_index.md`).
- ❌ Rewriting the whole plan when the human asks for a punctual adjustment (use surgical edits — `mandatory_planning_rule.md` §3).
- ❌ Mixing two pieces of work in one ID. One piece of work = one ID = one trio.
- ❌ Writing the plan before the pre-plan analyses (§1.5) close.
- ❌ Dispatching analyses for a trivial/mechanical task (overhead with no return), or creating analysis questions that depend on each other (kills the parallelism).
- ❌ Treating triage/analysis as if it replaced the plan-approval gate — the human gate stays at §2.
- ❌ Applying a fixed role→model table. Model choice is contextual and re-evaluated each job.
- ❌ Blindly trusting the model list in `.agents/llm/*` without checking what is available now.

## work_id naming

Format: `YYYY-MM-DD_short-slug-in-kebab-case`.

- Date = the task's creation date.
- Slug = 2-5 words, no stopwords (e.g. `diary-schedule-service`, not `the-new-diary-service`).
- Lowercase, hyphens. No underscore, space, or accents.
