---
trigger: always_on
---

# Git Branching Rule (core, single-repo)

> The **default** branching rule, installed for a single-repo project (one app / one package, one line of history). If the project is a **monorepo with multiple apps and/or shared packages**, install `modules/monorepo/rules/git_branching_rule.md` instead — the two are **mutually exclusive** and install to the same path (§10).

## 1. Core directive

**STOP.** Before creating any branch, opening a Pull Request, or running `git push` in this repository, you MUST validate that the operation respects this rule. It is **non-negotiable** for any LLM agent operating in the repo and is the Git-layer counterpart of `mandatory_planning_rule.md`. **Do not invent branch names. Do not create a branch before the approval gate. Do not commit directly to a permanent branch.**

## 2. Language requirement

New documents generated under this rule (ADRs, wiki pages) are authored in **{{KNOWLEDGE_LANG}}** (the project's knowledge-content language). Branch names, Git commands, commit messages, and Git identifiers stay in **English** and pure ASCII — only `[a-z0-9-_]` and `/`, no accents, spaces, or special characters.

## 3. Permanent branches

There are **two** permanent branches. Both live forever on the remote; neither is deleted.

| Branch | Role | Receives from | Direct commit |
|---|---|---|---|
| `main` | Release line. The stable products live here; SemVer tags are cut from it. | PRs from `dev` only. | **FORBIDDEN** — no exception. |
| `dev` | Continuous integration. Where ephemeral branches land. | Merges of ephemeral branches (`<type>/<work_id>__<scope>`). | Forbidden except a `chore` approved in a plan. |

### 3.1. Promotion flow

```
<type>/<work_id>__<scope>  →  dev  →  main
                                        ↑
                                   SemVer tag (vX.Y.Z)
```

`experiment/<slug>` (§3.2) lives **outside** this flow and never merges.

### 3.2. Experimental branches

`experiment/<slug>` — throwaway PoCs and spikes, **outside the formal cycle** (no mandatory task/plan/execution trio). Used to explore an idea before it becomes real work.

- Short-lived. Deleted once the idea is absorbed (turned into a formal task) or abandoned.
- **NEVER** merged into `dev` or `main` — they are disposable by design. Insights from an `experiment/*` become a **new task** that follows the normal cycle.
- Examples: `experiment/new-transport-spike`, `experiment/io-uring-investigation`.

> **Host neutrality.** The gates in this rule are enforced two ways: (a) this rule, which every agent obeys; and (b) **branch-protection / merge-check settings configured in your git host's UI** (GitHub, GitLab, Bitbucket, …). Neither replaces the other. Protect `main` and `dev`; require PR review and CI green before merge into `main`.

## 4. Ephemeral branches

Any branch that is not `main`, `dev`, or an `experiment/*` is **ephemeral** — it lives while its work is in progress and is deleted after merge.

### 4.1. Mandatory syntax

```
<type>/<work_id>__<scope>
```

- **`<type>`** — the change category (§4.2).
- **`<work_id>`** — the methodology's `YYYY-MM-DD_short-slug-in-kebab-case` (e.g. `2026-05-16_diary-schedule-service`). Same ID as `{{project}}_wiki/work/{tasks,plans,executions}/{ID}.md`.
- **`<scope>`** — exactly **one** area (module, layer, or subsystem). Never two scopes on one branch.

The **`__` (double underscore)** separator between `<work_id>` and `<scope>` is mandatory — a single underscore would be ambiguous with underscores inside the slug or a scope name.

### 4.2. Valid types (core)

| Type | When | Source | PR target |
|---|---|---|---|
| `feat` | New feature | `dev` | `dev` |
| `fix` | Bug fix | `dev` | `dev` |
| `chore` | Maintenance (deps, lint, config), no behavior change | `dev` | `dev` |
| `docs` | In-repo docs (non-wiki — wiki has its own `/wiki-sync` flow) | `dev` | `dev` |
| `refactor` | Refactor, no behavior change | `dev` | `dev` |
| `hotfix` | Critical production fix | `main` | `main` (then merge-back to `dev`) — §5 |

Every type except `hotfix` branches off `dev`. `hotfix` is the **only** type that branches off `main`.

### 4.3. Module-registered types (extension hook)

Core stays minimal. **Optional modules MAY register additional ephemeral branch types**; for example, the benchmarks module adds `bench` and the contracts module adds `contract`. When such a module is installed, its own rule file defines that type's flow, source, and gate — see `modules/benchmarks/rules/benchmark_protocol_rule.md` and `modules/contracts/rules/contract_change_rule.md`. If a module is **not** installed, its type is not valid here.

### 4.4. Valid examples

```
feat/2026-05-16_diary-schedule-service__scheduler
fix/2026-05-14_connect-timeout__transport
chore/2026-05-20_bump-toolchain__tooling
docs/2026-06-05_wire-protocol__docs
refactor/2026-06-10_buffer-pool__io
hotfix/2026-05-30_crash-on-launch__runtime
experiment/new-transport-spike               (no work_id — outside the formal cycle, never merged)
```

### 4.5. Invalid examples (REJECTED by the gate)

```
feature/diary-schedule_scheduler      ← type "feature" does not exist; single underscore ambiguous
feat/diary-schedule__scheduler        ← missing work_id (no date)
feat/2026-05-16_diary__api__db        ← two scopes
bench/2026-05-25_tpcc__benchmarks     ← type "bench" only valid if the benchmarks module is installed (§4.3)
dev-feature / main_fix                ← collides with a permanent branch
```

### 4.6. Creation gate — mandatory sequence

Before running `git checkout -b <branch>`, the LLM MUST, in order:

1. **Validate** that `{{project}}_wiki/work/plans/{work_id}.md` exists.
2. **Validate** that this plan is `status: approved` in its frontmatter (not `draft`, not `executed`).
3. **Validate** that the branch name obeys §4.1–§4.2 exactly (or `experiment/<slug>` for a spike, which is exempt from steps 1–2).
4. **Announce** the exact command to the human before executing it.

If any check fails: **stop and demand the gate.** Do not invent a branch name; do not skip the plan.

## 5. Hotfix

Hotfixes patch the release line without going through `dev`. They still require a `work_id` and an approved plan — urgency shortens the timeline, it does not suppress the gate (record the accelerated approval in the execution log).

### 5.1. Flow

1. Branch off `main`:
   ```bash
   git checkout main && git pull
   git checkout -b hotfix/<work_id>__<scope>
   ```
2. Implement the fix, commit.
3. Open a PR to `main`.
4. **Mandatory merge-back:** after merging into `main`, merge `main` into `dev` so the fix is not lost.
5. Cut the SemVer patch tag on the merge commit (§7).

## 6. Commits

- **Language:** commit messages in **English**.
- **Format (Conventional Commits):** `<type>(<scope>): <short imperative description>` — e.g. `feat(scheduler): add worker pool router`; `fix(transport): close socket on connect failure`.
- **Granularity:** one commit = one reversible logical unit. Do not amalgamate unrelated changes.
- **Atomic:** avoid leaving "WIP" commits on ephemeral branches before the final PR; clean up with a local interactive rebase.

## 7. Version tags

Format: `vMAJOR.MINOR.PATCH` (SemVer). **No** app/scope prefix — this is a single repo, so a bare tag is unambiguous.

Cut **only** after a `dev → main` merge (or a `hotfix → main` merge). Annotated (`git tag -a`).

```bash
git checkout main && git pull
git tag -a v0.1.0 -m "Release v0.1.0"
git push origin v0.1.0
```

## 8. Canonical Git commands

Use these. Do not invent non-standard flags.

```bash
# Create ephemeral branch (base = dev)
git checkout dev && git pull
git checkout -b <type>/<work_id>__<scope>

# Hotfix (base = main — the only type that does)
git checkout main && git pull
git checkout -b hotfix/<work_id>__<scope>

# Experiment (base = dev, outside the formal cycle)
git checkout dev && git pull
git checkout -b experiment/<slug>

# Sync an ephemeral branch with dev
git checkout <type>/<work_id>__<scope>
git fetch origin
git rebase origin/dev

# Annotated SemVer tag (after dev → main merge)
git checkout main && git pull
git tag -a vX.Y.Z -m "Release vX.Y.Z"
git push origin vX.Y.Z

# Delete ephemeral branch after merge
git push origin --delete <type>/<work_id>__<scope>
git branch -D <type>/<work_id>__<scope>
```

**Destructive operations — require in-the-moment human confirmation.** Announce the exact command and ask **`[y/n]`** before running any of:

- `push --force` (any variant, **including `--force-with-lease` on a permanent branch** `main`/`dev`).
- `branch -D` (unmerged local delete).
- `push --delete` on a permanent branch (`main`, `dev`).
- `branch -m` (rename a permanent branch).
- `reset --hard` on a branch with unpublished commits.

Never chain multiple destructive operations without an intermediate confirmation.

## 9. LLM gates (explicit prohibitions)

These are **forbidden** for any LLM agent. Violations require immediate reversal.

1. ❌ Direct commit into `main` — always forbidden, no exception. To reach `main`, always PR via `dev`.
2. ❌ Direct commit into `dev` without a valid `work_id` in an approved plan (the only exception is a `chore` explicitly approved in a plan).
3. ❌ Creating a branch before its plan is `status: approved`.
4. ❌ Creating a branch with no `work_id` matching a plan in `{{project}}_wiki/work/plans/` (except `experiment/<slug>`).
5. ❌ Creating a dual-scope branch (`feat/x__api__db`). One scope per branch.
6. ❌ Skipping the branch step: each execution gets its own branch.
7. ❌ Merging an `experiment/*` into `dev` or `main` — they are disposable by design.
8. ❌ Using a module-registered type (e.g. `bench`, `contract`) when that module is not installed (§4.3).
9. ❌ `git push --force` (without `--with-lease`) on any branch; any force push on `main`/`dev` without explicit confirmation.
10. ❌ A commit message in a language other than English.
11. ❌ A tag with an app/scope prefix, or an un-annotated tag.
12. ❌ Renaming/deleting a permanent branch without `[y/n]` human confirmation.

## 10. Precedence / Cross-reference

This rule is part of the broader methodology in `.agents/METHODOLOGY.md`. On conflict between this rule and the methodology, **this rule prevails for everything Git- and branch-related**; the methodology prevails for the work cycle (task/plan/execution/wiki-sync) and the wiki. It composes with `mandatory_planning_rule.md`, which owns the plan-approval gate this rule depends on (§4.6). Keep a companion ADR (`{{project}}_wiki/decisions/YYYY-MM-DD_git-branching-strategy.md`) with the context and discarded alternatives.

> **Module precedence.** If the **monorepo module** is installed, its `git_branching_rule.md` **SUPERSEDES this file** — both install to the same path (`.agents/rules/git_branching_rule.md`) and are mutually exclusive; only one is ever present in a project.
