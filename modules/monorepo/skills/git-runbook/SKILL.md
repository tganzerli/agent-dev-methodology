---
name: git-runbook
description: Operational runbook for this monorepo's Git branch flow — the HOW, not the WHETHER. Use when (1) changing a shared package through the dev_packages trunk — pkg/* flow, contents of dev_packages, release to main with a SemVer tag, new-app bootstrap, the two broadcasts; (2) running a canonical Git command (create, sync, rebase staging, tag, delete a branch); (3) guiding the human through a host-panel setting (branch protection, approvals, required checks, CI push exception, merge strategy, PR template). Whether an operation is allowed is decided by .agents/rules/git_branching_rule.md — this skill replaces no gate.
---

# Git runbook

> **Recipe, not rule.** Obligations and prohibitions live in `.agents/rules/git_branching_rule.md`
> (`trigger: always_on`, always loaded). This file is the step by step, and it lives in a skill
> because a skill's body enters context **only when invoked** — which takes the recipes out of every
> session's prefix without moving any gate (METHODOLOGY §6.6).
>
> ⚠ If you came here to find out **whether** you may do something, you are in the wrong file — go
> back to the rule.
>
> **This file carries no gate (lock) marker, on purpose.** Every gate these recipes touch is stated in the
> rule. Here they appear as explanation of the flow, not as obligation; a lock here would suggest the
> obligation lives in a skill that may never be invoked.

## 1. Package trunk (`dev_packages`)

Changes to `packages/<pkg>` live on the permanent `dev_packages` trunk. Apps consume them through the automatic CI broadcast or the manual `/distribute-packages` skill.

> **History.** The trunk model replaced an earlier "N twin all-or-nothing PRs" model. A fresh install starts at the mature trunk + broadcast form.

### 1.1. Change flow

1. **Ephemeral branch** `pkg/<work_id>__<pkg>` off `dev_packages`.
2. **Implementation + single PR** `pkg/<id>__<pkg> → dev_packages`. The human review happens once, here.
3. **After the merge, top-down broadcast via CI (direct auto-merge):**
   - **Automatic:** `scripts/broadcast-packages.sh` fires on push to `dev_packages`. For each consuming `dev_<app>` it runs `git merge --no-ff` + `git push` — no intermediate PRs.
   - **No-op gate:** if the pushed range changed nothing under `packages/` (e.g. a fast-forward of `main`), CI skips the broadcast rather than create purposeless merge commits.
   - **Best-effort conflict:** a conflicting `dev_<app>` is aborted, the others continue, and the pipeline is marked failed with the list. A roster branch that does not exist yet is skipped and named; if nothing propagated, the pipeline fails.
4. **Manual fallback (`/distribute-packages`):** pull ahead of CI, resolve a post-abort conflict, or bootstrap a new app.

### 1.2. Contents of `dev_packages`

`packages/<pkg>/…`, shared tooling (root workspace manifest, …), and the knowledge layer (present on every branch). **No `apps/*`** — removed on the initial commit; apps live only on `dev_<app>`.

### 1.3. Release to `main` (tagged)

1. Ephemeral branch `tag/<pkg>-vX.Y.Z__<pkg>` off `dev_packages`.
2. Bump the package manifest + `packages/<pkg>/CHANGELOG.md`.
3. PR → `main`. The reviewer checks CHANGELOG, breaking changes, version.
4. After the merge, **cut the tag by hand** on the merge commit (§3 below). CI creates none.

Bump only the packages that changed since their last tag; an unchanged package's version already describes it.

### 1.4. New app (bootstrap)

`dev_<newapp>` is born off `main`; its first action is `/distribute-packages`, to start in sync with the current `dev_packages` snapshot instead of accumulating debt. Then follow the roster checklist (`knowledge_source_of_truth_rule.md` §9).

### 1.5. PR conventions

- **`pkg/<id>__<pkg> → dev_packages`:** title `[pkg] <short description> (work_id: <id>)`. Body links the task + scope. The only PR in the flow.
- **`tag/<pkg>-vX.Y.Z__<pkg> → main`:** title `[tag] <pkg>-vX.Y.Z`. Body: the CHANGELOG + the `pkg/` PRs since the previous tag.
- Every ephemeral PR also carries what the rule's §6 requires (validations recorded, review closed, Testing / Risk / How to revert).

