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
# Test: scripts/test-broadcast-main.sh runs this script against a throwaway bare
# remote, through both the BROADCAST_REMOTE seam and the production push path.
# A reference GitHub Actions wiring lives in the kit at
# modules/monorepo/ci-examples/github-broadcast.yml.
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
# .gitattributes is knowledge layer but NOT Group A: git reads merge attributes
# from the ours side, so adopting main's copy mid-merge protects nothing.
#
# TODO(paths): adapt to your project's actual filenames. Must cover every [A] path of
# knowledge_source_of_truth_rule.md §2 and nothing tagged [B] — check-knowledge-paths.py checks it.
KNOWLEDGE_PATHS=(
  "{{project}}_wiki/"          # whole wiki: knowledge pages + work/ (trios + generated index)
  ".agents/"
  ".claude/skills/"
  ".claude/agents/"
  ".claude/hooks/"
  ".claude/settings.json"
  "<per-agent-config>"         # TODO(paths): e.g. .gemini/settings.json + .gemini/commands/
  ".mcp.json"
  "CLAUDE.md" "GEMINI.md" "AGENTS.md" "README.md"
  "<workspace-file>"           # TODO(paths): e.g. the multi-root editor workspace file
)

# ── TODO(env): map your CI's variables onto these two, in the CI job ──────────
# Keep the mapping in the pipeline config, not here, so this script stays
# host-neutral and its test (test-broadcast-main.sh) keeps exercising it as is.
#   CI_COMMIT_SHA  — the commit that triggered the run (the head of main).
#     GitHub Actions: ${GITHUB_SHA} · GitLab CI: ${CI_COMMIT_SHA} · Bitbucket: ${BITBUCKET_COMMIT}
#   CI_PUSH_REMOTE — the authenticated push URL, with the bot credential in it:
#     deploy key over SSH : git@github.com:<owner>/<repo>.git (key loaded by the checkout step)
#     GitHub token        : https://x-access-token:<token>@github.com/<owner>/<repo>.git
#     GitLab              : https://gitlab-ci-token:<token>@gitlab.com/<group>/<repo>.git
#     Bitbucket           : https://x-token-auth:<token>@bitbucket.org/<workspace>/<repo>.git
# There is no separate token variable: the credential travels inside the URL (or
# the SSH key), and a guard demanding a token nothing reads aborts a deploy-key
# push that would have worked.
SHA="${CI_COMMIT_SHA:?TODO set CI_COMMIT_SHA to the CI trigger commit SHA}"
SHORT_SHA="${SHA:0:8}"
PUSH_URL="${CI_PUSH_REMOTE:?TODO set CI_PUSH_REMOTE to the authenticated push URL}"

# Test seam: BROADCAST_REMOTE replaces the push target ONLY. The production inputs
# above are still demanded, so a test run cannot pass while production would fail
# for a missing variable — the first real run of an earlier seam did exactly that.
REMOTE="${BROADCAST_REMOTE:-${PUSH_URL}}"
if [ -n "${BROADCAST_REMOTE:-}" ]; then
  echo "[broadcast-main] TEST SEAM: pushing to BROADCAST_REMOTE, not CI_PUSH_REMOTE"
fi

git config user.email "ci-bot@example.invalid"
git config user.name  "CI Broadcast Bot"

