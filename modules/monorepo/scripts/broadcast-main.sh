#!/usr/bin/env bash
#
# scripts/broadcast-main.sh  —  TEMPLATE / STUB (adapt to your CI before use)
#
# Top-down broadcast: main → dev_<app> (+ dev_packages) via DIRECT AUTO-MERGE.
# Intended to run on your CI when something is pushed/merged into `main`.
#
# ────────────────────────────────────────────────────────────────────────────
# THIS IS A HOST-NEUTRAL TEMPLATE. It is runnable-shaped bash, but you MUST
# adapt the marked TODOs to your git host (GitHub Actions / GitLab CI / Bitbucket
# Pipelines / …) before relying on it. The load-bearing LOGIC is host-neutral;
# only the environment variables, the authenticated push URL, and the trigger
# wiring differ per host.
# ────────────────────────────────────────────────────────────────────────────
#
# Why this exists: every PR merged into `main` (knowledge via docs/__knowledge,
# an app release via staging_<app> → main, or a package release via
# tag/<pkg> → main) must propagate to the downstream long-lived branches without
# manual work. This replaces the normal use of the `/sync-knowledge` skill
# (which stays as a manual fallback).
#
# Conflict strategy: BEST-EFFORT. Abort the problematic target, continue the
# others, mark the pipeline failed, and log which target needs attention.
#
# Precondition (configure in your git host UI): the branch protection on `dev_*`
# must grant a push exception to the CI bot identity (a repository access token /
# deploy key with write scope). Humans stay restricted to PRs; only the bot
# pushes directly.

set -uo pipefail   # NOT -e: best-effort loop must continue past a failed target

# ── TODO(roster): fill with your downstream long-lived branches ───────────────
# Apps + the package trunk (dev_packages receives knowledge-layer + release tags).
# ⚠ Hardcoded roster — when onboarding a new app, update this array, APPS in
# broadcast-packages.sh, the root workspace manifest, the editor workspace file,
# and your CI pipeline config (see knowledge_source_of_truth_rule.md §9).
TARGETS=(
  # "dev_web"
  # "dev_mobile"
  # "dev_packages"
)

# ── Group A of the knowledge layer — SAFE for a blind "take main's version" ───
# on conflict, because these are docs/config with no effect on build/CI. Main is
# the canonical source of the knowledge layer, so the broadcast (top-down
# main→dev) always adopts main's side for a Group-A-only conflict, then
# regenerates the derived work index on top.
#
# Group A deliberately EXCLUDES Group B — the root workspace manifest, qa/, the
# CI pipeline config, and scripts/ — because those affect build/CI or have
# non-regenerable derivatives inside the CI runner image. A conflict touching
# ANY Group-B path ABORTS and requires a human via /sync-knowledge.
# (See knowledge_source_of_truth_rule.md §3.6.)
#
# TODO(paths): adapt to your project's actual filenames.
KNOWLEDGE_PATHS=(
  "{{project}}_wiki/"          # whole wiki: knowledge pages + work/ (trios + generated index)
  ".agents/"
  ".claude/skills/"
  # "<per-agent config>"       # e.g. .gemini/settings.json + .gemini/commands/
  ".mcp.json"
  "CLAUDE.md" "GEMINI.md" "AGENTS.md" "README.md"
  # "<workspace file>"         # e.g. the multi-root editor workspace file
)

# ── TODO(env): map these to your CI's provided variables ──────────────────────
# The SHA that triggered this run; the bot token; the workspace/repo identifiers
# used to build the authenticated push URL.
#   GitHub Actions : ${GITHUB_SHA}, ${GITHUB_TOKEN}, ${GITHUB_REPOSITORY}
#   GitLab CI      : ${CI_COMMIT_SHA}, ${CI_JOB_TOKEN}, ${CI_PROJECT_PATH}
#   Bitbucket      : ${BITBUCKET_COMMIT}, ${BITBUCKET_TOKEN}, ${BITBUCKET_WORKSPACE}/${BITBUCKET_REPO_SLUG}
SHA="${CI_COMMIT_SHA:?TODO set this to the CI trigger commit SHA}"
SHORT_SHA="${SHA:0:8}"
TOKEN="${CI_BOT_TOKEN:?TODO set this to the CI bot write token}"

# TODO(remote): build the authenticated push URL for your host.
# The generic form is a token-embedded HTTPS remote. Examples:
#   GitHub    : https://x-access-token:${TOKEN}@github.com/${REPO}.git
#   GitLab    : https://gitlab-ci-token:${TOKEN}@gitlab.com/${REPO}.git
#   Bitbucket : https://x-token-auth:${TOKEN}@bitbucket.org/${WORKSPACE}/${REPO}.git
REMOTE="${CI_PUSH_REMOTE:?TODO set this to the authenticated push URL}"

git config user.email "ci-bot@example.invalid"
git config user.name  "CI Broadcast Bot"

