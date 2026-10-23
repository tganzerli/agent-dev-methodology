---
trigger: always_on
---

# Git Branching Rule (monorepo module)

> Monorepo module only — multiple apps and/or shared packages, each on its own long-lived branch. Never installed in a single-repo project.

## 1. Core directive

**STOP.** Before creating any branch, opening a Pull Request, or running `git push` in this repository, you MUST validate that the operation respects this rule. **Non-negotiable** for every agent; the Git-layer counterpart of `mandatory_planning_rule.md`.

<!-- OPTIONAL §1.1 — keep it at install ONLY if no dev_<app> exists yet; otherwise delete this whole section. -->
## 1.1. Transition state — before the first `dev_<app>` (IN FORCE)

> ⚠ **Read this first.** While this section is present, the rest of this rule describes the **future** topology, not the current one.

Why: with zero apps the plan gate, the trio rule and §3.2 deadlock (`git-runbook` §5.1).

**Rule in force meanwhile:** *all work happens directly on `main`.* A direct commit to `main` is **allowed** and is the normal flow; §3.2's prohibition is **suspended for `main`** until the trigger.

**The trigger that ends it:** the creation of the first `dev_<app>`. From then, with no grace period, §3 on applies in full (§3.2 included) and **this section is deleted** — not marked expired. Check: `git branch --list 'dev_*'`; `scripts/check-transition-state.sh` fails CI if a `dev_*` exists while this section is here; the plan creating the first `dev_<app>` lists this rule under "Rules affected".

**What it does NOT relax:** the plan gate (`mandatory_planning_rule.md`) — no code change before an `approved` plan, on `main` as anywhere. It relaxes **where a commit may land**, never **whether the work was planned and approved**.

Genesis commit and bootstrap without a `dev_<app>` (the monorepo skills abort until one exists; run `scripts/check-knowledge-paths.py` in CI meanwhile): `git-runbook` §5.1.

## 2. Language requirement