### 1.6. Broadcast `main → dev_<app>` + `dev_packages`

- **Trigger:** push to `main` (any merge — `staging_<app>`, `tag/<pkg>`, `docs/__knowledge`, `contract/`).
- **Script:** `scripts/broadcast-main.sh` fast-forwards when possible, merges otherwise. A conflict confined to Group A of the knowledge layer adopts `main`'s version and regenerates the work index; anything else aborts that target (`knowledge_source_of_truth_rule.md` §3.6). `_meta/log.md` never conflicts — `merge=union`.
- **Best-effort:** same pattern as §1.1.
- **Manual fallback:** `/sync-knowledge`.
- **Tests:** `scripts/test-broadcast-main.sh` and `scripts/test-broadcast-packages.sh` run both scripts against a throwaway bare remote, including the production push path. Run them after any edit to a broadcast script.

### 1.7. CI identity

`dev_*` carries branch protection with a push exception for the CI identity only. Prefer a **write-scoped deploy key** (private half as a CI secret, the workflow pushing over SSH): no human inherits it. On GitHub, a push made with `GITHUB_TOKEN` does not trigger other workflows, and on a user-owned repository the GitHub Actions app cannot be a ruleset bypass actor (the API answers 422). A reference workflow lives in the kit at `modules/monorepo/ci-examples/github-broadcast.yml`.

## 2. Hotfix commands

```bash
git checkout main && git pull
git checkout -b hotfix/<work_id>__<app>
# fix, commit, PR to staging_<app>; after validation PR staging_<app> → main;
# then merge main back into dev_<app> (the rule's §5).
```

## 3. Canonical Git commands

```bash
# Create an ephemeral branch
git checkout dev_<app>            # or: main (hotfix, contract/, docs/__knowledge)
git pull
git checkout -b <type>/<work_id>__<scope>

# Sync an ephemeral branch with its dev_<app>
git checkout <type>/<work_id>__<scope>
git fetch origin
git rebase origin/dev_<app>

# Mandatory rebase of staging onto main (before the PR to main)
git checkout staging_<app>
git fetch origin
git rebase origin/main
git push --force-with-lease origin staging_<app>   # --force-with-lease, never --force; ask [y/n] first

# Namespaced tag — by hand, on the MERGE COMMIT on main, not on your local HEAD
git fetch origin main
git log --oneline -1 <merge_commit>               # confirm the target first
git tag <app>-vX.Y.Z <merge_commit>
git push origin <app>-vX.Y.Z

# Delete an ephemeral branch after merge
git push origin --delete <type>/<work_id>__<scope>
git branch -d <type>/<work_id>__<scope>            # -D (unmerged) is destructive: ask [y/n]
```

A local `dev_<app>` that stays "ahead" after its content was promoted and broadcast back is reset with `/reset-dev-branch`, never with a hand-typed `reset --hard`.

## 4. Host panel settings

The agent guides the human; it changes host configuration only with explicit, per-task authorisation (the rule's §9.1). Name the concept and let the human find it in their host — GitHub → Settings → Rules → Rulesets (or Settings → Branches); GitLab → Settings → Repository → Protected branches; Bitbucket → Repository settings → Branch permissions.

| Situation | Concept to configure in the host |
|---|---|
| Protect permanent branches (`main`, `staging_*`, `dev_*`, `demo_*`) | Branch protection / restriction |
| Force PR review before merge | Require N minimum approvals (0 on a solo repo: a host may forbid approving your own PR) |
| Force CI green before merge | Require successful builds/checks — only on branches where CI actually fires |
| Let the CI push to `dev_*` | Branch-protection exception for the CI identity (deploy key preferred) |
| PR template | The host's PR-template file, committed to `main` |
| Merge strategy (squash/merge/rebase) | Merge settings / merge checks |
| Block force-push on permanent branches | Prevent history rewriting |
| Delete ephemeral branches after merge | Auto-delete head branches |

When guiding the human, describe the path for their specific host and the expected result; afterwards, read the state back rather than trusting the write.
