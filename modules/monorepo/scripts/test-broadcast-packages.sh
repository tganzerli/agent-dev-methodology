#!/usr/bin/env bash
#
# scripts/test-broadcast-packages.sh — runs broadcast-packages.sh against a
# throwaway bare remote. Never touches the real host. Same shape as
# test-broadcast-main.sh: the roster is read from the script, and an empty
# roster (the kit template) is replaced by two probe apps in a temporary copy.
#
# Usage: bash scripts/test-broadcast-packages.sh [path/to/broadcast-packages.sh]
# Exit 1 if any check fails.

set -uo pipefail

HERE="$(cd "$(dirname "$0")" && pwd)"
SRC_SCRIPT="${1:-${HERE}/broadcast-packages.sh}"
[ -f "${SRC_SCRIPT}" ] || { echo "no script at ${SRC_SCRIPT}"; exit 2; }

TMP="$(mktemp -d)"
trap 'rm -rf "${TMP}"' EXIT
REMOTE="${TMP}/remote.git"
PASS=0
FAIL=0

# shellcheck disable=SC1090
eval "$(sed -n '/^APPS=(/,/^)/p' "${SRC_SCRIPT}")"
SCRIPT="${SRC_SCRIPT}"
if [ ${#APPS[@]} -eq 0 ]; then
  SCRIPT="${TMP}/broadcast-packages.sh"
  sed 's/^APPS=($/APPS=("alpha" "beta"/' "${SRC_SCRIPT}" > "${SCRIPT}"
  APPS=("alpha" "beta")
fi
D1="dev_${APPS[0]}"
DLAST="dev_${APPS[${#APPS[@]}-1]}"

g() { git -C "${TMP}/author" -c user.name=test -c user.email=test@example.invalid "$@"; }

setup_base() {
  rm -rf "${REMOTE}" "${TMP}/author"
  git init -q --bare "${REMOTE}"
  git init -q -b dev_packages "${TMP}/author"
  g remote add origin "${REMOTE}"
  mkdir -p "${TMP}/author/packages/core" "${TMP}/author/docs"
  echo "version: 0.1.0" > "${TMP}/author/packages/core/version.txt"
  echo "base" > "${TMP}/author/docs/note.md"
  g add -A >/dev/null && g commit -q -m "test base" && g push -q origin dev_packages
  for a in "${APPS[@]}"; do git --git-dir="${REMOTE}" update-ref "refs/heads/dev_${a}" refs/heads/dev_packages; done
}

commit() { # commit <branch> <file> <content>
  g fetch -q origin
  g checkout -q -B "$1" "origin/$1"
  mkdir -p "$(dirname "${TMP}/author/$2")"
  printf '%s\n' "$3" > "${TMP}/author/$2"
  g add -A >/dev/null && g commit -q -m "test: $1 $2" && g push -q origin "$1"
}

rev()  { git --git-dir="${REMOTE}" rev-parse --verify -q "refs/heads/$1"; }
show() { git --git-dir="${REMOTE}" show "refs/heads/$1:$2" 2>/dev/null; }
check() { if [ "$2" = "1" ]; then PASS=$((PASS+1)); echo "  ok    $1"; else FAIL=$((FAIL+1)); echo "  FAIL  $1"; fi; }
yes_if() { if "$@"; then echo 1; else echo 0; fi; }
has() { printf '%s' "${OUT}" | grep -qF -- "$1" && echo 1 || echo 0; }

run_seam() { # run_seam <before-sha>
  rm -rf "${TMP}/work"
  git clone -q "${REMOTE}" "${TMP}/work" -b dev_packages
  local sha; sha="$(git -C "${TMP}/work" rev-parse HEAD)"
  OUT="$(cd "${TMP}/work" && env CI_COMMIT_SHA="${sha}" CI_BEFORE_SHA="$1" \
         CI_PUSH_REMOTE="https://ci.example.invalid/o/r.git" BROADCAST_REMOTE="${REMOTE}" bash "${SCRIPT}" 2>&1)"
  CODE=$?
}

echo "roster: ${APPS[*]}"

echo "== a) push without a change under packages/ -> skipped, devs untouched"
setup_base
B="$(rev dev_packages)"
commit dev_packages docs/note.md "docs only"
BEFORE="$(rev "${D1}")"
run_seam "${B}"
check "exit 0" "$(yes_if [ "${CODE}" -eq 0 ])"
check "says Skipping" "$(has "Skipping")"
check "${D1} unchanged" "$(yes_if [ "$(rev "${D1}")" = "${BEFORE}" ])"

echo "== b) change under packages/ -> each dev gets a merge, app code kept"
setup_base
commit "${D1}" apps/probe/code.txt "app code"
B="$(rev dev_packages)"
commit dev_packages packages/core/new.txt "new in core"
run_seam "${B}"
check "exit 0" "$(yes_if [ "${CODE}" -eq 0 ])"
check "package reached ${D1}" "$(yes_if [ -n "$(show "${D1}" packages/core/new.txt)" ])"
check "app code kept" "$(yes_if [ -n "$(show "${D1}" apps/probe/code.txt)" ])"

echo "== c) conflict on one dev -> that one aborts, the others update, exit 1"
setup_base
commit "${D1}" packages/core/version.txt "version: 0.2.0-dev"
B="$(rev dev_packages)"
commit dev_packages packages/core/version.txt "version: 0.3.0"
BEFORE="$(rev "${D1}")"
run_seam "${B}"
check "exit 1" "$(yes_if [ "${CODE}" -eq 1 ])"
check "reports CONFLICT" "$(has "CONFLICT")"
check "${D1} unchanged" "$(yes_if [ "$(rev "${D1}")" = "${BEFORE}" ])"
if [ "${#APPS[@]}" -gt 1 ]; then
  check "${DLAST} still updated" "$(yes_if [ -n "$(show "${DLAST}" packages/core/version.txt | grep 0.3.0)" ])"

  echo "== d) a roster dev does not exist yet -> skipped loudly, exit 0"
  setup_base
  git --git-dir="${REMOTE}" update-ref -d "refs/heads/${DLAST}"
  B="$(rev dev_packages)"
  commit dev_packages packages/core/new_d.txt "new"
  run_seam "${B}"
  check "exit 0" "$(yes_if [ "${CODE}" -eq 0 ])"
  check "names the skipped branch" "$(has "${DLAST} does not exist on the remote yet")"
fi

echo "== e) no roster dev exists -> exit 1, nothing propagated"
setup_base
for a in "${APPS[@]}"; do git --git-dir="${REMOTE}" update-ref -d "refs/heads/dev_${a}"; done
B="$(rev dev_packages)"
commit dev_packages packages/core/new_e.txt "new"
run_seam "${B}"
check "exit 1" "$(yes_if [ "${CODE}" -eq 1 ])"
check "says nothing propagated" "$(has "No dev propagated")"

echo "== f) PRODUCTION push path (no seam): CI_PUSH_REMOTE rewritten to the bare remote"
setup_base
B="$(rev dev_packages)"
commit dev_packages packages/core/new_f.txt "new"
rm -rf "${TMP}/work"
git clone -q "${REMOTE}" "${TMP}/work" -b dev_packages
SHA="$(git -C "${TMP}/work" rev-parse HEAD)"
URL="https://ci.example.invalid/owner/repo.git"
OUT="$(cd "${TMP}/work" && env -u BROADCAST_REMOTE CI_COMMIT_SHA="${SHA}" CI_BEFORE_SHA="${B}" CI_PUSH_REMOTE="${URL}" \
       GIT_CONFIG_COUNT=1 GIT_CONFIG_KEY_0="url.${REMOTE}.insteadOf" GIT_CONFIG_VALUE_0="${URL}" \
       bash "${SCRIPT}" 2>&1)"
CODE=$?
check "exit 0" "$(yes_if [ "${CODE}" -eq 0 ])"
check "package reached ${D1} through CI_PUSH_REMOTE" "$(yes_if [ -n "$(show "${D1}" packages/core/new_f.txt)" ])"

echo
echo "result: ${PASS} ok, ${FAIL} failed"
[ "${FAIL}" -eq 0 ]
