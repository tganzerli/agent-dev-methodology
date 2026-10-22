#!/bin/sh
# Branch scope barrier — git_branching_rule.md, "Branch scope barrier".  TEMPLATE.
#
# Keeps one app's code out of a branch that is not that app's. The invariant:
#
#   apps/<X>     diverges only on X's line         (dev_X, staging_X, ephemerals __X)
#   packages/<P> diverges only on the packages line (dev_packages, ephemerals __P)
#
# Everything else must be IDENTICAL to the baseline the branch received. So the
# only way app code travels between branches is the top-down broadcast from main.
#
# The scope comes from the branch NAME (<type>/<work_id>__<scope>), not from the PR
# target: a release checked against its target instead once carried 254 files to
# main instead of 8.
#
# POSIX sh on purpose, so it runs in a minimal git image.
#
# Usage:
#   scripts/check_branch_scope.sh [branch] [ref]
#     branch  default: $SCOPE_BRANCH   (TODO(env): map from your CI, e.g. the PR source branch)
#     ref     default: HEAD            (any commit-ish — used by tests)
#
#   SCOPE_CONTRACT_LINE  where `contract/` branches come from (default: main — rule §3.2).
#                        `dev_packages` = the shared-package variant (git-runbook §5.3):
#                        source dev_packages, any package, no apps/*.
set -eu

# ---------------------------------------------------------------------------
# MODE. 0 = advisory (reports, exits 0); 1 = blocking (exits 1 on a violation).
# Ship advisory. Flip the DEFAULT to 1 only after it has run clean across real
# releases — the installation this came from never flipped it. The env override
# exists so both modes are testable before the flip.
# ---------------------------------------------------------------------------
BLOCKING="${SCOPE_BARRIER_BLOCKING:-0}"

# Ephemeral types (rule §4.2) — keep module-registered types in sync with the rule.
TYPES="feat fix chore docs refactor hotfix pkg tag bench contract"

# A configuration or naming error is reported like a violation: advisory mode
# exits 0, blocking mode exits 1. Advisory means advisory for every finding.
fail() { # fail <message...>
  for line in "$@"; do echo "ERROR: ${line}" >&2; done
  if [ "${BLOCKING}" = "1" ]; then exit 1; fi
  echo "[scope] ADVISORY MODE — reported, not blocking." >&2
  exit 0
}

cd "$(dirname "$0")/.."

BRANCH="${1:-${SCOPE_BRANCH:-}}"
REF="${2:-HEAD}"

if [ -z "${BRANCH}" ]; then
  fail "branch name not given (neither \$1 nor \$SCOPE_BRANCH)."
fi

# ---------------------------------------------------------------------------
# TODO(roster): print the app slugs and package slugs, one per line. Derive them
# from the ROOT workspace manifest, never from a second hardcoded list — a new
# app then enters the barrier on its own. Examples:
#   pub workspace : sed -n '/^workspace:/,/^[a-zA-Z]/p' pubspec.yaml | sed -n 's|^[[:space:]]*-[[:space:]]*apps/||p'
#   directories   : git ls-tree --name-only origin/main apps/ | sed 's|^apps/||'
# SCOPE_APPS / SCOPE_PKGS (space-separated) override both, for tests.
# ---------------------------------------------------------------------------
roster_apps() { :; }
roster_pkgs() { :; }

if [ -n "${SCOPE_APPS:-}" ]; then APPS=$(echo "${SCOPE_APPS}" | tr ' ' '\n'); else APPS=$(roster_apps); fi
if [ -n "${SCOPE_PKGS:-}" ]; then PKGS=$(echo "${SCOPE_PKGS}" | tr ' ' '\n'); else PKGS=$(roster_pkgs); fi

if [ -z "${APPS}" ]; then
  fail "empty app roster — fill roster_apps (TODO(roster)) in $0." \
       "Without a roster the barrier has nothing to check."