if [ ${#TARGETS[@]} -eq 0 ]; then
  echo "[broadcast-main] TARGETS is empty — fill the roster array first. Nothing to do."
  exit 0
fi

echo "[broadcast-main] main@${SHORT_SHA} → ${#TARGETS[@]} branch(es): ${TARGETS[*]}"

OK_TARGETS=()
FAIL_TARGETS=()

for TARGET in "${TARGETS[@]}"; do
  echo ""
  echo "[broadcast-main] === ${TARGET} ==="

  # Explicit refspec so refs/remotes/origin/<branch> is updated even in a shallow
  # CI clone (without it, fetch only updates FETCH_HEAD and origin/<branch> is
  # not resolvable → checkout fails).
  if ! git fetch --no-tags origin "+refs/heads/${TARGET}:refs/remotes/origin/${TARGET}" 2>&1 | tail -3; then
    FAIL_TARGETS+=("${TARGET}:fetch"); continue
  fi
  if ! git checkout -B "${TARGET}" "origin/${TARGET}" 2>&1 | tail -3; then
    FAIL_TARGETS+=("${TARGET}:checkout"); continue
  fi

  # Already at the target commit → skip.
  if [ "$(git rev-parse HEAD)" = "${SHA}" ]; then
    echo "[broadcast-main]   ${TARGET} already at ${SHORT_SHA}"
    OK_TARGETS+=("${TARGET}"); continue
  fi

  # Try fast-forward first (common, clean history), then a merge commit.
  if git merge --ff-only "${SHA}" 2>/dev/null; then
    echo "[broadcast-main]   fast-forward"
  elif git merge --no-ff --no-edit "${SHA}" -m "broadcast: main@${SHORT_SHA} → ${TARGET}"; then
    echo "[broadcast-main]   merge commit"
  else
    # ── Conflict. Auto-reconcile ONLY if every conflict is confined to Group A.
    # Main is canonical for the knowledge layer, so adopt main's version for the
    # conflicted Group-A files, then regenerate the derived index on top. Any
    # conflict OUTSIDE Group A (app/package code, Group-B build/CI paths) → abort.
    CONFLICTS=$(git diff --name-only --diff-filter=U)
    KNOWLEDGE_ONLY=1
    for f in ${CONFLICTS}; do
      match=0
      for p in "${KNOWLEDGE_PATHS[@]}"; do
        case "${f}" in "${p}"*) match=1; break ;; esac
      done
      [ "${match}" = "0" ] && { KNOWLEDGE_ONLY=0; break; }
    done

    if [ -n "${CONFLICTS}" ] && [ "${KNOWLEDGE_ONLY}" = "1" ] && command -v python3 >/dev/null 2>&1; then
      echo "[broadcast-main]   conflict confined to knowledge layer (Group A) — reconciling with the main version"
      # Adopt main's side. Handle delete/modify correctly: if main DELETED the
      # file (no stage-3 entry in ls-files -u), remove it; otherwise --theirs.
      # (A naive `checkout --theirs || true` would silently KEEP dev's version
      #  when main deleted the file — violating main-canonical.)
      for f in ${CONFLICTS}; do
        if git ls-files -u -- "${f}" | grep -q '^[0-7]* [0-9a-f]* 3'; then
          git checkout --theirs -- "${f}" && git add -- "${f}"
        else
          git rm -- "${f}" >/dev/null
        fi
      done
      # The work index + archive are DERIVED from trio frontmatter → regenerate
      # authoritatively rather than merging. TODO(index): point at your generator.
      if python3 .claude/skills/work-index/generate.py --root . \
         && git add {{project}}_wiki/work/_index.md {{project}}_wiki/work/archive/ \
         && [ -z "$(git diff --name-only --diff-filter=U)" ] \
         && git commit --no-edit -m "broadcast: main@${SHORT_SHA} → ${TARGET} (knowledge reconciled)"; then
        echo "[broadcast-main]   ✓ ${TARGET} knowledge reconciled"
      else
        git merge --abort 2>/dev/null || true
        FAIL_TARGETS+=("${TARGET}:conflict")
        echo "[broadcast-main]   ✗ ${TARGET} CONFLICT (reconcile failed) — resolve manually via /sync-knowledge"
        continue
      fi
    else
      git merge --abort 2>/dev/null || true
      FAIL_TARGETS+=("${TARGET}:conflict")
      echo "[broadcast-main]   ✗ ${TARGET} CONFLICT — aborted, resolve manually via /sync-knowledge"
      continue
    fi
  fi

  if git push "${REMOTE}" "${TARGET}" 2>&1 | tail -3; then
    OK_TARGETS+=("${TARGET}"); echo "[broadcast-main]   ✓ ${TARGET} updated"
  else
    FAIL_TARGETS+=("${TARGET}:push"); echo "[broadcast-main]   ✗ ${TARGET} push failed"
  fi
done

echo ""
echo "[broadcast-main] summary:"
echo "[broadcast-main]   OK   = ${OK_TARGETS[*]:-(none)}"
echo "[broadcast-main]   FAIL = ${FAIL_TARGETS[*]:-(none)}"

if [ ${#FAIL_TARGETS[@]} -gt 0 ]; then
  echo "[broadcast-main] ! Pipeline marked FAILED — ${#FAIL_TARGETS[@]} target(s) need attention"
  exit 1
fi
echo "[broadcast-main] done"