if [ ${#TARGETS[@]} -eq 0 ]; then
  # Exit codes: 0 = something propagated (or, packages only, the push changed
  # nothing under packages/); 1 = any failure, an empty roster, or every roster
  # branch skipped. A broadcast that reaches no branch is never green.
  echo "[broadcast-main] ! TARGETS is empty — fill the roster array first. Nothing propagated."
  exit 1
fi

echo "[broadcast-main] main@${SHORT_SHA} → ${#TARGETS[@]} branch(es): ${TARGETS[*]}"

OK_TARGETS=()
FAIL_TARGETS=()
SKIP_TARGETS=()

for TARGET in "${TARGETS[@]}"; do
  echo ""
  echo "[broadcast-main] === ${TARGET} ==="

  # A roster entry may land on main before its branch is born. Skip it LOUDLY —
  # named here and in the summary — never quietly: a quiet skip is green by
  # absence. ls-remote exits 2 when the ref does not exist; anything else
  # non-zero is a real remote problem.
  git ls-remote --exit-code --heads origin "refs/heads/${TARGET}" >/dev/null 2>&1
  RC=$?
  if [ "${RC}" -eq 2 ]; then
    echo "[broadcast-main]   ⊘ ${TARGET} does not exist on the remote yet — SKIPPED (roster declares it)"
    SKIP_TARGETS+=("${TARGET}"); continue
  elif [ "${RC}" -ne 0 ]; then
    FAIL_TARGETS+=("${TARGET}:ls-remote"); continue
  fi

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
    # Read conflicted paths NUL-delimited into an array so paths with spaces or
    # shell-glob characters are neither word-split nor glob-expanded (a plain
    # `for f in ${CONFLICTS}` would mis-handle them).
    CONFLICTS=()
    while IFS= read -r -d '' f; do CONFLICTS+=("${f}"); done \
      < <(git diff --name-only -z --diff-filter=U)
    KNOWLEDGE_ONLY=1
    for f in "${CONFLICTS[@]}"; do
      match=0
      for p in "${KNOWLEDGE_PATHS[@]}"; do
        case "${f}" in "${p}"*) match=1; break ;; esac
      done
      [ "${match}" = "0" ] && { KNOWLEDGE_ONLY=0; break; }
    done

    # The python3 gate is kept apart from the knowledge-only test on purpose:
    # glued into one `if`, "could not try" and "tried and failed" left by the same
    # door with the same message, and the log blamed a merge conflict that was
    # auto-resolvable. Aborting stays right (reconciling without regenerating the
    # index would leave it inconsistent); what changes is saying why.
    if [ ${#CONFLICTS[@]} -gt 0 ] && [ "${KNOWLEDGE_ONLY}" = "1" ] && ! command -v python3 >/dev/null 2>&1; then
      git merge --abort 2>/dev/null || true
      FAIL_TARGETS+=("${TARGET}:no-python3")
      echo "[broadcast-main]   ✗ ${TARGET} python3 MISSING — the conflict was confined to Group A and auto-resolvable, but regenerating the index needs python3. Nothing changed on ${TARGET}."
      continue
    elif [ ${#CONFLICTS[@]} -gt 0 ] && [ "${KNOWLEDGE_ONLY}" = "1" ]; then
      echo "[broadcast-main]   conflict confined to knowledge layer (Group A) — reconciling with the main version"
      # Adopt main's side. Handle delete/modify correctly: if main DELETED the
      # file (no stage-3 entry in ls-files -u), remove it; otherwise --theirs.
      # (A naive `checkout --theirs || true` would silently KEEP dev's version
      #  when main deleted the file — violating main-canonical.)
      # Name every resolution: adopting main may legitimately discard an
      # unpromoted dev edit, but the loss must be auditable in the log.
      for f in "${CONFLICTS[@]}"; do
        if git ls-files -u -- "${f}" | grep -q '^[0-7]* [0-9a-f]* 3'; then
          git checkout --theirs -- "${f}" && git add -- "${f}"
          echo "[broadcast-main]   ⚠ ${TARGET}: adopted main's '${f}' — any UNPROMOTED edit to it on ${TARGET} was discarded"
        else
          git rm -- "${f}" >/dev/null
          echo "[broadcast-main]   ⚠ ${TARGET}: main DELETED '${f}' — removed on ${TARGET} too"
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
echo "[broadcast-main]   SKIP = ${SKIP_TARGETS[*]:-(none)}"
echo "[broadcast-main]   FAIL = ${FAIL_TARGETS[*]:-(none)}"

if [ ${#FAIL_TARGETS[@]} -gt 0 ]; then
  echo "[broadcast-main] ! Pipeline marked FAILED — ${#FAIL_TARGETS[@]} target(s) need attention"
  exit 1
fi
# Nothing propagated is not a silent success: a broadcast that ran and reached
# no branch must not report green.
if [ ${#OK_TARGETS[@]} -eq 0 ]; then
  echo "[broadcast-main] ! No target propagated — every roster branch was skipped"
  exit 1
fi
echo "[broadcast-main] done"
