---
trigger: always_on
---

# Git Branching Rule (monorepo module)

> Installed only when the project is a **monorepo with multiple apps and/or shared packages, each on its own long-lived branch**. In a single-repo project this rule does not apply and must not be installed.

## 1. Core directive

**STOP.** Before creating any branch, opening a Pull Request, or running `git push` in this repository, you MUST validate that the operation respects this rule. This rule is **non-negotiable** for any LLM agent operating in the repo and is the Git-layer counterpart of `mandatory_planning_rule.md`.

<!-- OPTIONAL §1.1 — keep it at install ONLY if no dev_<app> exists yet; otherwise delete this whole section. -->
## 1.1. Transition state — before the first `dev_<app>` (IN FORCE)

> ⚠ **Read this first.** While this section is present, the rest of this rule describes the **future** topology, not the current one.

**In force:** from install until the first `dev_<app>` branch is created.

Why: with zero apps the plan gate, the trio rule and §3.2 deadlock (`git-runbook` §5.1).

**Rule in force meanwhile:** *all work happens directly on `main`.* A direct commit to `main` is **allowed** and is the normal flow; §3.2's prohibition is **suspended for `main`** until the trigger.

**The trigger that ends it:** the creation of the first `dev_<app>`. From that moment, with no grace period, §3.2 applies in full, the topology from §3 on is mandatory, and **this section is deleted** from the file — not marked expired. Check: `git branch --list 'dev_*'`; `scripts/check-transition-state.sh` fails CI if a `dev_*` exists while this section is here; the plan creating the first `dev_<app>` lists this rule under "Rules affected".

**What it does NOT relax:** the plan gate. `mandatory_planning_rule.md` is independent of this rule — no code change before an `approved` plan, on `main` as anywhere. This section relaxes **where a commit may land**, never **whether the work was planned and approved**.

Genesis commit and bootstrap without a `dev_<app>` (the monorepo skills abort until one exists; run `scripts/check-knowledge-paths.py` in CI meanwhile): `git-runbook` §5.1.

## 2. Language requirement

