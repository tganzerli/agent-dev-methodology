---
name: methodology-upgrade
description: Compare this project's installed methodology with a checkout of the kit, in both directions — kit changes the project lacks, and local evolutions worth sending back upstream. Uses the kit commit stamped in .agents/KIT_VERSION, de-templates placeholders heuristically, and only proposes; nothing is applied without the human. Use when the human invokes /methodology-upgrade <path-to-kit> or asks whether the methodology is up to date with the kit.
argument-hint: "<path-to-kit-checkout>"
disable-model-invocation: true
allowed-tools: Bash(python3 *), Bash(git *), Read
---

# Methodology Upgrade

**Manual and human-gated.** It reads two repositories and writes neither.

## 1. Compare

```bash
python3 .claude/skills/methodology-upgrade/compare.py --kit $ARGUMENTS --root .
```

It maps each kit file to its installed path, reads it at the **stamped** commit (`.agents/KIT_VERSION` → `kit_commit`) and at kit **HEAD**, fills the kit's placeholders from the vault slug and the stamp, and classifies: `kit-change`, `local`, `both`, `new-in-kit`, `missing` (`optional-not-installed` — modules, agents, hooks, CI, MCP, `REVIEW.md` — hidden unless `--all`). Inspect one file with `--diff <installed-path> [--against stamp|head]`.

No stamp (an install older than the stamp)? The script still compares with HEAD, but cannot tell who moved; ask the human for the approximate install date and pick the kit commit from `git -C <kit> log`, then write `.agents/KIT_VERSION` as part of the upgrade.

## 2. Read before you classify

De-templating is a heuristic: a `local` diff may be an **adaptation** the install required (a project-specific path, the knowledge language), not an evolution. Read each diff and sort it into:

- **(a) Kit changes to adopt** — `kit-change`, `new-in-kit`, and the kit half of `both`.
- **(b) Local evolutions worth upstreaming** — generic behaviour the kit lacks (a new check, a sharper rule, a fixed bug). Not project names, paths or adaptations.
- **Adaptations to keep** — say so, so the next run does not re-ask.

## 3. Propose — never apply

Report the three lists, each item with its file and a one-line reason. Then:

- **(a)** becomes ordinary work: a task and a plan in this project (`mandatory_planning_rule.md`), applied after approval, ending with `.agents/KIT_VERSION` updated to the kit commit adopted and a `methodology-update` entry in `_meta/log.md`. For `both`, merge by hand — never overwrite the local half.
- **(b)** becomes a note for the kit's maintainer: what the behaviour is, the pain that produced it (with the dated page or trio as provenance), and the project specifics to strip. Writing into the kit repo is the human's call.

## Anti-patterns

- ❌ Copying kit files over installed ones — that erases local evolutions and adaptations alike.
- ❌ Proposing a project name, path or language as an upstream change.
- ❌ Bumping `KIT_VERSION` without having adopted the changes up to that commit.
