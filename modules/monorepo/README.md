# Monorepo module

> Optional module of the agent-dev-methodology kit. Adds the machinery for a monorepo where **multiple apps and/or shared packages each live on their own long-lived branch**, with `main` as the canonical production/knowledge timeline and a CI broadcast that keeps the downstream branches in sync.

## When to install

Install this module **only** when all of the following hold:

- The repo hosts **more than one app** (`apps/<app>/`) and/or **shared packages** (`packages/<pkg>/`).
- Each app has its **own long-lived development branch** (`dev_<app>`), promoted through `staging_<app>` to `main` on independent cadences.
- Agents are allowed to **create branches** and need a rule that constrains branch names, gates, and promotion.

If the project is a single repo with one deliverable, **do not install this module.** In that shape these skills have no second branch to promote to and would be no-ops at best, confusing at worst (see "No-op in a single repo" below). This maps to install-interview answer #4 (`INSTALL.md` §4).

## What it adds

| File (post-install path) | Purpose |
|---|---|
| `.agents/rules/git_branching_rule.md` | The branch model: permanent classes (`main`, `staging_<app>`, `dev_<app>`, `demo_<app>`, optional `dev_packages`), ephemeral `<type>/<work_id>__<scope>`, the "branch only after an approved plan" gate, namespaced tags. `trigger: always_on`. |
| `.agents/rules/knowledge_source_of_truth_rule.md` | Knowledge layer canonical in `main`; promote/sync flow; the INSERT-ONLY `_index.md` invariant; the Group-A auto-reconcile vs Group-B abort concept; the roster note. `trigger: always_on`. |
| `.claude/skills/promote-knowledge/` | Promote knowledge from `dev_<app>` → `main` via an ephemeral `docs/<id>__knowledge` branch + PR. Agent-invocable with a single `yes/no` gate. |
| `.claude/skills/sync-knowledge/` | Manual fallback for the `main → dev_<app>` broadcast. `disable-model-invocation: true`. |
| `.claude/skills/distribute-packages/` | Manual fallback for the `dev_packages → dev_<app>` package broadcast. `disable-model-invocation: true`. |
| `scripts/broadcast-main.sh` | Host-neutral **stub** for the CI `main → dev_*` broadcast (auto-reconcile Group A, abort Group B). |
| `scripts/broadcast-packages.sh` | Host-neutral **stub** for the CI `dev_packages → dev_*` broadcast. |

> The two `scripts/*.sh` are **templates**, not drop-in scripts. They encode the load-bearing logic (best-effort loop, Group-A reconcile / Group-B abort, no-op gate) but need their environment variables, authenticated push URL, and trigger wiring adapted to your git host (GitHub Actions / GitLab CI / Bitbucket Pipelines / …). Every spot to change is marked `TODO(...)`. The decision to ship **described patterns + generic stubs** rather than verbatim host scripts is deliberate — the CI is the least portable part.

## Vault reorganization

The core installs a flat knowledge vault. This module reorganizes the knowledge dirs so per-app and per-package knowledge is separated, while cross-cutting knowledge stays shared:

```
{{project}}_wiki/
├── _meta/                     ← conventions, index, log (shared)
├── overview.md                ← apps × packages × domains map
├── apps/
│   └── <app>/                 ← knowledge scoped to one app (e.g. apps/web/, apps/mobile/)
│       ├── domains/  entities/  services/  flows/  pages/  contracts/
├── packages/
│   └── <pkg>/                 ← knowledge scoped to one shared package (e.g. packages/core/, packages/ui/)
│       ├── api/  internals/  contracts/
├── cross-cutting/             ← subjects that span apps/packages (shared)
├── decisions/                 ← ADRs (shared)
├── sources/                   ← external/internal source summaries (shared)
├── benchmarks/                ← evidence pages, if the benchmarks module is installed (shared)
├── postmortems/               ← thematic lessons graduated from executions, per methodology §5.6 (shared)
├── <your own>/                ← see below — this tree is NOT exhaustive
└── work/                      ← the task/plan/execution trio cycle (unchanged from core)
```

⚠ **This tree is not exhaustive, and reading it as exhaustive is the mistake to avoid.** It names the directories this module *reorganizes*; every other top-level knowledge directory **stays where it is and is left alone**. Two sources of those:

- **Other parts of this kit.** The benchmarks module creates `{{project}}_wiki/benchmarks/`, and the methodology references `postmortems/` (§5.6, §10.1). Both are listed above now, because omitting them made this module look like it contradicted the rest of the kit.
- **The project's own axis of organization.** A repo whose knowledge is organized by *layer* rather than by app — say `dart/`, `native/`, `protocols/` — keeps those directories untouched. This module separates knowledge **per app and per package**; it does not claim that app and package are the only valid axes.

**What to do with a top-level directory this tree does not name:** leave it. If it holds knowledge, add it to the knowledge-layer path list in `knowledge_source_of_truth_rule.md` §2 in the same work, so promotion and reconciliation cover it. That §2 list — not this drawing — is the authoritative one.

- Every knowledge page's `scope` frontmatter declares which `apps/*` and/or `packages/*` it covers (methodology §2 principle 5).
- A page that genuinely spans boundaries lives under `cross-cutting/`, not duplicated per app.
- `work/` is untouched — trios stay in `{{project}}_wiki/work/{tasks,plans,executions}/` and the index is generated.

The knowledge-layer path list in `knowledge_source_of_truth_rule.md` §2 already references `apps/` and `packages/` — keep the two aligned if you rename anything.

## Roster checklist — adding a new app or branch

The app/branch roster is **hardcoded in several places** and is **not** auto-reconciled by the broadcast (`scripts/` is Group B). When you onboard a new app (or otherwise change the branch topology), update **all of these in one work/promotion**, or the copies will drift between branches:

- [ ] **Root workspace manifest** — add `apps/<new>` to the workspace member list.
- [ ] **Editor workspace file** (e.g. the multi-root `*.code-workspace`) — add the new app folder.
- [ ] `scripts/broadcast-main.sh` — `TARGETS` += `dev_<new>`.
- [ ] `scripts/broadcast-packages.sh` — `APPS` += `<new>` (only if it consumes shared packages).
- [ ] **CI pipeline config** — add the new per-app parallel step/job (build/test/lint).
- [ ] `git_branching_rule.md` §3 — the permanent-branch list.
- [ ] `knowledge_source_of_truth_rule.md` §2 — the path list (if the app introduces new knowledge dirs).
- [ ] **Git host UI** — create `dev_<new>` (+ `staging_<new>`, optional `demo_<new>`); apply branch protection; grant the CI bot the push exception on `dev_<new>` (see `git_branching_rule.md` §9).
- [ ] **Bootstrap the branch** — first action on the fresh `dev_<new>`: run `/distribute-packages` to sync with the current `dev_packages` snapshot (if packages exist).

> This generalizes the real onboarding checklist that lived in the source project's rule. Because `scripts/` is not auto-reconciled by the broadcast, editing the roster on only one branch causes drift — always propagate roster changes through a normal `main` promotion.

## No-op in a single repo

`promote-knowledge`, `sync-knowledge`, and `distribute-packages` hardcode a `dev_<app>` / `dev_packages` / `main` topology and **abort outside it** (step 1 of each skill validates the current branch). In a single-repo project there is no second branch to promote to, so:

- These skills collapse to no-ops (they would abort immediately).
- The generic core skills already cover single-repo needs: `work-cycle`, `wiki-sync`, `ingest-source`, `commit`, `work-index`, `work-find`, `work-audit` all operate on trio frontmatter, not on branch topology.

That is why the module is separate and gated on install-interview answer #4. Do not install it "just in case".

## Install & register

1. Copy the files per `INSTALL.md` §4 (de-templating `{{project}}`, `{{PROJECT}}`, `{{KNOWLEDGE_LANG}}`).
2. Reorganize the vault knowledge dirs into `apps/<app>/` + `packages/<pkg>/` as above.
3. Register the three skills in `.claude/skills/_index.md`.
4. Adapt the two `scripts/*.sh` stubs to the git host chosen in interview answer #7 (fill every `TODO(...)`), and wire them as CI triggers (on push to `main`, and on push to `dev_packages`).
5. Configure branch protection + the CI bot push exception in the host UI (`git_branching_rule.md` §9).
6. Add the companion ADRs in `{{project}}_wiki/decisions/` (branching strategy; packages-trunk strategy; knowledge-reconcile scope) so the rules cite real context.

## Cross-references

- `.agents/METHODOLOGY.md` §11 — where this module sits in the overall methodology.
- `INSTALL.md` §4 — the install playbook step for this module.
- `docs/design-rationale.md` — why the monorepo skills are a separate accretion, and why to start at the mature "trunk + broadcast" form (not the retired N-PR form).