fi

# ---------------------------------------------------------------------------
# Branch name -> scope.
#   SCOPE_APP  app whose code this branch MAY change ("" = none, "*" = all)
#   SCOPE_PKG  package this branch MAY change        ("" = none, "*" = all)
# ---------------------------------------------------------------------------
SCOPE_APP=""
SCOPE_PKG=""
EXPECTED=""

is_in() { # is_in <needle> <multi-line list>
  echo "$2" | grep -qx -- "$1"
}

case "${BRANCH}" in
  main|demo_*)
    echo "[scope] ${BRANCH}: outside the barrier (main is not a code source; demo_* is terminal)."
    exit 0
    ;;
  dev_packages) SCOPE_PKG="*" ;;
  dev_*)        SCOPE_APP="${BRANCH#dev_}" ;;
  staging_*)    SCOPE_APP="${BRANCH#staging_}" ;;
  */*)
    TYPE="${BRANCH%%/*}"
    REST="${BRANCH#*/}"
    case "${REST}" in
      *__*) ;;
      *) fail "'${BRANCH}' lacks the '__' separator (<type>/<work_id>__<scope>)." ;;
    esac
    SCOPE="${REST##*__}"
    if ! echo "${TYPES}" | tr ' ' '\n' | grep -qx -- "${TYPE}"; then
      fail "branch type '${TYPE}' does not exist. Valid: ${TYPES}"
    fi
    if [ "${TYPE}" = "contract" ] && [ "${SCOPE_CONTRACT_LINE:-main}" = "dev_packages" ]; then
      # Shared-package variant (git-runbook §5.3): a package change like any other, no apps/*.
      SCOPE_APP=""; SCOPE_PKG="*"; EXPECTED="dev_packages"
    elif [ "${TYPE}" = "contract" ]; then
      # A contract surface lands in every consumer at once, off main (rule §3.2).
      SCOPE_APP="*"; SCOPE_PKG="*"; EXPECTED="main"
    else
      case "${SCOPE}" in
        knowledge|tooling) ;;
        *)
          if is_in "${SCOPE}" "${APPS}"; then
            SCOPE_APP="${SCOPE}"
          elif [ -n "${PKGS}" ] && is_in "${SCOPE}" "${PKGS}"; then
            SCOPE_PKG="${SCOPE}"
          else
            fail "scope '${SCOPE}' is not an app, a package, 'knowledge' or 'tooling'." \
                 "Apps: $(echo "${APPS}" | tr '\n' ' ')" "Packages: $(echo "${PKGS}" | tr '\n' ' ')"
          fi
          ;;
      esac
    fi
    ;;
  *)
    fail "'${BRANCH}' is neither a permanent branch nor <type>/<work_id>__<scope>."
    ;;
esac

# Sources compatible with the declared scope (computed here: detect_parent needs it).
if [ -z "${EXPECTED}" ]; then
  if [ -n "${SCOPE_APP}" ]; then
    EXPECTED="dev_${SCOPE_APP} staging_${SCOPE_APP}"
    # Only a hotfix branches off main (rule §4.2/§4.6).
    if [ "${TYPE:-}" = "hotfix" ]; then EXPECTED="${EXPECTED} main"; fi
  elif [ -n "${SCOPE_PKG}" ]; then
    EXPECTED="dev_packages"
  fi
fi

if [ -n "${SCOPE_APP}" ] && [ "${SCOPE_APP}" != "*" ] && ! is_in "${SCOPE_APP}" "${APPS}"; then
  fail "'${SCOPE_APP}' is not a known app. Apps: $(echo "${APPS}" | tr '\n' ' ')"
fi