New documents generated under this rule (ADRs, wiki pages) are authored in **{{KNOWLEDGE_LANG}}** (the project's knowledge-content language). Branch names, Git commands, and Git identifiers (including the Conventional Commits type) stay in **English** and pure ASCII — only `[a-z0-9-_]` and `/`, no accents, spaces, or special characters. Commit messages and PR titles/bodies are written in **{{COMMIT_LANG}}** (the commit language chosen at install).

## 3. Permanent branches

There are **four classes** of permanent branch. All live forever on the remote; none is deleted. `<app>` and `<pkg>` stand for real app and package slugs.

| Branch | Role | Receives PRs from | Tags |
|---|---|---|---|
| `main` (production) | Production. The collection of stable products. | `staging_<app>` + `tag/<pkg>-vX.Y.Z__<pkg>` + `docs/<id>__knowledge` (+ `contract/<id>__<surface>` with the contracts module) | No (tags are cut on staging merges or package releases) |
| `staging_<app>` | Release candidate, per app. | `dev_<app>` only | **Yes** — namespaced tag (`web-v1.0.1`, `mobile-v2.3.0`) cut on merge |
| `dev_<app>` | Continuous development, per app. | Ephemeral branches + CI auto-merge (top-down broadcast from `main` and `dev_packages`) | No |
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

**Packages (trunk model):** `pkg/<id>__<pkg> → dev_packages`, broadcast by CI into each `dev_<app>`; a release goes `tag/<pkg>-vX.Y.Z__<pkg> → main`, broadcast back into `dev_<app>` + `dev_packages` (diagram: `git-runbook` §1).

### 3.2. Gate at each level's entry

- **PR into `main`** requires one of these sources:
  - `staging_<app>` (app release): `staging_<app>` was **rebased onto `main`** immediately before; CI green; human approved the release.
  - `tag/<pkg>-vX.Y.Z__<pkg>` (package release per §6): from `dev_packages`; CHANGELOG present; SemVer bump in the package manifest.
  - `docs/<id>__knowledge` — **only** knowledge-layer changes (`knowledge_source_of_truth_rule.md`): the diff must not touch `apps/*/lib/`, `packages/*/lib/`, or any other code path.
  - `contract/<id>__<surface>` (contracts module only) — **only** a change to a versioned cross-boundary contract, atomic per `contract_change_rule.md`: the contract, the implementation, the ADR, **every** in-repo consumer, the tests and the knowledge page, in the same diff. Why `main`: `git-runbook` §5.3.
- **PR into `staging_<app>`** requires: source is `dev_<app>`; the affected app's manifest got a **version bump** (patch/minor/major); CI green. On merge, the `<app>-vX.Y.Z` tag is cut.
- **PR into `dev_<app>`** requires one of: an ephemeral branch with a valid `work_id` (`feat/`, `fix/`, `chore/`, `docs/`, `refactor/`, `hotfix/`, or a module-registered type — §4.2); a CI auto-merge (the broadcast, §6).

  > **There is no direct commit into `dev_<app>`, not even from an approved plan** (why: `git-runbook` §5.2).
- **PR into `dev_packages`** requires: source is `pkg/<work_id>__<pkg>` with an approved plan. Diff restricted to `packages/*` + shared knowledge/tooling.
- **Commit into `demo_<app>`** requires: explicit human confirmation and justification (this branch is frozen).
- **Direct commit into `main` or `staging_*` is FORBIDDEN** — no exception.
  (Before the first `dev_<app>`, the optional §1.1 suspends this for `main`; the genesis commit: `git-runbook` §5.1.)

> **Host neutrality.** Enforced two ways: this rule, which every agent obeys, and the **host's branch-protection / merge-check settings** (§9). Neither replaces the other.

## 4. Ephemeral branches

Every other branch is **ephemeral** — it lives while its task is in progress and is deleted after merge.

### 4.1. Mandatory syntax

```
<type>/<work_id>__<scope>
```

- **`<type>`** — the change category (§4.2).
- **`<work_id>`** — the methodology's `YYYY-MM-DD_short-slug-in-kebab-case` — the same ID as `{{project}}_wiki/work/{tasks,plans,executions}/{ID}.md`.
- **`<scope>`** — exactly **one** of: an app; a package; `knowledge` (`docs/` branches touching **only** the knowledge layer — `knowledge_source_of_truth_rule.md` §2); `tooling` (shared tooling/CI — `scripts/`, CI config, `qa/`, the root workspace manifest, methodology/skills/rules — developed on a `dev_<app>`); a **contract surface** (`contract/` only, e.g. `public-api`). Never two scopes on one branch.

  > **`tooling` vs `knowledge`:** branched off `dev_<app>` → `tooling` (promoted to `main` via `/promote-knowledge`); branched off `main` → `knowledge`. Why: `git-runbook` §3.2.

The **`__`** separator between `<work_id>` and `<scope>` is mandatory — a single `_` is ambiguous with package names.

### 4.2. Valid types

| Type | When | Source | PR target |
|---|---|---|---|
| `feat` | New feature in an app | `dev_<app>` | `dev_<app>` |
| `fix` | Bug fix in an app | `dev_<app>` | `dev_<app>` |
| `chore` | Maintenance (deps, lint, config), no behavior change | `dev_<app>` | `dev_<app>` |
| `docs` | In-repo docs (the wiki has `/wiki-sync`) | `dev_<app>` | `dev_<app>` |
| `refactor` | Refactor, no behavior change | `dev_<app>` | `dev_<app>` |
| `hotfix` | Critical production fix | `main` | `staging_<app>` → `main` (then merge-back to `dev_<app>`) |
| `pkg` | Change to a shared package | `dev_packages` | `dev_packages` (single PR — §6) |
| `tag` | SemVer release of a package — promotes it to `main` | `dev_packages` | `main` |
| `docs` (knowledge) | Knowledge layer (scope `knowledge`) — rule/skill/wiki/methodology | `main` | `main` |
| `bench` | Benchmark work (`benchmark_protocol_rule.md`) | `dev_<app>` | `dev_<app>` |
| `contract` | Versioned cross-boundary contract change (`contract_change_rule.md`) — **atomic** (§3.2) | `main` | `main` |

**Variant — the contract is a shared package:** `contract/<id>__<pkg>` off and into `dev_packages`, only if this rule names it in place of the `contract` row (recipe, trade-off, `SCOPE_CONTRACT_LINE`: `git-runbook` §5.3).

**Module-registered types.** `bench` (benchmarks) and `contract` (contracts) are valid **only while their module is installed**; delete the row of a module not installed. The module's rule owns what rides on the branch; this table owns where it starts and lands.

### 4.3. Valid examples

`git-runbook` §3.2 (one per type).

### 4.4. Invalid examples (REJECTED by the gate)

`git-runbook` §3.2.

### 4.5. Creation gate — mandatory sequence

Before running `git checkout -b <branch>`, the LLM MUST:

1. **Validate** that `{{project}}_wiki/work/plans/{work_id}.md` exists.
2. **Validate** that this plan is `status: approved` in its frontmatter (not `draft`, not `executed`).
3. **Validate** that the branch name obeys §4.1–§4.2 exactly.
4. **Announce** the command to the human before executing.

If any check fails: **stop and demand the gate.** Do not invent a branch name; do not skip the plan.

**Tool-created branch or worktree:** no second one; commit nothing guarded on it before approval; rename it in place (`git branch -m <type>/<work_id>__<scope>`, announced) only if it sits on the type's source line (§4.2), else branch from that line. Procedure: `git-runbook` §3.1.

### 4.6. Branch scope barrier — what each branch may write

The branch name (§4.1) is not a label: it is a **scope declaration**, and CI checks it. The invariant:

> 🔒 **`apps/<X>` diverges only on X's line** — `dev_X`, `staging_X` and ephemerals `__<X>`.
> **`packages/<P>` diverges only on the packages line** — `dev_packages` and ephemerals `__<P>`.
> On every other branch those paths are identical to what the branch **received** from its source.

Three operational rules follow:

1. **Derivation.** To change `apps/<X>` a branch must come from `dev_<X>` (or `staging_<X>`, or `main` for a `hotfix`). To change `packages/<P>` it must come from `dev_packages`. A `contract/` branch comes from `main` and may touch every consumer (§3.2).
2. **No contamination.** No branch writes to an app outside its scope — by edit, or by a merge that carries another app's snapshot.
3. **Single distribution path.** App code reaches other branches only via `staging_<X> → main` and then the broadcast (§6). No lateral shortcut.

Checked by `scripts/check_branch_scope.sh` on every PR and on push to `dev_<app>` — **advisory** by default (`SCOPE_BARRIER_BLOCKING=1` blocks); hard prevention is branch protection requiring PRs on `dev_*` (§9). How and why: `git-runbook` §5.4.

## 5. Hotfix

Hotfixes patch production without going through `dev_<app>`. They still require a `work_id` and an approved plan (urgency shortens the timeline, it does not suppress the gate).

### 5.1. Flow

1. Branch off `main` (`hotfix/<work_id>__<app>`; commands in the `git-runbook` skill).
2. Implement the fix, commit.
3. Open a PR to `staging_<app>` (not `main` directly) and validate in staging.
4. After validation, open the `staging_<app> → main` PR.
5. **Mandatory merge-back:** after merging into `main`, merge `main` into `dev_<app>` so the fix is not lost.

### 5.2. Tag

The manifest version bump (patch — e.g. `1.0.1 → 1.0.2`) is still required in the PR to `staging_<app>`. The tag is cut on the `staging_<app> → main` merge if it does not already exist.

## 6. Shared-package change — trunk model (`dev_packages`)

*(Install this section only if the repo has shared packages — see §3.)*

Invoke **`git-runbook`** §1 (the recipe) **before** opening a `pkg/` or `tag/` branch or touching `dev_packages`. The gates:

- 🔒 **`pkg/<work_id>__<pkg>` branches off `dev_packages` and has a single PR into `dev_packages`.** The human review gate happens **once**, there; the CI broadcast (`scripts/broadcast-packages.sh`) then merges into each consuming `dev_<app>` with no intermediate PR. Twin PRs into several `dev_<app>` are forbidden (§10 gate 5).
- 🔒 **`dev_packages` does not contain `apps/*`** (§10 gate 11).
- 🔒 **A package release** is a `tag/<pkg>-vX.Y.Z__<pkg>` branch off `dev_packages` with a SemVer bump and a CHANGELOG entry, PR into `main` (§3.2); the tag is cut by hand on the merge commit (§7.2).
- 🔒 **New app bootstrap:** the first action on a fresh `dev_<newapp>` (born off `main`) is `/distribute-packages`, to sync with the current `dev_packages` snapshot.
- 🔒 **PR titles:** `pkg/` → `[pkg] <description> (work_id: <id>)`; `tag/` → `[tag] <pkg>-vX.Y.Z`, body = the CHANGELOG + the `pkg/` PRs since the previous tag.
- 🔒 **Every ephemeral PR** (`<type>/<work_id>__<scope>` into its `dev_*` trunk, including `pkg/`): opened only with the validations green **with their output recorded** in the execution, the agent review closed with no open `Important` finding (or `skipped — low`), and the human review done at the depth the plan's risk tier sets (`.agents/METHODOLOGY.md` §4.4.1). The body states **Testing**, **Risk** and **How to revert**, taken from plan §4.4.
- 🔒 **Broadcast failures are resolved by hand, never forced:** `/distribute-packages` for `dev_packages → dev_<app>`, `/sync-knowledge` for `main → dev_*` (knowledge-layer conflicts in Group A are auto-reconciled per `knowledge_source_of_truth_rule.md` §3.6; everything else aborts).
- 🔒 **Admin precondition:** `dev_*` carries branch protection with a push exception for the CI identity only (a deploy key or bot token with write scope). Humans stay restricted to PRs. Configured in the host (§9).

## 7. Version tags

### 7.1. Namespaced convention

Every tag is prefixed with the app or package name — `web-v1.0.1`, `core-v0.4.0`. Global tags (a bare `v1.0.0`) are **forbidden** — they collide in a monorepo.

### 7.2. When to cut

- **App tag** — on the `dev_<app> → staging_<app>` merge (or `staging → main` for a hotfix).
- **Package tag** — on the `tag/<pkg>-vX.Y.Z__<pkg> → main` merge.

**Tags are MANUAL — the CI creates none** (unless the project adds and documents a tagging job). Whoever merges the release PR cuts the tag. Before tagging, verify the **target commit**: it is the merge commit on `main` (or `staging_<app>`), never the `HEAD` of your local tree.

### 7.3. Manifest bump

The version bump is **manual** in the `dev → staging` PR, following SemVer: `patch` (fix), `minor` (compatible feat), `major` (breaking).

## 8. Git commands and destructive operations

Canonical commands (create, sync, rebase staging, tag, delete): the **`git-runbook`** skill (§3). Use those; do not invent non-standard flags.

**Destructive operations — require human confirmation.** `push --force` (any variant, including `--force-with-lease` on a permanent branch), `branch -D` (unmerged local delete), `push --delete` on a permanent branch (`main`, `staging_*`, `dev_*`, `demo_*`) — always announce the command and ask `[y/n]` before running.

## 9. Host configuration — who may change it, and how

Some operations live in the git host's **control panel**, not in `git`: branch protection, required checks, merge settings, a bot's push exception. **By default the agent guides the human through the panel** — the path for their specific host and the expected result — **and does not touch them itself.** The **`git-runbook`** skill (§4) lists the settings and where each host keeps them.

⚠ **Require a status check on a branch only once CI actually fires there** — a check no event produces **waits forever**, and every PR into that branch hangs. Add it in the work that extends CI to that branch (`git-runbook` §5.6).

### 9.1. The gate is the authorisation, not the tool

🔒 **An agent never changes host configuration on its own initiative.** That — and only that — is the prohibition. The API is not what is banned: **access control is the repository owner's to grant, not an agent's to assume.**

With **explicit, per-task human authorisation**, an agent MAY apply the change through the API. Three obligations ride with it:

1. 🔒 **Scoped.** The authorisation covers the named change, in the named work. It does **not** carry to the next task, the next session, or a second change nobody mentioned.
2. 🔒 **Recorded.** The execution log states what changed, **from what to what**, and quotes the authorisation in the human's own words.
3. 🔒 **Read back.** Verify with a fresh read of the host's state — **never trust the exit code of the write.**

**Prefer the panel whenever the agent would have to guess an identifier** (actor id, app id, role name): a bypass handed to the wrong role dissolves the funnel §10 gate 1 depends on.

Why "authorisation" and not "never": `git-runbook` §5.7.

## 10. LLM gates (explicit prohibitions)

These are **forbidden** for any LLM agent. Violations require immediate reversal.

1. ❌ Direct push to `main`, `staging_*` or `dev_*` — always, except `main` while the optional §1.1 is present. Every change enters a permanent branch through a PR from an ephemeral branch with a valid `work_id` in an approved plan, or through the CI bot token's auto-merge. An approved plan authorises the **work**, never the **push path** (see the note in §3.2).
2. ❌ Creating a branch with no `work_id` matching a plan in `{{project}}_wiki/work/plans/`.
3. ❌ Creating a dual-scope branch (`feat/x__web__mobile`). Use `pkg/` if it affects multiple apps' shared code.
4. ❌ `git push --force` (without `--with-lease`) on any branch.
5. ❌ A `pkg/*` PR not sourced from `dev_packages` or targeting anything other than `dev_packages`. Single trunk — twin PRs to multiple `dev_<app>` are forbidden.
6. ❌ Skipping the `staging_<app> → main` rebase before the PR to `main`.
7. ❌ A global tag (e.g. `v1.0.0`). Always namespaced.
8. ❌ Renaming/deleting a permanent branch without human confirmation.
9. ❌ A `docs/<id>__knowledge` branch that touches **code** (`apps/*/lib/`, `apps/*/test/`, `packages/*/lib/`, `packages/*/test/`, any app/package manifest, lockfiles). Everything else in `knowledge_source_of_truth_rule.md` §2 may be touched: the knowledge layer (the root workspace manifest, `scripts/`, CI config and `qa/` included) **and the trio files under `{{project}}_wiki/work/`**, §2's third category (why: `git-runbook` §5.8).
10. ❌ Editing the knowledge layer on `demo_*`/`staging_*` without explicit human confirmation + justification.
11. ❌ Editing `apps/*` on `dev_packages`, or creating a `pkg/<id>__<app>` branch. `dev_packages` is packages-only.
12. ❌ A human pushing directly to `dev_<app>` (without a PR, and without being the CI bot token). A manual broadcast while CI is down is allowed only under a named, dated exception written into this rule (recipe: `git-runbook` §1.6.1).
13. ❌ Using a module-registered type (`bench`, `contract`) when its module is not installed (§4.2).

## 11. Cross-reference

On conflict between this rule and `.agents/METHODOLOGY.md`, **this rule prevails for everything Git- and branch-related**; the methodology prevails for the work cycle (task/plan/execution/wiki-sync) and the wiki. Keep a companion ADR (`{{project}}_wiki/decisions/YYYY-MM-DD_git-branching-strategy.md`) with the context and discarded alternatives.
