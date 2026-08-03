---
name: distribute-packages
description: MANUAL FALLBACK for the packages broadcast dev_packages → dev_<app>. In normal operation the broadcast is automatic via CI (scripts/broadcast-packages.sh — direct auto-merge, no PRs). Use this skill only when CI failed (a best-effort conflict aborted that dev), the pipeline is down, or bootstrapping a new app. Applies git merge --no-ff origin/dev_packages with a human gate. Aborts on non-dev_<app> branches.
argument-hint: ""
disable-model-invocation: true
allowed-tools: Bash(git *), Read
---

# Distribute Packages (manual fallback)

> ⚠ **Fallback role.** The `dev_packages → dev_<app>` broadcast is **automatic via CI** (`scripts/broadcast-packages.sh` does a direct auto-merge, no PRs). This skill is a **manual fallback** — use it only when:
> - CI failed on a specific `dev_<app>` (best-effort aborted on conflict).
> - The CI pipeline is unavailable.
> - Bootstrapping a new app (first sync of a fresh `dev_<newapp>`).
> - Pulling ahead of CI (rarely useful).
>
> In normal flow, **do not use this skill** — CI handles it.

> **Monorepo module skill.** Install only if the repo has shared packages on a `dev_packages` trunk (see `git_branching_rule.md` §6). In a single-repo project it does not apply.

Syncs the current branch (`dev_<app>`) with `dev_packages` (the single package trunk), implementing `.agents/rules/git_branching_rule.md` §6 (fallback).

## When to use

- **Start of a session on `dev_<app>`** when you suspect divergence.
- **Bootstrapping a new app** — the first action after creating `dev_<newapp>` off `main`.
- **Before work** that depends on a package feature just merged into `dev_packages` (not waiting for CI).
- **CI fallback** — when the pipeline is down or the auto-merge aborted on conflict.

## When NOT to use

- On `main`, `staging_*`, `demo_*`, or `dev_packages` — the skill aborts at step 1.
- With uncommitted changes — commit or stash first.

## Steps

### 1. Validate context

- `git branch --show-current` → must be `dev_<app>`. Otherwise **abort** with a clear message.
- `git status --short` → must be empty. If dirty, instruct `commit`/`stash`.
- `git fetch origin dev_packages`.

### 2. Detect divergence

Compare `HEAD` vs `origin/dev_packages` for packages and shared tooling:

```bash
git diff --name-only HEAD origin/dev_packages -- \
  packages/ \
  scripts/ <CI pipeline config> <root workspace manifest>
```

Exclude paths that should **NOT** arrive via distribute (per-app or wiki): `apps/*` (dev_packages does not have them), `{{project}}_wiki/work/` (per-branch), gitignored files.

**If empty** → report "Packages already in sync with `dev_packages`" and stop.

### 3. Present the plan (gate)

List the files to bring in:

```
I will apply `git merge --no-ff origin/dev_packages` on the current branch <branch>.

N files will come from origin/dev_packages@<short sha>:
  - packages/core/lib/.../file.ext (will be modified)
  - packages/ui/lib/.../new.ext (new)
  - ...

Confirm? (y/n)
```

Without an explicit `y` → abort (do not touch the working tree).

### 4. Apply the merge

```bash
SHA=$(git rev-parse --short origin/dev_packages)
git merge --no-ff origin/dev_packages \
  -m "distribute: packages in sync with dev_packages@${SHA}"
```

### 5. Resolve conflicts (if any)

Typical conflicts:
- `{{project}}_wiki/work/_index.md` — the work index is per-branch; divergence is expected when `dev_<app>` gained its own trios between distributions. Prefer regenerating via `/work-index` over hand-merging.
- `.agents/rules/*` — only if there was a parallel change in both `dev_packages` and `dev_<app>` to the same file (rare — knowledge normally flows via main).

For each conflict: human gate. **Do not resolve automatically.**

### 6. Verify the staged diff

```bash
git status --short
git diff --cached --stat
```

Present a summary.

### 7. Push (optional)

Ask: `Packages distributed. Push to origin/<current branch>? (y/n)`. If `y` → `git push origin <branch>`.

## Anti-patterns

- ❌ Running on non-`dev_<app>` branches (the skill aborts).
- ❌ Applying without reviewing the list (skipping step 3).
- ❌ Forcing with a dirty working tree.
- ❌ Using `git merge --ff-only` instead of `--no-ff` — the explicit merge commit matters for audit ("this came from a dev_packages distribution, not feature work").
- ❌ Resolving conflicts without knowing which side is canonical (for `_index.md`, regenerate; for package code, keep dev_packages).

## Cross-references

- `.agents/rules/git_branching_rule.md` §6 — the rule this skill implements.
- `{{project}}_wiki/decisions/YYYY-MM-DD_packages-trunk-strategy.md` — the ADR that motivated the trunk model.
- `scripts/broadcast-packages.sh` — the automatic CI counterpart this skill backs up.
- `.claude/skills/sync-knowledge/SKILL.md` — sibling skill with a similar pattern (sync from a canonical branch).