New documents generated under this rule (ADRs, wiki pages) are authored in **{{KNOWLEDGE_LANG}}** (the project's knowledge-content language). Branch names, Git commands, and Git identifiers (including the Conventional Commits type) stay in **English** and pure ASCII — only `[a-z0-9-_]` and `/`, no accents, spaces, or special characters. Commit messages and PR titles/bodies are written in **{{COMMIT_LANG}}** (the commit language chosen at install).

## 3. Permanent branches

There are **four classes** of permanent branch. All live forever on the remote; none is deleted. Substitute `<app>` with a real app slug (e.g. `web`, `mobile`) and `<pkg>` with a package slug (e.g. `core`, `ui`).

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
  - `contract/<id>__<surface>` (contracts module only — a versioned cross-boundary contract per `contract_change_rule.md`): the ADR is present, and every in-repo consumer is updated **in the same diff**.
- **PR into `staging_<app>`** requires: source is `dev_<app>`; the affected app's manifest got a **version bump** (patch/minor/major); CI green. On merge, the `<app>-vX.Y.Z` tag is cut.
- **PR into `dev_<app>`** requires one of: an ephemeral branch with a valid `work_id` (`feat/`, `fix/`, `chore/`, `docs/`, `refactor/`, `hotfix/`, or a module-registered type — §4.2); a CI auto-merge (top-down broadcast per §6 — the bot token has a branch-protection exception, humans stay restricted).

  > **There is no direct commit into `dev_<app>`, not even from an approved plan** (why: `git-runbook` §5.2).
- **PR into `dev_packages`** requires: source is `pkg/<work_id>__<pkg>` with an approved plan. Diff restricted to `packages/*` + shared knowledge/tooling.
- **Commit into `demo_<app>`** requires: explicit human confirmation and justification (this branch is frozen).
- **Direct commit into `main` or `staging_*` is FORBIDDEN** — no exception.
  (Before the first `dev_<app>` exists, the optional §1.1 suspends this for `main`, and the genesis commit is an ordering case — both described there.)
- **PR into `main` via `docs/<id>__knowledge`** is allowed **only** for knowledge-layer changes. Gate: the diff must not touch `apps/*/lib/`, `packages/*/lib/`, or any other code path.
- **PR into `main` via `contract/<id>__<surface>`** is allowed **only** for a change to a versioned cross-boundary contract, and **only** when the diff is atomic in the sense of `contract_change_rule.md`: the contract, the implementation, **every** in-repo consumer, the tests and the knowledge page, together.

  Why `main`: `git-runbook` §5.3.

> **Host neutrality.** These gates are enforced two ways: (a) this rule, which every agent obeys; and (b) **branch-protection / merge-check settings configured in your git host's UI** (GitHub, GitLab, Bitbucket, …) — see §9. Neither replaces the other.

## 4. Ephemeral branches

Any branch that is not one of the permanent branches above is **ephemeral** — it lives while its task is in progress and is deleted after merge.

### 4.1. Mandatory syntax

```
<type>/<work_id>__<scope>
```

- **`<type>`** — the change category (§4.2).
- **`<work_id>`** — the methodology's `YYYY-MM-DD_short-slug-in-kebab-case` (e.g. `2026-05-16_diary-schedule-service`). Same ID as `{{project}}_wiki/work/{tasks,plans,executions}/{ID}.md`.
- **`<scope>`** — exactly **one** app **OR** exactly **one** package **OR** `knowledge` (for `docs/` branches touching **only** the knowledge layer — see `knowledge_source_of_truth_rule.md` §2) **OR** `tooling` (for shared monorepo tooling/CI — `scripts/`, CI pipeline config, `qa/`, the root workspace manifest, methodology/skills/rules — developed via the normal `dev_<app>` flow) **OR** a **contract surface** (`contract/` branches only — e.g. `public-api`, `shared-packages`, `wire-protocol`: the change lands in every consumer at once, so one app or package name would misdescribe the diff). Never two scopes on one branch.

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
| `bench` | Benchmark work (`benchmark_protocol_rule.md`) — evidence page, dataset, command, versioned artifacts | `dev_<app>` | `dev_<app>` |
| `contract` | Change to a versioned cross-boundary contract (`contract_change_rule.md`) — **atomic**: contract + implementation + every consumer + tests + knowledge page | `main` | `main` (§3.2) |

**Variant — the contract is a shared package.** A project whose versioned contract *is* a package (`packages/<contract>`) may instead cut `contract/<id>__<pkg>` off `dev_packages` and PR it into `dev_packages`, consumers following on their own branches — only if this rule names the variant in place of the `contract` row above (trade-off, and `SCOPE_CONTRACT_LINE=dev_packages` for the barrier: `git-runbook` §5.3).

**Module-registered types.** `bench` (benchmarks module) and `contract` (contracts module) are valid **only while their module is installed**; delete the row of a module the project did not install. The module's own rule owns what must ride on the branch; this table owns where the branch starts and lands.

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
bench/2026-08-02_decode-throughput__web        (benchmarks module; off dev_<app>, PR to dev_<app>)
contract/2026-08-04_retire-legacy__public-api  (contracts module; off main, PR to main — atomic across every consumer)
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

**Tool-created branch or worktree.** If a tool already created a branch or worktree for the session, do not create a second one: commit nothing guarded on it before approval, then rename it in place (`git branch -m <type>/<work_id>__<scope>`, announced) — only if it sits on the type's source line from §4.2; otherwise create the branch from that line instead. Procedure: `git-runbook` §3.1.

### 4.6. Branch scope barrier — what each branch may write

The branch name (§4.1) is not a label: it is a **scope declaration**, and CI checks it. The invariant:

> 🔒 **`apps/<X>` diverges only on X's line** — `dev_X`, `staging_X` and ephemerals `__<X>`.
> **`packages/<P>` diverges only on the packages line** — `dev_packages` and ephemerals `__<P>`.
> On every other branch those paths are identical to what the branch **received** from its source.

Three operational rules follow:

1. **Derivation.** To change `apps/<X>` a branch must come from `dev_<X>` (or `staging_<X>`, or `main` for a `hotfix`). To change `packages/<P>` it must come from `dev_packages`. A `contract/` branch comes from `main` and may touch every consumer (§3.2).
2. **No contamination.** No branch writes to an app outside its scope — by edit, or by a merge that carries another app's snapshot.
3. **Single distribution path.** App code reaches other branches only via `staging_<X> → main` and then the broadcast (§6). No lateral shortcut.

Checked by `scripts/check_branch_scope.sh` on every PR and on push to `dev_<app>` — **advisory** by default (`SCOPE_BARRIER_BLOCKING=1` blocks; flip only after clean runs across real releases); hard prevention is branch protection requiring PRs on `dev_*` (§9). How it works and why: `git-runbook` §5.4.

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

Packages live on the permanent `dev_packages` trunk; apps receive them by broadcast. Invoke the **`git-runbook`** skill (the recipe) **before** opening a `pkg/` or `tag/` branch or touching `dev_packages`. The gates:

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

**Tags are MANUAL — the CI creates none** (unless the project adds and documents a tagging job). Whoever merges the release PR cuts the tag. Before tagging, verify the **target commit**: it is the merge commit on `main` (or `staging_<app>`), never the `HEAD` of your local tree.

### 7.3. Manifest bump

The version bump is **manual** in the `dev → staging` PR, following SemVer: `patch` (fix), `minor` (compatible feat), `major` (breaking). An auto-bump CI step is a possible follow-up.

## 8. Git commands and destructive operations

The canonical commands (create, sync, rebase staging, tag, delete) are in the **`git-runbook`** skill. Use those; do not invent non-standard flags.

**Destructive operations — require human confirmation.** `push --force` (any variant, including `--force-with-lease` on a permanent branch), `branch -D` (unmerged local delete), `push --delete` on a permanent branch (`main`, `staging_*`, `dev_*`, `demo_*`) — always announce the command and ask `[y/n]` before running.

## 9. Host configuration — who may change it, and how

Some operations live in the git host's **control panel**, not in `git`: branch protection, required checks, merge settings, a bot's push exception. **By default the agent guides the human through the panel and does not touch them itself.** The **`git-runbook`** skill lists the settings and where each host keeps them.

When guiding the human, **describe the path for their specific host** and the expected result.

⚠ **Require a status check on a branch only once CI actually fires there.** A required check that no event produces does not fail — it **waits forever**, and every PR into that branch hangs. Add the required checks in the same work that extends CI to that branch.

### 9.1. The gate is the authorisation, not the tool

🔒 **An agent never changes host configuration on its own initiative.** That — and only that — is the prohibition. The API is not what is banned: **access control is the repository owner's to grant, not an agent's to assume.**

With **explicit, per-task human authorisation**, an agent MAY apply the change through the API. Three obligations ride with it:

1. 🔒 **Scoped.** The authorisation covers the named change, in the named work. It does **not** carry to the next task, the next session, or a second change nobody mentioned.
2. 🔒 **Recorded.** The execution log states what changed, **from what to what**, and quotes the authorisation in the human's own words.
3. 🔒 **Read back.** Verify with a fresh read of the host's state — **never trust the exit code of the write.**

**Prefer the panel whenever the agent would have to guess an identifier** — an actor id, an app id, a role name. A wrong guess — e.g. a bypass handed to a repository-admin role instead of the CI identity — dissolves the funnel §10 gate 1 depends on.

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
9. ❌ A `docs/<id>__knowledge` branch that touches **code** (`apps/*/lib/`, `apps/*/test/`, `packages/*/lib/`, `packages/*/test/`, any app/package manifest, lockfiles). Everything else covered by `knowledge_source_of_truth_rule.md` §2 may be touched: the knowledge layer itself, **and the trio files under `{{project}}_wiki/work/` that §2 defines as a third category** (`tasks/`, `plans/`, `executions/`, and the generated `work/_index.md`). The root workspace manifest, `scripts/`, CI pipeline config, and `qa/` **are** knowledge layer and may be touched here.

10. ❌ Editing the knowledge layer on `demo_*`/`staging_*` without explicit human confirmation + justification.
11. ❌ Editing `apps/*` on `dev_packages`, or creating a `pkg/<id>__<app>` branch. `dev_packages` is packages-only.
12. ❌ A human pushing directly to `dev_<app>` (without a PR, and without being the CI bot token). The CI auto-merge has a branch-protection exception; humans stay restricted to PRs. A manual broadcast while CI is down is allowed only under a named, dated exception written into this rule (recipe: `git-runbook` §1.6.1).
13. ❌ Using a module-registered type (`bench`, `contract`) when its module is not installed (§4.2).

## 11. Cross-reference

This rule is part of the broader methodology in `.agents/METHODOLOGY.md`. On conflict between this rule and the methodology, **this rule prevails for everything Git- and branch-related**; the methodology prevails for the work cycle (task/plan/execution/wiki-sync) and the wiki. Keep a companion ADR (`{{project}}_wiki/decisions/YYYY-MM-DD_git-branching-strategy.md`) with the context and discarded alternatives.
