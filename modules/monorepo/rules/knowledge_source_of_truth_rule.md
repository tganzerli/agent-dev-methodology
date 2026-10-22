---
trigger: always_on
---

# Knowledge Source-of-Truth Rule (monorepo module)

> Installed only alongside `git_branching_rule.md` in a multi-app/multi-package monorepo with per-app branches. It governs where the **knowledge layer** is canonical and how it flows between branches.

## 1. Core directive

**STOP.** Before editing any **knowledge-layer** file (defined in §2), understand that `main` is the **canonical timeline**. `dev_<app>` branches author locally but converge to `main` via `/promote-knowledge`. `demo_<app>` and `staging_<app>` stay **outside** the automatic flow.

This rule is **non-negotiable** and complements `mandatory_planning_rule.md` (planning layer) and `git_branching_rule.md` (Git layer).

## 2. Knowledge layer — covered paths

These paths make up the canonical knowledge layer (versioned, kept aligned across `main` and every `dev_<app>`). One path per line (a line may group files with commas); after `#`, a comment that starts with the path's **reconcile group** (§3.6): `[A]` or `[B]`. At install, replace each `<placeholder>`, delete lines that do not apply, and mark a path declared but not yet created with `— DECLARED, not yet created` (every unmarked path must match a tracked file — §9.1):

```
.agents/                              # [A] methodology + rules + per-LLM specifics + mcp.md
.claude/skills/                       # [A] Agent Skills (gitignored: local settings, projects/, todos/)
.claude/agents/                       # [A] role sub-agents
.claude/hooks/                        # [A] agent hooks
.claude/settings.json                 # [A] shared agent settings (settings.local.json is gitignored)
<per-agent-config>                    # [A] e.g. .gemini/settings.json + .gemini/commands/
.mcp.json                             # [A] MCP server registry (if any)
<workspace-file>                      # [A] e.g. the multi-root editor workspace file
CLAUDE.md, GEMINI.md, AGENTS.md, README.md   # [A] entry-points
<root-manifest>                       # [B] the ROOT dependency/workspace manifest only — app/package manifests are OUT
scripts/                              # [B] shared CI tooling — must stay aligned across branches
<ci-config>                           # [B] e.g. .github/workflows/, .gitlab-ci.yml
qa/                                   # [B] shared QA pipeline (if any)
.gitattributes                        # [B] merge attributes (log.md merge=union — §3.6)
# docker/                             # [B] uncomment when the dev-env module is installed
{{project}}_wiki/_meta/               # [A] conventions, index, log
{{project}}_wiki/apps/                # [A] per-app knowledge
{{project}}_wiki/packages/            # [A] per-package knowledge
{{project}}_wiki/cross-cutting/       # [A] cross-cutting knowledge
{{project}}_wiki/decisions/           # [A] ADRs
{{project}}_wiki/sources/             # [A] external/internal source summaries
{{project}}_wiki/benchmarks/          # [A] evidence pages — benchmarks module (kit-created)
{{project}}_wiki/postmortems/         # [A] lessons graduated from executions (METHODOLOGY §5.6, kit-created)
{{project}}_wiki/overview.md          # [A] apps × packages × domains map
{{project}}_wiki/.obsidian/           # [A] shared vault config (gitignored: workspace*.json)
```

A project organized on another axis adds its own top-level knowledge directories here (module README, "Vault reorganization").

**Outside the knowledge layer (per-branch during the trio; promoted on close):**
- `{{project}}_wiki/work/tasks/`, `plans/`, `executions/` — born on the work branch.
- `{{project}}_wiki/work/_index.md` — updated in `main` when a trio closes (generated, not hand-edited).
- `{{project}}_wiki/work/relay/` — cross-repository coordination **messages**, if the `peer-relay`
  module is installed. **Outside by decision, not by omission:** a delivered message exists in *both*
  repositories and is never rewritten, so it cannot be reconciled by a broadcast. This is what the
  `relay` branch scope in `git_branching_rule.md` §4 rests on — today it argues from the *absence* of
  this line, which survives only until someone adds the path "for completeness".

  > ⚠ **The reason covers messages; the path covers more than messages.** Two files in this directory
  > are not messages, and neither inherits the argument above.
  >
  > `_board.md` is not delivered, does not exist in both repositories, and **is** rewritten every
  > time — three of three attributes fail. It still belongs outside the layer, but on its own
  > argument: it is durable coordination state, versioned with the trio, and reaches this line when
  > the work lands.
  >
  > `_locks.md` is **live state** and the line above actively harms it: a scope lock must be readable
  > from another working tree *while it exists*, and per-branch versioning guarantees that writer and
  > reader sit in different trees during exactly that window. Measured in one installation at 17.0 h
  > of lock life and zero visibility. It needs a publication route that does not wait for the work to
  > land, and §3.2 of `git_branching_rule.md` forbids the obvious one without exception — so the
  > route is a deliberate choice, not a default. See `modules/intra-team/README.md` §4.

