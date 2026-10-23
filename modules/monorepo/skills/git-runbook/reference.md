# Git runbook — reference (the why)

> Companion of `SKILL.md` in this directory: the rationale and provenance behind `.agents/rules/git_branching_rule.md` (§5) and `knowledge_source_of_truth_rule.md` (§6), kept out of the skill body so the recipes stay small. No gate lives here; every obligation is in the rules.

## 5. Why the branching rule says what it says

Rationale and provenance moved out of the always-on `git_branching_rule.md`; the rule keeps every obligation and points here.

### 5.1. Genesis commit and bootstrap without `dev_<app>`

**Genesis commit.** The very first commit of a repository lands on `main` directly even without §1.1: `main` does not exist before it, and no PR can target a branch with no commits. Record it in `_meta/log.md` as an ordering exception, not a precedent — that circumstance does not repeat.

**Bootstrap without `dev_<app>`.** `/promote-knowledge`, `/sync-knowledge` and `/distribute-packages` abort outside a `dev_<app>` by design, so before the first one exists they never run — one installation did seven promotions by hand during bootstrap, and its path-list copies drifted unnoticed because nothing executed them. Until then, knowledge lands per `knowledge_source_of_truth_rule.md` §3.5 (a `docs/<id>__knowledge` branch off `main`, or directly on `main` under §1.1), and `scripts/check-knowledge-paths.py` runs in CI rather than inside the skills.

**Why not a local `docs/…` branch merged with `--no-ff` during the transition:** with no remote and no reviewer it keeps the rule's form without its gate, and the history then claims a review that never happened.

### 5.2. No direct commit into `dev_<app>`

An earlier version of the rule (§3 table and §3.2) allowed "a direct commit from an approved plan" into `dev_<app>`, while §10 gate 12 forbade any human push to `dev_<app>`: two sections authorised what a third banned. An installation found it by walking into it — an agent committed a work log straight to a `dev_<app>`, then checked and got both answers; the missing host-side protection let it pass in silence instead of failing. Resolved toward the stricter reading: **one flow, always a PR.** An approved plan authorises the work, never the push path.

### 5.3. Why `contract/` goes straight to `main`

`main` is the only branch where every app and every package coexist, so it is the only place a simultaneous change across all consumers can be expressed. `dev_packages` refuses `apps/*` (§10 gate 11) and each `dev_<app>` covers one app: a PR into either leaves the other consumers speaking the old shape until the broadcast arrives. The accepted cost is that a contract change reaches `main` without passing `staging_<app>`. The trade is asymmetric — diverging package copies between apps are recoverable (the broadcast exists for that), a consumer speaking the old shape at runtime is a production break.

**Variant: the contract is a shared package — `contract/` off and into `dev_packages`.** When the versioned contract is itself a package (`packages/<contract>`: generated types, a schema package, an API client), a project may route it like any package change:

1. `contract/<id>__<pkg>` branches off `dev_packages`; its single PR targets `dev_packages`. It carries what `contract_change_rule.md` requires (ADR, the package's version bump + CHANGELOG) — but **no `apps/*`** (`dev_packages` refuses them, §10 gate 11).
2. Each consuming app follows on its own `feat/<id>__<app>` branch off `dev_<app>`, after the broadcast (`broadcast-packages.sh`) has brought the new contract version — or, before it, by merging the contract branch to build against it (the scope barrier reports that merge; record it in the execution).
3. The contract reaches `main` through the normal `tag/<pkg>-vX.Y.Z__<pkg>` release, the apps through `staging_<app>`.

The cost the default route avoids — consumers on the old shape until each app's own branch lands — is accepted here because **no app reaches `main` without its own release through `staging_<app>`**, which pins the contract version it was built against. Choose the variant only when that holds. The project's rule must name it in place of the `contract` row (rule §4.2), and the barrier must be told: `SCOPE_CONTRACT_LINE=dev_packages` makes `scripts/check_branch_scope.sh` expect `dev_packages` as the source and forbid `apps/*` on `contract/` branches.

### 5.4. Branch scope barrier — how it is checked, and why

**How it is checked.** `scripts/check_branch_scope.sh`, on every PR and on push to `dev_<app>`. The roster comes from the root workspace manifest (a placeholder to fill at install), so a new app enters the barrier on its own. The baseline is the **cut point of the source branch**, not the tip of `main`: an ephemeral legitimately carries what its `dev_<app>` has ahead of `main`. The source is **detected** (among the permanent branches, the one with the most recent merge-base by DAG ancestry), which also makes rule 1 checkable.

**Advisory first.** The script ships reporting and exiting 0 (`SCOPE_BARRIER_BLOCKING=1` makes it block). Flip the default only after it has run clean across real releases; the installation it came from never flipped it. And a check on push **reports**, it does not prevent — the commit is already there; hard prevention is branch protection requiring PRs on `dev_*` (§9).

> **Why it exists.** In the installation it came from, three incidents in one day had this cause: an app's change leaked into every `dev_*` through `apps/` on `dev_packages`; a release PR carried 254 files to `main` instead of 8, 189 of them another app; and a `dev_<app>` carried a stale copy of another app with code already removed from the store. Nobody edited the wrong app on purpose — every case was a **snapshot carried by a merge**. The rule already forbade it in text; it lacked enforcement.

### 5.5. Why tags are manual

While the rule said a tag "is cut on merge", agents assumed it appeared on its own and never cut it; one installation also found a release tag on the wrong commit. The manifest bump is manual for the same reason; an auto-bump CI step is a possible follow-up, and once it exists the rule must say so.

### 5.6. Required checks that never fire

One installation armed `staging_*` with protection but deliberately without the required checks, because its CI ran on PRs into `main` and `dev_*` only; adding the checks belongs to the work that extends CI to that branch. Protection that blocks a legitimate merge becomes the reason someone turns protection off.

### 5.7. Host configuration: why "authorisation" and not "never"

**Why this section says "authorisation" instead of "never".** It said "never" until 2026-09-11. In the project this kit came from, the human authorised **three** exceptions to it **on one day** — creating the permanent-branch ruleset, then a repository setting plus a second ruleset, then a CI bypass actor. Each was legitimate, each was scoped in the human's own words, and **not one violated what the section actually protects**: the owner granted, the agent did not assume.

The second of those carried a written trigger — *"if a third arrives, stop writing notes and rewrite this section"* — on the reasoning that a policy suspended every time it binds is not a policy but a ritual with a waiver attached. The third arrived the same day.

This rewrite is deliberately **not** a loosening. The control that was actually in force all three times is now what the text says, plus two obligations (record, read back) that used to be habit and are now required. The failure it avoids is the one catalogued in the kit's own lesson on unexecuted copies: a clause that everybody waives becomes a clause nobody reads.

**Why the panel when an identifier would be guessed.** An actor id, an app id or a role name typed from memory is the likeliest wrong write: a bypass handed to a repository-admin role instead of the CI identity looks like success and dissolves the funnel the rule's §10 gate 1 depends on.

### 5.8. Why gate 9 allows trio files on `docs/__knowledge`

An earlier version demanded the diff be "100% inside the knowledge layer". That contradicted §3.2 of this rule, which asks only that the diff *"must not touch `apps/*/lib/`, `packages/*/lib/`, or any other code path"* — and, worse, forbade what this rule's own procedure produces: `/promote-knowledge --trio <id>` (`knowledge_source_of_truth_rule.md` §3.4) promotes a closed trio by creating exactly a `docs/<id>__knowledge` branch carrying trio files. §2 of that rule lists **three** categories, not two, and trio files are the middle one. Found in use by an installation on 2026-09-07; the fix restricts nothing that §3.2 did not already allow.

## 6. Why the knowledge source-of-truth rule says what it says

Rationale moved out of the always-on `knowledge_source_of_truth_rule.md`.

### 6.1. The §2 path list

`benchmarks/` comes with the benchmarks module and `postmortems/` is referenced by `METHODOLOGY.md` §5.6 and §10.1 — both are listed so an install does not have to rediscover them. A line marked `— DECLARED, not yet created` is a target: a mask does not match a directory that does not exist, so declaring it early costs nothing; every unmarked line must match a tracked file.

### 6.2. Reconcile groups and `merge=union`

`{{project}}_wiki/` enters `KNOWLEDGE_PATHS` whole, so the broadcast also reconciles `work/` (closed trios and the generated index), for which `main` is canonical too: §2 defines what is **promoted**, Group A what is safe to **reconcile**.

- **`docker/`** (dev-env module) is Group B because `dev_environment_rule.md` governs services that stay **up** on the developer's machine: silently adopting main's version swaps a port, volume or image under a running environment. Changes there are rare, so aborting is cheap and guessing is not.
- **`.gitattributes`** is knowledge layer but deliberately **not** Group A. Git reads merge attributes from the **ours** side (the `dev_<app>`), and a `--theirs` resolution happens **after** `git merge` has already merged everything else with the *old* file — a new directive arriving from `main` does not apply retroactively to the current merge. Putting it in Group A would give false protection. It takes effect from the merge **after** the one that brings it.
- **`scripts/`** in Group B has the consequence §9 records: the roster is **not** auto-reconciled and drifts between branches if edited on one side only.

> **Exception: append-only files.** "Adopt main's version" is right for a **page**, whose canonical
> content lives in `main`. It is **wrong** for a **ledger**, where the `dev_<app>` legitimately holds
> lines `main` has not seen yet — the ones written between `/wiki-sync` and `/promote-knowledge`. In
> that window the `dev_<app>` is the **only** place that content exists, and adopting `main` is
> **data loss**, not reconciliation: pipeline green, `git status` clean, no warning.
>
> This applies to **`{{project}}_wiki/_meta/log.md`**, declared in the root `.gitattributes`:
>
> ```
> {{project}}_wiki/_meta/log.md merge=union
> ```
>
> With `union` the conflict stops existing — git keeps both sides, for every merge (broadcast,
> `/sync-knowledge`, promote, manual), and the auto-resolve block is never reached.
>
> **Do not extend `union` to `_meta/index.md` or other catalogs**: their existing lines are
> **edited**, not only appended, and `union` over a line changed on both sides keeps **both**
> versions — a count `10 → 11` on dev and `10 → 12` on main becomes two contradictory lines. That
> trades silent loss for silent corruption, which is worse because absence does not reveal it.
> `{{project}}_wiki/work/_index.md` and `work/archive/*` stay out for another reason: they are
> regenerated right after reconciliation, so a clobber there is harmless by construction.
>
> **Refuted: "`union` is not idempotent / duplicates log entries".** Measured in a synthetic repo
> by the installation that first adopted it: an **identical** append on both sides is recognised as
> the same change and not duplicated; a dev append plus other appends on main resolves cleanly. The
> one repetition found in its real log (238 entries) came from two **different** commits with
> different bodies — two legitimate syncs whose header (`[date] wiki-sync | work_id | N pages`) did
> not disambiguate. Do not replace `union` on that assumption: the loss it prevents is measured, the
> duplication feared from it is not. `scripts/check_log_entry_collisions.py` reports repeated
> headers, so if merge duplication ever happens it shows up there.

### 6.3. Why the path list has a checker

**Do not trust this checklist alone.** `python3 scripts/check-knowledge-paths.py` verifies the four copies: the two skill masks equal §2; §2 is partitioned by Groups A and B with no overlap and no leftover; no Group B path leaks into `KNOWLEDGE_PATHS` and every Group A path is there; and every §2 path matches at least one tracked file unless marked `— DECLARED, not yet created`. Both skills run it at step 1 and abort if it fails; wire it into CI too, since the skills do not run until a `dev_<app>` exists.

> **Why this exists.** An installation found `{{project}}_wiki/benchmarks/` missing from §2 — a
> directory the kit itself creates. Both skill masks had the same hole, plus four install placeholders
> never filled in and three paths that did not exist in that repository. Nobody had decided to ignore
> them: **neither skill had ever run there**, because both abort outside `dev_<app>` and no `dev_*`
> existed yet. A copy nobody executes does not warn that it is wrong — so the checklist got a checker.