# ---------------------------------------------------------------------------
# Baselines. Each axis is compared with what THIS branch received, not with the
# remote tip: against the tip, every branch that has not yet received the latest
# broadcast would report a false positive.
# ---------------------------------------------------------------------------
git fetch -q origin main dev_packages 2>/dev/null || git fetch -q origin main 2>/dev/null || true
if [ -f "$(git rev-parse --git-dir)/shallow" ]; then
  git fetch -q --unshallow origin 2>/dev/null || git fetch -q --deepen=500 origin 2>/dev/null || true
fi

# Test seam: point the axes at a historical state. Defaults in CI.
MAIN_REF="${SCOPE_MAIN_REF:-origin/main}"
PKGS_REF="${SCOPE_PKGS_REF:-origin/dev_packages}"

base_or_skip() { git merge-base "$1" "${REF}" 2>/dev/null || true; }

# ---------------------------------------------------------------------------
# SOURCE branch. An ephemeral legitimately carries what its dev_<app> has ahead of
# main; comparing its content against main would blame it for that inherited work.
# The source is DETECTED: among the permanent branches, the one whose merge-base
# with REF is the most RECENT wins — by DAG ancestry, not by clock (commit times
# have one-second resolution, and broadcasts create commits in bursts).
# Same merge-base on two candidates (e.g. dev_packages level with main, the
# healthy state) is a tie broken by scope. Warnings go to STDERR: this runs in
# command substitution.
# ---------------------------------------------------------------------------
detect_parent() { # detect_parent [<compatible sources...>]
  preferred="$*"; best=""; best_mb=""; best_ts=-1; best_pref=0
  for cand in main dev_packages $(echo "${APPS}" | sed 's|^|dev_|') $(echo "${APPS}" | sed 's|^|staging_|'); do
    git rev-parse --verify -q "origin/${cand}" >/dev/null 2>&1 || continue
    mb=$(git merge-base "origin/${cand}" "${REF}" 2>/dev/null) || continue
    [ -z "${mb}" ] && continue
    ts=$(git log -1 --format=%ct "${mb}" 2>/dev/null || echo 0)
    pref=0
    if [ -n "${preferred}" ] && echo "${preferred}" | tr ' ' '\n' | grep -qx -- "${cand}"; then pref=1; fi
    take=0
    if [ -z "${best_mb}" ]; then
      take=1
    elif [ "${mb}" = "${best_mb}" ]; then
      [ "${pref}" -gt "${best_pref}" ] && take=1
    elif git merge-base --is-ancestor "${best_mb}" "${mb}" 2>/dev/null; then
      take=1
    elif git merge-base --is-ancestor "${mb}" "${best_mb}" 2>/dev/null; then
      take=0
    else
      echo "  ! unrelated merge-bases (${cand} x ${best}); tie broken by scope, then clock." >&2
      if [ "${pref}" -gt "${best_pref}" ]; then take=1
      elif [ "${pref}" -eq "${best_pref}" ] && [ "${ts}" -gt "${best_ts}" ]; then take=1; fi
    fi
    if [ "${take}" = "1" ]; then best="${cand}"; best_mb="${mb}"; best_ts="${ts}"; best_pref="${pref}"; fi
  done
  echo "${best}"
}

case "${BRANCH}" in
  dev_*|staging_*)
    PARENT=""
    BASE_MAIN=$(base_or_skip "${MAIN_REF}")
    BASE_PKGS=$(base_or_skip "${PKGS_REF}")
    ;;
  *)
    # SCOPE_PARENT forces the source — for tests, and for a shallow clone where
    # detection fails: better declared than guessed wrong.
    # shellcheck disable=SC2086
    PARENT="${SCOPE_PARENT:-$(detect_parent ${EXPECTED})}"
    if [ -z "${PARENT}" ]; then
      echo "  ! could not detect the source branch — falling back to the axes."
      BASE_MAIN=$(base_or_skip "${MAIN_REF}")
      BASE_PKGS=$(base_or_skip "${PKGS_REF}")
    else
      BASE_MAIN=$(base_or_skip "origin/${PARENT}")
      BASE_PKGS="${BASE_MAIN}"
    fi
    ;;
