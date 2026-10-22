#!/usr/bin/env bash
#
# Publish one lock row in <vault>/work/relay/_locks.md DIRECTLY on the shared line.
#
# Why direct, not by PR: a lock that waits for a PR is invisible for its whole
# life (measured: 17.0 h alive, zero visible on the shared line).
# Why a worktree, not a checkout: whoever takes a lock is mid-cycle with a dirty
# tree; switching branches would drag their work along.
#
# The live-state exception in the branching rule promises a machine-bounded diff.
# The check is here, in the guard before the push - an `exit 1`, not a promise.
#
# Environment:
#   SCOPE_LOCK_FILE    repo-relative path of the table (default: <the single *_wiki>/work/relay/_locks.md)
#   SCOPE_LOCK_REMOTE  remote to publish to (default: origin)
#   SCOPE_LOCK_LINE    the shared line every agent reads (default: main). Supported ONLY
#                      for the one line the installed exception names; any other line
#                      is refused, because the push has no human gate.
#   SCOPE_LOCK_RULE    the branching rule carrying the exception
#                      (default: .agents/rules/git_branching_rule.md)

set -euo pipefail
# git's push messages are matched below; keep them in English.
export LC_ALL=C

REPO="$(git rev-parse --show-toplevel)"
HERE="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
REMOTE="${SCOPE_LOCK_REMOTE:-origin}"
LINE="${SCOPE_LOCK_LINE:-main}"
RULE="${SCOPE_LOCK_RULE:-.agents/rules/git_branching_rule.md}"

if [[ -n "${SCOPE_LOCK_FILE:-}" ]]; then
  LOCKS_REL="$SCOPE_LOCK_FILE"
else
  vaults=( "$REPO"/*_wiki )
  if [[ ${#vaults[@]} -ne 1 || ! -d "${vaults[0]}" ]]; then
    echo "scope-lock: no single *_wiki/ vault found; set SCOPE_LOCK_FILE" >&2
    exit 2
  fi
  LOCKS_REL="$(basename "${vaults[0]}")/work/relay/_locks.md"
fi

# The exception must be installed and must name this line and this file.
# Language-neutral: only the backticked line name and the path are matched.
if [[ ! -f "$REPO/$RULE" ]] || ! grep -qF "\`${LINE}\`" "$REPO/$RULE" \
   || ! grep -qF "$LOCKS_REL" "$REPO/$RULE"; then
  echo "scope-lock: REFUSED - ${RULE} does not carry a live-state exception naming \`${LINE}\` and ${LOCKS_REL}." >&2
  echo "scope-lock: install snippets/branching-live-state-exception.md first; no other line receives this exception." >&2
  exit 2
fi

OP="" SCOPE="" OWNER="" WORK_ID="" STATE="held" UNTIL="" SOURCE=""
while [[ $# -gt 0 ]]; do
  case "$1" in
    take|release) OP="$1"; shift ;;
    --scope)   SCOPE="$2";   shift 2 ;;
    --owner)   OWNER="$2";   shift 2 ;;
    --work-id) WORK_ID="$2"; shift 2 ;;
    --state)   STATE="$2";   shift 2 ;;
    --until)   UNTIL="$2";   shift 2 ;;
    --source)  SOURCE="$2";  shift 2 ;;
    *) echo "scope-lock: unknown argument: $1" >&2; exit 2 ;;
  esac
done

[[ -n "$OP"    ]] || { echo "scope-lock: use 'take' or 'release'" >&2; exit 2; }
[[ -n "$SCOPE" ]] || { echo "scope-lock: --scope is required" >&2; exit 2; }
# No `${var,,}`: macOS system bash is 3.2.
if [[ "$OP" == "take" ]]; then
  [[ -n "$OWNER"   ]] || { echo "scope-lock: --owner is required for take" >&2; exit 2; }
  [[ -n "$WORK_ID" ]] || { echo "scope-lock: --work-id is required for take" >&2; exit 2; }
  [[ -n "$UNTIL"   ]] || { echo "scope-lock: --until is required for take" >&2; exit 2; }
  [[ -n "$SOURCE"  ]] || { echo "scope-lock: --source is required for take" >&2; exit 2; }
fi

TMP="$(mktemp -d)"
WT="$TMP/locks"
cleanup() {
  git -C "$REPO" worktree remove --force "$WT" >/dev/null 2>&1 || true
  rm -rf "$TMP"
}
trap cleanup EXIT

git -C "$REPO" fetch --quiet "$REMOTE" "$LINE"
git -C "$REPO" worktree add --quiet --detach "$WT" "$REMOTE/$LINE"
cd "$WT"

for attempt in 1 2 3; do
  git fetch --quiet "$REMOTE" "$LINE"
  git checkout --quiet --detach "$REMOTE/$LINE"

  if [[ "$OP" == "take" ]]; then
    python3 "${HERE}/edit_table.py" --file "$LOCKS_REL" --op take \
      --scope "$SCOPE" --owner "$OWNER" --work-id "$WORK_ID" \
      --state "$STATE" --until "$UNTIL" --source "$SOURCE"
  else
    python3 "${HERE}/edit_table.py" --file "$LOCKS_REL" --op release --scope "$SCOPE"
  fi

  # Stage everything the edit produced, then refuse unless it is exactly one path.
  git add -A
  staged="$(git diff --cached --name-only)"
  if [[ "$staged" != "$LOCKS_REL" ]]; then
    echo "scope-lock: ABORTED - the staged diff is not exactly ${LOCKS_REL}:" >&2
    echo "$staged" | sed 's/^/  /' >&2
    git reset --quiet
    exit 1
  fi

  # `release` takes no --work-id.
  MSG="docs(work): ${OP} scope lock on ${SCOPE}"
  [[ -n "$WORK_ID" ]] && MSG="${MSG} (${WORK_ID})"

  git -c user.name="$(git -C "$REPO" config user.name)" \
      -c user.email="$(git -C "$REPO" config user.email)" \
      commit --quiet -m "$MSG"

  if err="$(git push --quiet "$REMOTE" "HEAD:${LINE}" 2>&1)"; then
    echo "scope-lock: ${OP} published on ${LINE} - $(git rev-parse --short HEAD)"
    exit 0
  fi
  echo "$err" | sed 's/^/  git: /' >&2
  # Only a moved line is worth a retry. A protected branch, auth or hook rejection
  # will not change on the next attempt: fail now, and say so.
  if ! grep -qE '\((fetch first|non-fast-forward)\)' <<<"$err"; then
    echo "scope-lock: push refused - the lock is NOT published (see git's message above)" >&2
    exit 1
  fi
  echo "scope-lock: push rejected (attempt ${attempt}/3) - ${LINE} moved, redoing on top of it" >&2
done

echo "scope-lock: push rejected 3x - ${LINE} is under concurrent writes; the lock is NOT published" >&2
exit 1
