#!/usr/bin/env bash
#
# scripts/broadcast-packages.sh  —  TEMPLATE / STUB (adapt to your CI before use)
#
# Top-down broadcast: dev_packages → dev_<app> via DIRECT AUTO-MERGE (no PRs).
# Intended to run on your CI when something is pushed/merged into `dev_packages`.
#
# ────────────────────────────────────────────────────────────────────────────
# THIS IS A HOST-NEUTRAL TEMPLATE. It is runnable-shaped bash, but you MUST
# adapt the marked TODOs to your git host (GitHub Actions / GitLab CI / Bitbucket
# Pipelines / …) before relying on it. Only the environment variables, the
# authenticated push URL, and the trigger wiring differ per host — the LOGIC is
# host-neutral.
# ────────────────────────────────────────────────────────────────────────────
#
# Install this script only if the repo has SHARED PACKAGES on a `dev_packages`
# trunk (see git_branching_rule.md §6). A monorepo of independent apps with no
# shared package layer does not need it.
#
# Why this exists: the human review gate happens ONCE, on the PR
# pkg/<id>__<pkg> → dev_packages. After that merge, this script propagates the
# change to every consuming dev_<app> with no intermediate PRs.
#
# Conflict strategy: BEST-EFFORT. Abort the problematic dev, continue the others,
# mark the pipeline failed, log the summary.
#
# Precondition (configure in your git host UI): branch protection on `dev_*` must
# grant a push exception to the CI bot identity (repository access token / deploy
# key with write scope). Humans stay restricted to PRs; only the bot pushes.

set -uo pipefail   # NOT -e: best-effort loop must continue past a failed dev

# ── TODO(roster): fill with the app slugs that consume the shared packages ────
# ⚠ Hardcoded roster — keep in sync with TARGETS in broadcast-main.sh, the root
# workspace manifest, and your CI pipeline config (see
# knowledge_source_of_truth_rule.md §9). The loop builds TARGET="dev_${APP}".
APPS=(
  # "web"
  # "mobile"
)

# ── TODO(env): map these to your CI's provided variables ──────────────────────
#   GitHub Actions : ${GITHUB_SHA}, ${GITHUB_TOKEN}
#   GitLab CI      : ${CI_COMMIT_SHA}, ${CI_JOB_TOKEN}
#   Bitbucket      : ${BITBUCKET_COMMIT}, ${BITBUCKET_TOKEN}
SHA="${CI_COMMIT_SHA:?TODO set this to the CI trigger commit SHA}"
SHORT_SHA="${SHA:0:8}"
TOKEN="${CI_BOT_TOKEN:?TODO set this to the CI bot write token}"

# TODO(remote): build the authenticated push URL for your host (see broadcast-main.sh).
REMOTE="${CI_PUSH_REMOTE:?TODO set this to the authenticated push URL}"

# ── No-op gate ────────────────────────────────────────────────────────────────
# If the push to dev_packages introduced no change under packages/, this is a
# fast-forward of main (or a commit with no package effect). Skip the broadcast
# to avoid purposeless merge commits on the devs.
# A push may introduce several commits; inspect the whole pushed range, not just
# the tip. Map CI_BEFORE_SHA to your host's "before" SHA:
#   GitHub Actions : ${{ github.event.before }}
#   GitLab CI      : ${CI_COMMIT_BEFORE_SHA}
# A plain HEAD^..HEAD only sees the tip commit and false-skips a multi-commit push
# whose package change sits in an earlier commit. Falls back to HEAD^ when no
# "before" SHA is available (e.g. a brand-new branch's first push).
BEFORE="${CI_BEFORE_SHA:-}"
if [ -z "${BEFORE}" ] || ! git rev-parse --verify --quiet "${BEFORE}^{commit}" >/dev/null 2>&1; then
  BEFORE="$(git rev-parse --verify --quiet HEAD^ 2>/dev/null || true)"
fi
if [ -n "${BEFORE}" ]; then
  if git diff --quiet "${BEFORE}" "${SHA}" -- packages/; then
    echo "[broadcast-packages] dev_packages@${SHORT_SHA} — no change under packages/ across the pushed range. Skipping."
    exit 0
  fi
fi

git config user.email "ci-bot@example.invalid"
git config user.name  "CI Broadcast Bot"

if [ ${#APPS[@]} -eq 0 ]; then
  echo "[broadcast-packages] APPS is empty — fill the roster array first. Nothing to do."
  exit 0
fi

echo "[broadcast-packages] dev_packages@${SHORT_SHA} → ${#APPS[@]} app(s): ${APPS[*]}"

OK_APPS=()
FAIL_APPS=()

for APP in "${APPS[@]}"; do
  TARGET="dev_${APP}"
  echo ""
  echo "[broadcast-packages] === ${TARGET} ==="

  # Explicit refspec for shallow CI clones (see broadcast-main.sh).
  if ! git fetch --no-tags origin "+refs/heads/${TARGET}:refs/remotes/origin/${TARGET}" 2>&1 | tail -3; then
    FAIL_APPS+=("${APP}:fetch"); continue
  fi
  if ! git checkout -B "${TARGET}" "origin/${TARGET}" 2>&1 | tail -3; then
    FAIL_APPS+=("${APP}:checkout"); continue
  fi

  # Merge dev_packages into the app branch. A package change is pure code, so
  # there is no knowledge-layer auto-reconcile here — a conflict aborts this dev
  # (best-effort) and is resolved manually via /distribute-packages.
  if git merge --no-ff --no-edit "${SHA}" -m "broadcast: dev_packages@${SHORT_SHA} → ${TARGET}"; then
    if git push "${REMOTE}" "${TARGET}" 2>&1 | tail -3; then
      OK_APPS+=("${APP}"); echo "[broadcast-packages]   ✓ ${TARGET} updated"
    else
      FAIL_APPS+=("${APP}:push"); echo "[broadcast-packages]   ✗ ${TARGET} push failed"
    fi
  else
    git merge --abort 2>/dev/null || true
    FAIL_APPS+=("${APP}:conflict")
    echo "[broadcast-packages]   ✗ ${TARGET} CONFLICT — aborted, resolve manually via /distribute-packages"
  fi
done

echo ""
echo "[broadcast-packages] summary:"
echo "[broadcast-packages]   OK   = ${OK_APPS[*]:-(none)}"
echo "[broadcast-packages]   FAIL = ${FAIL_APPS[*]:-(none)}"

if [ ${#FAIL_APPS[@]} -gt 0 ]; then
  echo "[broadcast-packages] ! Pipeline marked FAILED — ${#FAIL_APPS[@]} dev(s) need attention"
  exit 1
fi
echo "[broadcast-packages] done"