esac

# SCOPE_BASE pins both baselines, to re-analyse a historical PR. Not for CI.
if [ -n "${SCOPE_BASE:-}" ]; then BASE_MAIN="${SCOPE_BASE}"; BASE_PKGS="${SCOPE_BASE}"; fi

# A ref already contained in main makes every check vacuously empty: green by
# absence, not green for real. Say so.
if [ -n "${BASE_MAIN}" ] && [ "$(git rev-parse "${BASE_MAIN}")" = "$(git rev-parse "${REF}")" ]; then
  echo "[scope] NOTE: ${REF} is already an ancestor of the baseline — the checks are empty."
  echo "        To re-analyse a historical PR use SCOPE_MAIN_REF=<main at the time>."
fi

echo "[scope] branch=${BRANCH}  source=${PARENT:-(axis)}  app-in-scope=${SCOPE_APP:-none}  package-in-scope=${SCOPE_PKG:-none}"

VIOL=0

# Check C — DERIVATION. To change apps/<X> the branch must come from X's line;
# otherwise cutting from dev_Y, editing apps/X and declaring scope X would pass A.
if [ -n "${PARENT}" ] && [ -n "${EXPECTED}" ] && ! echo "${EXPECTED}" | tr ' ' '\n' | grep -qx -- "${PARENT}"; then
  echo "  x derivation: branch comes from '${PARENT}', but the declared scope requires one of: ${EXPECTED}"
  echo "      Re-cut from the right branch — the work done here does not belong on this line."
  VIOL=$((VIOL + 1))
fi

check_path() { # check_path <baseline> <path> <label>
  [ -z "$1" ] && return 0
  n=$(git diff --name-only "$1" "${REF}" -- "$2" | wc -l | tr -d ' ')
  if [ "${n}" != "0" ]; then
    echo "  x $3: ${n} file(s) diverge — this branch may not change $2"
    git diff --name-only "$1" "${REF}" -- "$2" | sed 's/^/      /' | head -10
    [ "${n}" -gt 10 ] && echo "      ... (+$((n - 10)) files)"
    VIOL=$((VIOL + 1))
  fi
  return 0
}

# Check A — apps outside the scope.
if [ "${SCOPE_APP}" != "*" ]; then
  if [ -z "${BASE_MAIN}" ]; then
    echo "  ! no merge-base with ${MAIN_REF} (shallow clone?) — app check SKIPPED."
  else
    for app in ${APPS}; do
      [ "${app}" = "${SCOPE_APP}" ] && continue
      check_path "${BASE_MAIN}" "apps/${app}" "apps/${app}"
    done
  fi
fi

# Check B — packages outside the scope.
if [ "${SCOPE_PKG}" != "*" ] && [ -n "${PKGS}" ]; then
  if [ -z "${BASE_PKGS}" ]; then
    echo "  ! no merge-base with ${PKGS_REF} — package check SKIPPED."
  else
    for pkg in ${PKGS}; do
      [ "${pkg}" = "${SCOPE_PKG}" ] && continue
      check_path "${BASE_PKGS}" "packages/${pkg}" "packages/${pkg}"
    done
  fi
fi

if [ "${VIOL}" = "0" ]; then
  echo "[scope] OK — nothing outside this branch's scope."
  exit 0
fi

echo ""
echo "[scope] ${VIOL} scope violation(s) (git_branching_rule.md, Branch scope barrier)."
echo "        App code travels between branches only through the broadcast from 'main'."
echo "        To restore a path to the state it received:"
echo "          git checkout <baseline> -- <path> && git clean -fd <path>"
echo "        (never 'git add -A' afterwards — it re-adds what you just removed)"

if [ "${BLOCKING}" = "1" ]; then
  exit 1
fi
echo "[scope] ADVISORY MODE — does not block the merge. Report it before merging."
exit 0
