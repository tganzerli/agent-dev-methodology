---
trigger: always_on
---

# Git Branching Rule (monorepo module)

> Installed only when the project is a **monorepo with multiple apps and/or shared packages, each on its own long-lived branch**. In a single-repo project this rule does not apply and must not be installed.

## 1. Core directive

**STOP.** Before creating any branch, opening a Pull Request, or running `git push` in this repository, you MUST validate that the operation respects this rule. This rule is **non-negotiable** for any LLM agent operating in the repo and is the Git-layer counterpart of `mandatory_planning_rule.md`.

## 2. Language requirement

New documents generated under this rule (ADRs, wiki pages) are authored in **{{KNOWLEDGE_LANG}}** (the project's knowledge-content language). Branch names, Git commands, and Git identifiers stay in **English** and pure ASCII — only `[a-z0-9-_]` and `/`, no accents, spaces, or special characters.

## 3. Permanent branches

There are **four classes** of permanent branch. All live forever on the remote; none is deleted. Substitute `<app>` with a real app slug (e.g. `web`, `mobile`) and `<pkg>` with a package slug (e.g. `core`, `ui`).

| Branch | Role | Receives PRs from | Tags |
|---|---|---|---|
| `main` (production) | Production. The collection of stable products. | `staging_<app>` + `tag/<pkg>-vX.Y.Z__<pkg>` + `docs/<id>__knowledge` | No (tags are cut on staging merges or package releases) |
| `staging_<app>` | Release candidate, per app. | `dev_<app>` only | **Yes** — namespaced tag (`web-v1.0.1`, `mobile-v2.3.0`) cut on merge |
| `dev_<app>` | Continuous development, per app. | Ephemeral branches + direct commits (from an approved plan) + CI auto-merge (top-down broadcast from `main` and `dev_packages`) | No |
| `demo_<app>` | Frozen demonstration build (fairs, events). **Terminal** — never promotes to staging/main. | Cherry-picked fixes only; manual rebase onto a stable snapshot | No |

Optionally, projects that share code across apps add a fifth permanent branch:

| Branch | Role | Receives PRs from | Tags |
|---|---|---|---|
| `dev_packages` | Single trunk for all shared packages (`<pkg>`…). **Does NOT contain `apps/*`.** | `pkg/<id>__<pkg>` branches | No (tag is cut on the `tag/* → main` merge) |

> Install `dev_packages` and the package flow (§6) only if the repo has **shared packages consumed by more than one app**. A monorepo of independent apps with no shared package layer skips it.

### 3.1. Promotion flow

**Apps:**

```
feat/<id>__<app>  →  dev_<app>  →  staging_<app>  →  main
                                       ↑
                                 namespaced tag
```

**Packages (trunk model):**

```
pkg/<id>__<pkg>  →  dev_packages  ──(CI: direct auto-merge)──▶  dev_<app>
                          │
                          └── tag/<pkg>-vX.Y.Z__<pkg> ──▶ main ──(CI: auto-merge)──▶ dev_<app> + dev_packages
                                                              ↑
                                                        namespaced tag
```

`demo_<app>` lives outside these flows — fed manually by cherry-picking stable commits.

### 3.2. Gate at each level's entry

- **PR into `main`** requires one of these sources:
  - `staging_<app>` (app release): `staging_<app>` was **rebased onto `main`** immediately before; CI green; human approved the release.
  - `tag/<pkg>-vX.Y.Z__<pkg>` (package release per §6): from `dev_packages`; CHANGELOG present; SemVer bump in the package manifest.
  - `docs/<id>__knowledge` (knowledge layer per `knowledge_source_of_truth_rule.md`).
- **PR into `staging_<app>`** requires: source is `dev_<app>`; the affected app's manifest got a **version bump** (patch/minor/major); CI green. On merge, the `<app>-vX.Y.Z` tag is cut.
- **PR into `dev_<app>`** requires one of: an ephemeral branch with a valid `work_id` (`feat/`, `fix/`, `chore/`, `docs/`, `refactor/`, `hotfix/`); a direct commit from an approved plan; a CI auto-merge (top-down broadcast per §6 — the bot token has a branch-protection exception, humans stay restricted).
- **PR into `dev_packages`** requires: source is `pkg/<work_id>__<pkg>` with an approved plan. Diff restricted to `packages/*` + shared knowledge/tooling.
- **Commit into `demo_<app>`** requires: explicit human confirmation and justification (this branch is frozen).
- **Direct commit into `main` or `staging_*` is FORBIDDEN** — no exception.
- **PR into `main` via `docs/<id>__knowledge`** is allowed **only** for knowledge-layer changes. Gate: the diff must not touch `apps/*/lib/`, `packages/*/lib/`, or any other code path.

> **Host neutrality.** These gates are enforced two ways: (a) this rule, which every agent obeys; and (b) **branch-protection / merge-check settings configured in your git host's UI** (GitHub, GitLab, Bitbucket, …) — see §9. Neither replaces the other.

## 4. Ephemeral branches

Any branch that is not one of the permanent branches above is **ephemeral** — it lives while its task is in progress and is deleted after merge.

### 4.1. Mandatory syntax

```
<type>/<work_id>__<scope>
```

- **`<type>`** — the change category (§4.2).
- **`<work_id>`** — the methodology's `YYYY-MM-DD_short-slug-in-kebab-case` (e.g. `2026-05-16_diary-schedule-service`). Same ID as `{{project}}_wiki/work/{tasks,plans,executions}/{ID}.md`.
- **`<scope>`** — exactly **one** app **OR** exactly **one** package **OR** `knowledge` (for `docs/` branches touching **only** the knowledge layer — see `knowledge_source_of_truth_rule.md` §2) **OR** `tooling` (for shared monorepo tooling/CI — `scripts/`, CI pipeline config, `qa/`, the root workspace manifest, methodology/skills/rules — developed via the normal `dev_<app>` flow). Never two scopes on one branch.

  > **`tooling` vs `knowledge`:** use `knowledge` for pure knowledge-layer `docs/` branches that go **straight to/from `main`** (§7). Use `tooling` when the tooling/CI change is **developed and tested on a `dev_<app>`** (types `chore`/`refactor`/`fix`) — even when it is also knowledge layer — and then promoted to `main` via `/promote-knowledge`. Rule of thumb: **branched off `dev_<app>` → `tooling`; branched off `main` → `knowledge`**.

The **`__` (double underscore)** separator between `<work_id>` and `<scope>` is mandatory — a single underscore would be ambiguous with package names (`some_pkg`, etc.).

### 4.2. Valid types

| Type | When | Source | PR target |
|---|---|---|---|
| `feat` | New feature in an app | `dev_<app>` | `dev_<app>` |
| `fix` | Bug fix in an app | `dev_<app>` | `dev_<app>` |
| `chore` | Maintenance (deps, lint, config), no behavior change | `dev_<app>` | `dev_<app>` |
| `docs` | In-repo docs (non-wiki — wiki has its own `/wiki-sync` flow) | `dev_<app>` | `dev_<app>` |
| `refactor` | Refactor, no behavior change | `dev_<app>` | `dev_<app>` |
| `hotfix` | Critical production fix | `main` | `staging_<app>` → `main` (then merge-back to `dev_<app>`) |
| `pkg` | Change to a shared package | `dev_packages` | `dev_packages` (single PR — §6) |
| `tag` | SemVer release of a package — promotes it to `main` | `dev_packages` | `main` |
| `docs` (knowledge) | Knowledge layer (scope `knowledge`) — rule/skill/wiki/methodology | `main` | `main` |

### 4.3. Valid examples

```
feat/2026-05-16_diary-schedule__mobile
fix/2026-05-14_dfu-disconnect__web
chore/2026-05-20_bump-toolchain__web
pkg/2026-05-22_retry-backoff__core          (off dev_packages, PR to dev_packages — broadcast downstream via CI)
tag/core-v0.4.0__core                       (off dev_packages, PR to main, tag cut on merge)
hotfix/2026-05-30_crash-on-launch__web
docs/2026-05-20_knowledge-source-of-truth__knowledge
chore/2026-07-30_ci-broadcast-tweak__tooling   (shared tooling/CI; off dev_<app>, promoted to main via /promote-knowledge)
```

### 4.4. Invalid examples (REJECTED by the gate)

```
feature/diary-schedule_mobile         ← type "feature" does not exist; single underscore ambiguous
feat/diary-schedule__mobile           ← missing work_id (no date)
feat/2026-05-16_diary__web__mobile    ← two scopes
feat/2026-05-16_diary__co             ← scope must be the full package name
web_dev / web-dev                     ← reserved (the permanent branch is dev_web)
```

### 4.5. Creation gate — mandatory sequence

Before running `git checkout -b <branch>`, the LLM MUST:

1. **Validate** that `{{project}}_wiki/work/plans/{work_id}.md` exists.
2. **Validate** that this plan is `status: approved` in its frontmatter (not `draft`, not `executed`).
3. **Validate** that the branch name obeys §4.1–§4.2 exactly.
4. **Announce** the command to the human before executing.

If any check fails: **stop and demand the gate.** Do not invent a branch name; do not skip the plan.

## 5. Hotfix

Hotfixes patch production without going through `dev_<app>`. They still require a `work_id` and an approved plan (urgency shortens the timeline, it does not suppress the gate).

### 5.1. Flow

1. Branch off `main`:
   ```bash
   git checkout main && git pull
   git checkout -b hotfix/<work_id>__<app>
   ```
2. Implement the fix, commit.
3. Open a PR to `staging_<app>` (not `main` directly) and validate in staging.
4. After validation, open the `staging_<app> → main` PR.
5. **Mandatory merge-back:** after merging into `main`, merge `main` into `dev_<app>` so the fix is not lost.

### 5.2. Tag

The manifest version bump (patch — e.g. `1.0.1 → 1.0.2`) is still required in the PR to `staging_<app>`. The tag is cut on the `staging_<app> → main` merge if it does not already exist.

## 6. Shared-package change — trunk model (`dev_packages`)

*(Install this section only if the repo has shared packages — see §3.)*

Changes to `packages/<pkg>` live on the permanent `dev_packages` trunk. Apps consume via automatic (CI) or manual (skill) distribution.

> **History.** This trunk model replaced an earlier "N twin all-or-nothing PRs" model. If you are installing this kit fresh, **start at the mature trunk + broadcast form** — do not reintroduce the N-PR form.

### 6.1. Change flow

1. **Ephemeral branch** `pkg/<work_id>__<pkg>` off `dev_packages`.
2. **Implementation + single PR** `pkg/<id>__<pkg> → dev_packages`. **The human review gate happens ONCE here.**
3. **After merge into `dev_packages`, top-down broadcast via CI (direct auto-merge):**
   - **Automatic (CI):** the pipeline (`scripts/broadcast-packages.sh`) fires on push to `dev_packages`. For each consuming `dev_<app>`, it does `git merge --no-ff` + `git push` directly — **no intermediate PRs**. The human gate already happened in step 2.
   - **No-op gate:** if the push to `dev_packages` introduced no change under `packages/*` (e.g. a fast-forward of main), CI skips the broadcast to avoid purposeless merge commits.
   - **Best-effort conflict:** if some `dev_<app>` conflicts, CI aborts that one, **continues the others**, and marks the pipeline failed with a log of which conflicted. Manual resolution via `/distribute-packages`.
4. **Manual fallback (`/distribute-packages`):** a dev on a `dev_<app>` can pull ahead of CI, or resolve a post-abort conflict. Useful when CI did not run, the pipeline is down, or bootstrapping a new app.

### 6.2. Contents of `dev_packages`

Contains: `packages/<pkg>/…`; shared tooling (root workspace manifest, etc.); the knowledge layer (present on any branch). Does **NOT** contain `apps/*` — removed on the initial commit. Apps live only on `dev_<app>`.

### 6.3. Promotion to `main` (tagged release)

When bumping a package's SemVer:

1. Ephemeral branch `tag/<pkg>-vX.Y.Z__<pkg>` off `dev_packages`.
2. Bump the package manifest + CHANGELOG (`packages/<pkg>/CHANGELOG.md`).
3. PR → `main`. Reviewer validates CHANGELOG, breaking changes, version.
4. After merge: the namespaced tag `<pkg>-vX.Y.Z` is cut on the merge commit (§7.1).

### 6.4. New apps (bootstrap)

A new app `dev_<newapp>` is born off `main`; its **first action** is `/distribute-packages` to sync with the current `dev_packages` snapshot. Bootstrapping in sync eliminates the accumulated-debt failure mode.

### 6.5. PR conventions

- **`pkg/<id>__<pkg> → dev_packages`:** title `[pkg] <short description> (work_id: <id>)`. Body links the task + scope. **The only PR in the flow** — downstream broadcast is automatic via CI.
- **`tag/<pkg>-vX.Y.Z__<pkg> → main`:** title `[tag] <pkg>-vX.Y.Z`. Body includes CHANGELOG + the list of `pkg/` PRs since the previous tag.

### 6.6. Top-down broadcast: `main → dev_<app>` + `dev_packages`

Analogous to §6.1 but for `main`:

- **Trigger:** push to `main` (any merge — `staging_<app>`, `tag/<pkg>`, `docs/__knowledge`).
- **CI script:** `scripts/broadcast-main.sh` auto-merges `main → dev_<app>` (each) + `dev_packages`. Fast-forward when possible, merge commit otherwise. Knowledge-layer conflicts are auto-reconciled (main is canonical) per `knowledge_source_of_truth_rule.md` §3.6.
- **Best-effort conflict:** same pattern as §6.1.
- **Manual fallback:** `/sync-knowledge` when CI fails or a rare conflict arises.

### 6.7. Admin precondition (host UI)

`dev_*` must have **branch protection** with an explicit exception for the CI **bot token** (a repository access token / deploy key with write scope). Humans stay restricted to PRs; only the token pushes directly via CI. Configure this in your git host's UI (§9).

## 7. Version tags

### 7.1. Namespaced convention

Every tag is prefixed with the app or package name:

```
web-v1.0.1
mobile-v2.3.0
core-v0.4.0            ← cut when a pkg release merges to main
ui-v0.2.1
```

Global tags (e.g. a bare `v1.0.0`) are **forbidden** — they collide in a monorepo.

### 7.2. When to cut

- **App tag** — on the `dev_<app> → staging_<app>` merge (or `staging → main` for a hotfix).
- **Package tag** — on the `tag/<pkg>-vX.Y.Z__<pkg> → main` merge.

### 7.3. Manifest bump

The version bump is **manual** in the `dev → staging` PR, following SemVer: `patch` (fix), `minor` (compatible feat), `major` (breaking). An auto-bump CI step is a possible follow-up.

## 8. Canonical Git commands

Use these. Do not invent non-standard flags.

```bash
# Create ephemeral branch
git checkout dev_<app>            # or: git checkout main (hotfix only)
git pull
git checkout -b <type>/<work_id>__<scope>

# Sync ephemeral branch with its dev_<app>
git checkout <type>/<work_id>__<scope>
git fetch origin
git rebase origin/dev_<app>

# Mandatory rebase of staging onto main (pre-PR to main)
git checkout staging_<app>
git fetch origin
git rebase origin/main
git push --force-with-lease origin staging_<app>   # --force-with-lease, never --force

# Namespaced tag
git tag <app>-vX.Y.Z <merge_commit>
git push origin <app>-vX.Y.Z

# Delete ephemeral branch after merge
git push origin --delete <type>/<work_id>__<scope>
git branch -D <type>/<work_id>__<scope>
```

**Destructive operations — require human confirmation.** `push --force` (any variant, including `--force-with-lease` on a permanent branch), `branch -D` (unmerged local delete), `push --delete` on a permanent branch (`main`, `staging_*`, `dev_*`, `demo_*`) — always announce the command and ask `[y/n]` before running.

## 9. Host configuration — who may change it, and how

Some operations live in the git host's **control panel**, not in `git`: branch protection, required checks, merge settings, a bot's push exception. **By default the agent guides the human through the panel and does not touch them itself.** The menu path varies by host (GitHub → Settings → Rules → Rulesets, or Settings → Branches; GitLab → Settings → Repository → Protected branches; Bitbucket → Repository settings → Branch permissions), so name the concept and let the human find it in their host:

| Situation | Concept to configure in the host UI |
|---|---|
| Protect permanent branches (`main`, `staging_*`, `dev_*`, `demo_*`) | Branch protection / restriction |
| Force PR review before merge | Require N minimum approvals |
| Force CI green before merge | Require successful builds/checks |
| Grant the CI bot token push on `dev_*` | Branch-protection exception for the bot identity |
| PR template | Add the host's PR-template file and commit to `main` |
| Merge strategy (squash/merge/rebase) | Merge settings / merge checks |
| Block force-push on permanent branches | Prevent history rewriting |

When guiding the human, **describe the path for their specific host** and the expected result.

### 9.1. The gate is the authorisation, not the tool

🔒 **An agent never changes host configuration on its own initiative.** That — and only that — is the prohibition. The API is not what is banned: the host's REST API configures **every row of the table above**, so *"not doable via `git`"* was never the same as *"cannot be automated"*. The principle underneath is narrower and holds either way: **access control is the repository owner's to grant, not an agent's to assume.**

With **explicit, per-task human authorisation**, an agent MAY apply the change through the API. Three obligations ride with it, and they are what make the permission auditable instead of a blank cheque:

1. 🔒 **Scoped.** The authorisation covers the named change, in the named work. It does **not** carry to the next task, the next session, or a second change nobody mentioned.
2. 🔒 **Recorded.** The execution log states what changed, **from what to what**, and quotes the authorisation in the human's own words.
3. 🔒 **Read back.** Verify with a fresh read of the host's state — **never trust the exit code of the write.**

**Prefer the panel whenever the agent would have to guess an identifier** — an actor id, an app id, a role name. The panel shows the real list; a wrong guess grants the wrong thing to the wrong actor, and a bypass handed to a repository-admin role instead of the CI identity quietly dissolves the funnel §10.1 depends on.

> **Why this section says "authorisation" instead of "never".** It said "never" until 2026-09-11. In the project this kit came from, the human authorised **three** exceptions to it **on one day** — creating the permanent-branch ruleset, then a repository setting plus a second ruleset, then a CI bypass actor. Each was legitimate, each was scoped in the human's own words, and **not one violated what the section actually protects**: the owner granted, the agent did not assume.
>
> The second of those carried a written trigger — *"if a third arrives, stop writing notes and rewrite this section"* — on the reasoning that a policy suspended every time it binds is not a policy but a ritual with a waiver attached. The third arrived the same day.
>
> This rewrite is deliberately **not** a loosening. The control that was actually in force all three times is now what the text says, plus two obligations (record, read back) that used to be habit and are now required. The failure it avoids is the one catalogued in the kit's own lesson on unexecuted copies: a clause that everybody waives becomes a clause nobody reads.

## 10. LLM gates (explicit prohibitions)

These are **forbidden** for any LLM agent. Violations require immediate reversal.

1. ❌ Direct commit into `main`, `staging_*`, or `dev_*` without a valid `work_id` in an approved plan. Direct push to `main`/`staging_*` is always forbidden.
2. ❌ Creating a branch with no `work_id` matching a plan in `{{project}}_wiki/work/plans/`.
3. ❌ Creating a dual-scope branch (`feat/x__web__mobile`). Use `pkg/` if it affects multiple apps' shared code.
4. ❌ `git push --force` (without `--with-lease`) on any branch.
5. ❌ A `pkg/*` PR not sourced from `dev_packages` or targeting anything other than `dev_packages`. Single trunk — twin PRs to multiple `dev_<app>` are forbidden.
6. ❌ Skipping the `staging_<app> → main` rebase before the PR to `main`.
7. ❌ A global tag (e.g. `v1.0.0`). Always namespaced.
8. ❌ Renaming/deleting a permanent branch without human confirmation.
9. ❌ A `docs/<id>__knowledge` branch that touches **code** (`apps/*/lib/`, `apps/*/test/`, `packages/*/lib/`, `packages/*/test/`, any app/package manifest, lockfiles). Everything else covered by `knowledge_source_of_truth_rule.md` §2 may be touched: the knowledge layer itself, **and the trio files under `{{project}}_wiki/work/` that §2 defines as a third category** (`tasks/`, `plans/`, `executions/`, and the generated `work/_index.md`). The root workspace manifest, `scripts/`, CI pipeline config, and `qa/` **are** knowledge layer and may be touched here.

   > **Why this wording.** An earlier version demanded the diff be "100% inside the knowledge layer". That contradicted §3.2 of this rule, which asks only that the diff *"must not touch `apps/*/lib/`, `packages/*/lib/`, or any other code path"* — and, worse, forbade what this rule's own procedure produces: `/promote-knowledge --trio <id>` (`knowledge_source_of_truth_rule.md` §3.4) promotes a closed trio by creating exactly a `docs/<id>__knowledge` branch carrying trio files. §2 of that rule lists **three** categories, not two, and trio files are the middle one. Found in use by an installation on 2026-09-07; the fix restricts nothing that §3.2 did not already allow.
10. ❌ Editing the knowledge layer on `demo_*`/`staging_*` without explicit human confirmation + justification.
11. ❌ Editing `apps/*` on `dev_packages`, or creating a `pkg/<id>__<app>` branch. `dev_packages` is packages-only.
12. ❌ A human pushing directly to `dev_<app>` (without a PR, and without being the CI bot token). The CI auto-merge has a branch-protection exception; humans stay restricted to PRs.

## 11. Cross-reference

This rule is part of the broader methodology in `.agents/METHODOLOGY.md`. On conflict between this rule and the methodology, **this rule prevails for everything Git- and branch-related**; the methodology prevails for the work cycle (task/plan/execution/wiki-sync) and the wiki. Keep a companion ADR (`{{project}}_wiki/decisions/YYYY-MM-DD_git-branching-strategy.md`) with the context and discarded alternatives.