**Outside this rule (code, always per-branch):**
- `apps/*/lib/`, `apps/*/test/`, `apps/*/android/`, `apps/*/ios/`, etc.
- `packages/*/lib/`, `packages/*/test/`, etc.
- App/package manifests and lockfiles at any level (versioned per-app/per-package).

## 3. Workflow

### 3.1. Authoring on `dev_<app>`
Permitted and encouraged. Edit the knowledge layer alongside code in the same commit or trio.

### 3.2. Promotion to `main`
After a commit on `dev_<app>` that touches the knowledge layer, **invoke** `/promote-knowledge`. The skill (`.claude/skills/promote-knowledge/SKILL.md`):

1. Detects the knowledge-layer files to promote. **Default = scoped to the `work_id`** — only the files touched by that work's trio commits (avoids over-reaching the whole branch divergence, which may hold several works). Opt-in `--all` promotes the entire divergence vs `main` (legacy). Ideal isolation is one ephemeral branch per work; the scoping covers direct authoring on `dev_<app>`.
2. Creates ephemeral branch `docs/<work_id>__knowledge` off `main`.
3. Copies only those files onto the new branch.
4. Pushes to `origin`.
5. Instructs the human to open the PR `docs/<id>__knowledge → main` in the git host.

**Single human gate:** one prior permission (`yes/no`) before any branch/push. Once granted, the agent runs the rest autonomously (the skill is **agent-invocable**). Merging the PR remains a separate human action in the host.

> **Critical invariant — `_index.md` promotion is INSERT-ONLY.** `{{project}}_wiki/work/_index.md` is edited by trios from **all** apps. NEVER copy the whole file between branches (`git checkout SRC -- _index.md`): under **multi-agent** work (one agent on `dev_web`, another on `dev_mobile`…), the source branch lags the other's `_index`, and a whole-file copy **erases** the entries the other just promoted. Promotion must **add only the `work_id`'s entry** to `main`'s current `_index` and validate the diff vs `origin/main` is **additions-only** (any deletion aborts). Because the index is **generated** (see the work-index skill), the modern skill regenerates it from frontmatter on the branch cut from `main` — clobber is impossible by construction. See the skill's steps 6b/7.

### 3.3. Synchronizing `main → dev_<app>`
Periodically, or when you suspect divergence, **invoke** `/sync-knowledge`. The skill:

1. Compares the current branch's knowledge layer vs `origin/main`.
2. Applies main's diff onto the current branch, without touching `apps/`, `packages/`, `{{project}}_wiki/work/`.
3. Local commit. Optional push.

**Does NOT work** on `demo_*`, `staging_*`, or `main` directly.

### 3.4. Task/plan/execution trios
- Trios are **born on `dev_<app>` or `demo_<app>`** during the work.
- When a trio **closes** (`task: done` + `plan: executed` + `execution: done`), the 3 files may be promoted to `main` via `/promote-knowledge --trio <id>`.
- `open`/`draft`/`in_progress` trios **do not** promote — they are still being edited.
- **Do not stage trio files in ephemeral-branch commits that travel via broadcast** (`pkg/<id>__<pkg>` → `dev_packages` → broadcast to `dev_<app>`; `tag/*`). Those commits carry **code only**. The trio lives on its origin `dev_<app>` and is promoted via `/promote-knowledge --trio <id>` on close. **Why:** staging the trio in a `pkg/` commit makes the broadcast distribute an *intermediate* version of the trio to every `dev_<app>`; when a later `/wiki-sync` rewrites the trio and that version is promoted to `main`, the `main → dev_<app>` broadcast finds divergent versions of the same file and conflicts.

### 3.5. `main`-only changes (rare)
When a knowledge-layer change goes **only** to main (no origin branch), create ephemeral `docs/<work_id>__knowledge` straight off main, change it there, PR to main. Typical: a typo fix in an old ADR, a standalone `_meta/index.md` update.

### 3.6. Broadcast auto-reconcile (main → dev)
§2 tags every path with exactly one group, and the `main → dev_<app>` broadcast (CI, `scripts/broadcast-main.sh`) consumes that partition:

