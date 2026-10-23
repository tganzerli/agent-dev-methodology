---
name: git-runbook
description: Operational runbook for this monorepo's Git branch flow — the HOW, not the WHETHER. Use when (1) changing a shared package through the dev_packages trunk — pkg/* flow, contents of dev_packages, release to main with a SemVer tag, new-app bootstrap, the two broadcasts; (2) running a canonical Git command (create, sync, rebase staging, tag, delete a branch), including renaming a branch or worktree a tool created for the session; (3) guiding the human through a host-panel setting (branch protection, approvals, required checks, CI push exception, merge strategy, PR template); (4) reading WHY a monorepo rule says what it says (the sibling reference.md, §5-6, holds the rationale moved out of the always-on rules). Whether an operation is allowed is decided by .agents/rules/git_branching_rule.md — this skill replaces no gate.
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

The flow (the rule's §3.1, drawn):

```
pkg/<id>__<pkg>  →  dev_packages  ──(CI: direct auto-merge)──▶  dev_<app>
                          │
                          └── tag/<pkg>-vX.Y.Z__<pkg> ──▶ main ──(CI: auto-merge)──▶ dev_<app> + dev_packages
                                                              ↑
                                                        namespaced tag
```

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

#### 1.6.1. Manual broadcast while CI is unavailable — a dated, human-run exception

A human pushing to `dev_*` is forbidden (the rule's §10 gate 12). This recipe is usable **only** while the project's `git_branching_rule.md` carries a **named, dated exception** to that gate — who runs it (the human, with their own git identity; never the agent on its own initiative), what may be pushed (only the merges the broadcast scripts produce), until when (a date, or the CI's return, whichever comes first), and its provenance (the plan or decision that opened it). Without that clause in the rule, wait for CI. When the date passes, delete the clause.

The agent prepares and verifies; the **human** runs the pushes. The scripts are the repository's own — never a hand-written merge.

```bash
# 1. Throwaway clone — the script runs `checkout -B` on every target: never in your working tree
WORK=$(mktemp -d) && git clone -q <origin-url> "$WORK/repo" && cd "$WORK/repo"
git config user.name  "<human name>"
git config user.email "<human email>"

# 2. A copy of the script WITHOUT the lines that pin the CI bot identity (kept outside the clone)
grep -v '^git config user\.' scripts/broadcast-main.sh > "$WORK/broadcast-main.sh"

# 3. main -> dev_* : the script's env contract — CI_COMMIT_SHA = the tip of main,
#    CI_PUSH_REMOTE = the clone's origin (pushes with the human's credentials)
CI_COMMIT_SHA=$(git rev-parse origin/main) CI_PUSH_REMOTE=origin bash "$WORK/broadcast-main.sh"

# 4. Verify — every dev_* has all of main: 0 on every line
git fetch -q origin
for b in $(git for-each-ref --format='%(refname:strip=3)' 'refs/remotes/origin/dev_*'); do
  echo "$b $(git rev-list --count origin/$b..origin/main)"
done
```

`dev_packages -> dev_<app>` (only when a package change reached `dev_packages` with no broadcast), in the same clone:

```bash
git fetch -q origin && git checkout -q -B dev_packages origin/dev_packages
grep -v '^git config user\.' scripts/broadcast-packages.sh > "$WORK/broadcast-packages.sh"
# CI_BEFORE_SHA = the root commit, so the no-op gate sees packages/ changed and does not skip
CI_COMMIT_SHA=$(git rev-parse origin/dev_packages) \
CI_BEFORE_SHA=$(git rev-list --max-parents=0 origin/dev_packages | tail -1) \
CI_PUSH_REMOTE=origin bash "$WORK/broadcast-packages.sh"
for a in <apps from the script's APPS roster>; do
  echo "dev_$a $(git rev-list --count origin/dev_$a..origin/dev_packages)"
done
```

- **Conflict:** the script aborts that target, continues the others and exits 1; the resolution goes through a PR (`/sync-knowledge`, `/distribute-packages`), never forced.
- **Record:** the commands and their output (the `OK / FAIL / SKIP` summary and the verification counts) go into the execution that needed the broadcast.
- **Afterwards:** delete the clone (`rm -rf "$WORK"`).

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

### 3.1. A branch or worktree the tool already created

Any tool that creates a branch or worktree for the session (e.g. Claude Code worktrees, desktop agent clients) does so before the plan exists, under a name of its own. The session works on that branch — no second one.

1. **Before approval:** draft the task and plan in the wiki; commit nothing the plan gate guards. Prefer keeping the drafts uncommitted until the branch is final (step 5 may replace it).
2. **After approval:** run the creation gate (the rule's §4.5 steps 1–3) on the target name.
3. **Check the base** against the type's source line (the rule's §4.2: `dev_<app>`, `dev_packages` for `pkg/` — and for `contract/` under the shared-package variant, `reference.md` §5.3 —, `main` for `hotfix/`, `contract/`, `docs/__knowledge`). Both must hold:
   ```bash
   git fetch origin
   git merge-base --is-ancestor origin/<source-line> HEAD   # the line is in HEAD (exit 0)
   git log --oneline origin/<source-line>..HEAD             # ONLY this session's own commits (nothing, if none)
   ```
   Together they mean HEAD = the line's tip + your own commits. The first check alone is not enough: every `dev_<app>` contains `main`, so a branch cut from any `dev_<app>` would pass it for a `hotfix/`/`contract/`/`docs/__knowledge` — the second list then shows that line's unreleased commits.
4. **Base ok → rename in place** (announce it; this is an ephemeral branch, not the destructive rename of a permanent one):
   ```bash
   git branch -m <type>/<work_id>__<scope>
   ```
5. **Base wrong** (a failed first check, or any foreign commit in the list) → do not rename; create the branch from the right base, cherry-pick any task/plan drafts you committed on the tool's branch, and leave that branch for cleanup. A worktree cannot check out a line that is checked out elsewhere, so branch from the remote ref:
   ```bash
   git checkout -b <type>/<work_id>__<scope> --no-track origin/<source-line>
   git cherry-pick <draft-sha>...        # only if drafts were committed on the tool's branch
   ```
   Renaming a branch cut from the wrong line is how another app's snapshot rides into `dev_<app>` — the contamination the rule's §4.6 forbids.

### 3.2. Branch names — examples, and the scopes that need a second look

Valid (the rule's §4.3):

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

Rejected by the gate (the rule's §4.4):

```
feature/diary-schedule_mobile         ← type "feature" does not exist; single underscore ambiguous
feat/diary-schedule__mobile           ← missing work_id (no date)
feat/2026-05-16_diary__web__mobile    ← two scopes
feat/2026-05-16_diary__co             ← scope must be the full package name
web_dev / web-dev                     ← reserved (the permanent branch is dev_web)
```

**`tooling` vs `knowledge`.** Use `knowledge` for pure knowledge-layer `docs/` branches that go **straight to and from `main`**. Use `tooling` when a tooling/CI change is **developed and tested on a `dev_<app>`** (types `chore`/`refactor`/`fix`) — even when it is also knowledge layer — and then promoted to `main` with `/promote-knowledge`. Rule of thumb: branched off `dev_<app>` → `tooling`; branched off `main` → `knowledge`.

**Contract surfaces** (`contract/` only — `public-api`, `shared-packages`, `wire-protocol`, …): the change lands in every consumer at once, so one app or package name would misdescribe the diff.

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

## 5–6. Why the rules say what they say → [`reference.md`](reference.md)

The rationale and provenance moved out of the always-on rules live in the sibling `reference.md` (same numbering), read only when a rule points there:

- §5 Why the branching rule says what it says
  - §5.1 Genesis commit and bootstrap without `dev_<app>`
  - §5.2 No direct commit into `dev_<app>`
  - §5.3 Why `contract/` goes straight to `main`
  - §5.4 Branch scope barrier — how it is checked, and why
  - §5.5 Why tags are manual
  - §5.6 Required checks that never fire
  - §5.7 Host configuration: why "authorisation" and not "never"
  - §5.8 Why gate 9 allows trio files on `docs/__knowledge`
- §6 Why the knowledge source-of-truth rule says what it says
  - §6.1 The §2 path list
  - §6.2 Reconcile groups and `merge=union`
  - §6.3 Why the path list has a checker