- **Group A — reconciles on its own**, adopting **main's** version (canonical) and regenerating the derived index. Docs and agent configuration. It is `KNOWLEDGE_PATHS` in the script, where `{{project}}_wiki/` enters whole (so `work/` is covered too).
- **Group B — aborts and calls a human** via `/sync-knowledge`: build, CI, the running dev environment (`docker/`), and `.gitattributes` (git reads merge attributes from the `dev_<app>` side, so adopting main's copy mid-merge protects nothing). `scripts/` in B means the roster is not auto-reconciled (§9).

> 🔒 **Exception: append-only files.** Adopting main's version of a **ledger** is data loss: the `dev_<app>` holds lines written between `/wiki-sync` and `/promote-knowledge` that exist nowhere else. The root `.gitattributes` declares `{{project}}_wiki/_meta/log.md merge=union`, so that conflict never happens.
>
> ⛔ `union` is for `_meta/log.md` **only** — never `_meta/index.md`, other catalogs or `work/_index.md`: union keeps both versions of a line edited on both sides. Do not replace it with another strategy. Why, and the refuted "union duplicates entries" claim: `git-runbook` §6.2.

`scripts/check-knowledge-paths.py` verifies the partition and that no Group B path leaks into `KNOWLEDGE_PATHS` (§9.1). Keep a companion ADR (`{{project}}_wiki/decisions/YYYY-MM-DD_knowledge-reconcile-scope.md`).

## 4. Exceptions

### 4.1. `demo_<app>` (terminal)
- **No automatic `/sync-knowledge`** — demo is frozen by design.
- Receives knowledge layer **manually** only: a specific cherry-pick if needed (with explicit justification).

### 4.2. `staging_<app>` (release candidate)
- **No auto-sync.** Receives the knowledge layer via normal release promotion: `dev_<app>` is rebased onto main (knowledge included), then PR `dev → staging`. The knowledge layer rides along.
- Convention: do not edit the knowledge layer directly in staging — use `dev_<app>` or `docs/__knowledge`.

### 4.3. `main`
- **Not edited directly.** Changes enter via a `docs/<id>__knowledge` PR (or via normal `staging → main` promotion). Direct commit stays forbidden (`git_branching_rule.md` §3.2).

## 5. LLM gates (explicit prohibitions)

1. ❌ Editing the knowledge layer on `demo_*`/`staging_*` without explicit human confirmation + justification.
2. ❌ Pushing `dev_<app>` with knowledge-layer changes without running `/promote-knowledge` afterward — leads to fragmentation.
3. ❌ Creating a `docs/<id>__knowledge` branch that touches code (`apps/*/lib/`, `packages/*/lib/`, etc.). Knowledge-only.
4. ❌ Running `/sync-knowledge` on `demo_*`/`staging_*`/`main` — the skill must abort.
5. ❌ Promoting an `open`/`draft`/`in_progress` trio to main via `/promote-knowledge --trio` — still being written.
6. ❌ Treating `{{project}}_wiki/work/_index.md` as per-branch — its version in `main` is the canonical catalog of closed trios; its `dev_<app>` version reflects in-flight work.

## 6. Expected conflict

When `dev_<app>` has knowledge-layer edits **simultaneous** with what main received from another `dev_<app>`, a rebase may conflict. Resolve manually following the chronological order of `_meta/log.md` where applicable; otherwise the human decides.

## 7. Cross-references

- `.agents/METHODOLOGY.md` §11 — conceptual overview.
- `.agents/rules/git_branching_rule.md` §4 — the allowed `__knowledge` scope.
- `.claude/skills/promote-knowledge/SKILL.md` — promotion implementation.
- `.claude/skills/sync-knowledge/SKILL.md` — sync implementation.
- `.claude/skills/wiki-sync/SKILL.md` — suggests `/promote-knowledge` at the end.
- `{{project}}_wiki/_meta/conventions.md` — source-of-truth discipline.

## 8. On conflict between rules

On conflict between this rule and the methodology, **this rule prevails** for everything about the knowledge layer. On conflict with `git_branching_rule.md`, both apply in different layers — this one governs *what* may enter each branch (knowledge); the other governs *how* branches relate (promotion, gates). When ambiguous, ask the human.

## 9. New-app onboarding — roster checklist

The app/branch roster is **hardcoded in several places** and is **not** auto-reconciled by the broadcast (`scripts/` is Group B — §3.6). When adding a new app (e.g. `mobile`), update **in sync** (in one work/promotion):

- [ ] **Root workspace manifest** — add `apps/<new>` to the workspace member list.
- [ ] **Editor workspace file** — add the new app folder.
- [ ] `scripts/broadcast-main.sh` — `TARGETS` += `dev_<new>`.
- [ ] `scripts/broadcast-packages.sh` — `APPS` += `<new>` (if it consumes packages).
- [ ] **CI pipeline config** — add the new per-app parallel step/job.
- [ ] The permanent-branch list in §3 of `git_branching_rule.md`.
- [ ] The path list in §2 of this rule (if the new app introduces new knowledge dirs) — and its three copies (§9.1).

> Because `scripts/` is not auto-reconciled, these copies **drift between branches** if edited on only one. Keep them aligned via normal promotion. Deriving the roster automatically from the root workspace manifest is a possible future improvement (not implemented).

### 9.1. The §2 path list has four copies

Changed §2? Update **all four in the same work** — none is derived from the others:

- [ ] §2 of this rule — **the authoritative one**, and the only one that carries each path's expected state.
- [ ] `.claude/skills/promote-knowledge/SKILL.md` — `KL_PATHS`. Equality required.
- [ ] `.claude/skills/sync-knowledge/SKILL.md` — `KL_PATHS`. Equality required.
- [ ] `scripts/broadcast-main.sh` — `KNOWLEDGE_PATHS`, which must cover every `[A]` path of §2 (the whole `{{project}}_wiki/` counts) and **nothing** tagged `[B]`.

**Do not trust this checklist alone:** run `python3 scripts/check-knowledge-paths.py` — both skills run it at step 1 and abort on failure; wire it into CI too, since the skills do not run until a `dev_<app>` exists. Why it exists: `git-runbook` §6.3.
