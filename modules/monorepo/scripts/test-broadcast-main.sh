#!/usr/bin/env bash
#
# scripts/test-broadcast-main.sh — runs broadcast-main.sh against a throwaway bare
# remote. Never touches the real host.
#
# Each scenario builds a fresh remote, moves `main` and the roster branches in a
# specific way, clones it the way CI does, and runs the broadcast. The roster and
# the wiki path are read from the script itself; an empty roster (the kit
# template) is replaced by two probe branches in a temporary copy.
#
# Scenario (h) runs the PRODUCTION push path (no BROADCAST_REMOTE): git is told
# to rewrite the CI_PUSH_REMOTE URL to the bare remote, so the real code path
# runs offline. A seam-only test once passed while production failed.
#
# Usage: bash scripts/test-broadcast-main.sh [path/to/broadcast-main.sh]
# Exit 1 if any check fails.

set -uo pipefail

HERE="$(cd "$(dirname "$0")" && pwd)"
SRC_SCRIPT="${1:-${HERE}/broadcast-main.sh}"
[ -f "${SRC_SCRIPT}" ] || { echo "no script at ${SRC_SCRIPT}"; exit 2; }
command -v python3 >/dev/null 2>&1 || { echo "python3 is required by the scenarios"; exit 2; }

TMP="$(mktemp -d)"
trap 'rm -rf "${TMP}"' EXIT
REMOTE="${TMP}/remote.git"
PASS=0
FAIL=0

# shellcheck disable=SC1090
eval "$(sed -n '/^TARGETS=(/,/^)/p' "${SRC_SCRIPT}")"
# shellcheck disable=SC1090
eval "$(sed -n '/^KNOWLEDGE_PATHS=(/,/^)/p' "${SRC_SCRIPT}")"
SCRIPT="${SRC_SCRIPT}"
if [ ${#TARGETS[@]} -eq 0 ]; then
  SCRIPT="${TMP}/broadcast-main.sh"
  sed 's/^TARGETS=($/TARGETS=("dev_alpha" "dev_beta"/' "${SRC_SCRIPT}" > "${SCRIPT}"
  TARGETS=("dev_alpha" "dev_beta")
fi
WIKI=""
for p in "${KNOWLEDGE_PATHS[@]}"; do
  case "${p}" in *_wiki/) WIKI="${p}"; break ;; esac
done
[ -n "${WIKI}" ] || { echo "no *_wiki/ entry in KNOWLEDGE_PATHS"; exit 2; }
T1="${TARGETS[0]}"
LAST="${TARGETS[${#TARGETS[@]}-1]}"

g() { git -C "${TMP}/author" -c user.name=test -c user.email=test@example.invalid "$@"; }

setup_base() {
  rm -rf "${REMOTE}" "${TMP}/author"
  git init -q --bare "${REMOTE}"
  git init -q -b main "${TMP}/author"
  g remote add origin "${REMOTE}"
  mkdir -p "${TMP}/author/${WIKI}cross-cutting" "${TMP}/author/${WIKI}_meta" \
           "${TMP}/author/apps/probe" "${TMP}/author/.claude/skills/work-index"
  echo "base" > "${TMP}/author/${WIKI}cross-cutting/probe.md"
  echo "# log" > "${TMP}/author/${WIKI}_meta/log.md"
  echo "v1" > "${TMP}/author/apps/probe/code.txt"
  printf '%s\n' "${WIKI}_meta/log.md merge=union" > "${TMP}/author/.gitattributes"
  # Stand-in for the work-index generator the reconcile step calls.
  cat > "${TMP}/author/.claude/skills/work-index/generate.py" <<PY
import os
os.makedirs("${WIKI}work/archive", exist_ok=True)
open("${WIKI}work/_index.md", "w").write("# index\n")
open("${WIKI}work/archive/.keep", "w").write("")
PY
  g add -A >/dev/null && g commit -q -m "test base" && g push -q origin main
  for t in "${TARGETS[@]}"; do git --git-dir="${REMOTE}" update-ref "refs/heads/${t}" refs/heads/main; done
}

commit() { # commit <branch> <file> <w|a> <content>
  g fetch -q origin
  g checkout -q -B "$1" "origin/$1"
  mkdir -p "$(dirname "${TMP}/author/$2")"
  if [ "$3" = "a" ]; then printf '%s\n' "$4" >> "${TMP}/author/$2"; else printf '%s\n' "$4" > "${TMP}/author/$2"; fi
  g add -A >/dev/null && g commit -q -m "test: $1 $2" && g push -q origin "$1"
}

clone_work() {
  rm -rf "${TMP}/work"
  git clone -q "${REMOTE}" "${TMP}/work" -b main
  SHA="$(git -C "${TMP}/work" rev-parse HEAD)"
}

run_seam() { # run through the BROADCAST_REMOTE seam
  clone_work
  OUT="$(cd "${TMP}/work" && env CI_COMMIT_SHA="${SHA}" CI_PUSH_REMOTE="https://ci.example.invalid/o/r.git" \
         BROADCAST_REMOTE="${REMOTE}" bash "${SCRIPT}" 2>&1)"
  CODE=$?
}

rev()  { git --git-dir="${REMOTE}" rev-parse --verify -q "refs/heads/$1"; }
show() { git --git-dir="${REMOTE}" show "refs/heads/$1:$2" 2>/dev/null; }
check() { if [ "$2" = "1" ]; then PASS=$((PASS+1)); echo "  ok    $1"; else FAIL=$((FAIL+1)); echo "  FAIL  $1"; fi; }
yes_if() { if "$@"; then echo 1; else echo 0; fi; }
file_has() { show "$1" "$2" | grep -q -- "$3"; }
has() { printf '%s' "${OUT}" | grep -qF -- "$1" && echo 1 || echo 0; }

echo "roster: ${TARGETS[*]}   wiki: ${WIKI}"

echo "== a) targets behind main, no divergence -> fast-forward"
setup_base
commit main "${WIKI}cross-cutting/new_a.md" w "from main"
run_seam
check "exit 0" "$(yes_if [ "${CODE}" -eq 0 ])"
check "${T1} == main" "$(yes_if [ "$(rev "${T1}")" = "$(rev main)" ])"

echo "== b) target has its own code, no conflict -> merge commit, code kept"
setup_base
commit "${T1}" apps/probe/own.txt w "only on ${T1}"
commit main "${WIKI}cross-cutting/new_b.md" w "from main"
run_seam
check "exit 0" "$(yes_if [ "${CODE}" -eq 0 ])"
check "app code kept" "$(yes_if [ -n "$(show "${T1}" apps/probe/own.txt)" ])"
check "knowledge from main arrived" "$(yes_if [ -n "$(show "${T1}" "${WIKI}cross-cutting/new_b.md")" ])"
check "merge commit (2 parents)" "$(yes_if [ "$(git --git-dir="${REMOTE}" rev-list --parents -n1 "refs/heads/${T1}" | wc -w)" -eq 3 ])"

echo "== c) conflict confined to Group A -> adopts main's version, names it"
setup_base
commit "${T1}" "${WIKI}cross-cutting/probe.md" w "dev version"
commit main "${WIKI}cross-cutting/probe.md" w "main version"
run_seam
check "exit 0" "$(yes_if [ "${CODE}" -eq 0 ])"
check "file has main's version" "$(yes_if [ "$(show "${T1}" "${WIKI}cross-cutting/probe.md")" = "main version" ])"
check "log names the adopted file" "$(has "adopted main's '${WIKI}cross-cutting/probe.md'")"

echo "== d) conflict outside Group A -> that target aborts, the others still update"
setup_base
commit "${T1}" apps/probe/code.txt w "v2-dev"
commit main apps/probe/code.txt w "v3-main"
BEFORE="$(rev "${T1}")"
run_seam
check "exit 1" "$(yes_if [ "${CODE}" -eq 1 ])"
check "reports CONFLICT" "$(has "CONFLICT")"
check "${T1} unchanged" "$(yes_if [ "$(rev "${T1}")" = "${BEFORE}" ])"
if [ "${#TARGETS[@]}" -gt 1 ]; then
  check "${LAST} still updated (best effort)" "$(yes_if [ "$(rev "${LAST}")" = "$(rev main)" ])"
fi

echo "== e) both sides append to _meta/log.md -> merge=union keeps both"
setup_base
commit "${T1}" "${WIKI}_meta/log.md" a "ENTRY-DEV"
commit main "${WIKI}_meta/log.md" a "ENTRY-MAIN"
run_seam
check "exit 0" "$(yes_if [ "${CODE}" -eq 0 ])"
check "dev entry kept" "$(yes_if file_has "${T1}" "${WIKI}_meta/log.md" ENTRY-DEV)"
check "main entry present" "$(yes_if file_has "${T1}" "${WIKI}_meta/log.md" ENTRY-MAIN)"

if [ "${#TARGETS[@]}" -gt 1 ]; then
  echo "== f) a roster branch does not exist yet -> skipped loudly, exit 0"
  setup_base
  git --git-dir="${REMOTE}" update-ref -d "refs/heads/${LAST}"
  commit main "${WIKI}cross-cutting/new_f.md" w "from main"
  run_seam
  check "exit 0" "$(yes_if [ "${CODE}" -eq 0 ])"
  check "names the skipped branch" "$(has "${LAST} does not exist on the remote yet")"
  check "${T1} == main" "$(yes_if [ "$(rev "${T1}")" = "$(rev main)" ])"
fi

echo "== g) no roster branch exists -> exit 1, nothing propagated"
setup_base
for t in "${TARGETS[@]}"; do git --git-dir="${REMOTE}" update-ref -d "refs/heads/${t}"; done
commit main "${WIKI}cross-cutting/new_g.md" w "from main"
run_seam
check "exit 1" "$(yes_if [ "${CODE}" -eq 1 ])"
check "says nothing propagated" "$(has "No target propagated")"

echo "== h) PRODUCTION push path (no seam): CI_PUSH_REMOTE rewritten to the bare remote"
setup_base
commit main "${WIKI}cross-cutting/new_h.md" w "from main"
clone_work
URL="https://ci.example.invalid/owner/repo.git"
OUT="$(cd "${TMP}/work" && env -u BROADCAST_REMOTE CI_COMMIT_SHA="${SHA}" CI_PUSH_REMOTE="${URL}" \
       GIT_CONFIG_COUNT=1 GIT_CONFIG_KEY_0="url.${REMOTE}.insteadOf" GIT_CONFIG_VALUE_0="${URL}" \
       bash "${SCRIPT}" 2>&1)"
CODE=$?
check "exit 0" "$(yes_if [ "${CODE}" -eq 0 ])"
check "no seam banner" "$(yes_if [ "$(has "TEST SEAM")" = "0" ])"
check "${T1} == main (pushed through CI_PUSH_REMOTE)" "$(yes_if [ "$(rev "${T1}")" = "$(rev main)" ])"

echo "== i) CI_PUSH_REMOTE missing -> fails loudly even with the seam set, pushes nothing"
setup_base
commit main "${WIKI}cross-cutting/new_i.md" w "from main"
BEFORE="$(rev "${T1}")"
clone_work
OUT="$(cd "${TMP}/work" && env -u CI_PUSH_REMOTE CI_COMMIT_SHA="${SHA}" BROADCAST_REMOTE="${REMOTE}" bash "${SCRIPT}" 2>&1)"
CODE=$?
check "exit != 0" "$(yes_if [ "${CODE}" -ne 0 ])"
check "message names CI_PUSH_REMOTE" "$(has "CI_PUSH_REMOTE")"
check "${T1} unchanged" "$(yes_if [ "$(rev "${T1}")" = "${BEFORE}" ])"

echo "== j) python3 missing on a Group A conflict -> says so, not 'CONFLICT'"
setup_base
commit "${T1}" "${WIKI}cross-cutting/probe.md" w "dev version"
commit main "${WIKI}cross-cutting/probe.md" w "main version"
BEFORE="$(rev "${T1}")"
clone_work
mkdir -p "${TMP}/bin"
for tool in git tail grep sed cat; do ln -sf "$(command -v "${tool}")" "${TMP}/bin/${tool}"; done
OUT="$(cd "${TMP}/work" && env PATH="${TMP}/bin" CI_COMMIT_SHA="${SHA}" CI_PUSH_REMOTE="x" \
       BROADCAST_REMOTE="${REMOTE}" "$(command -v bash)" "${SCRIPT}" 2>&1)"
CODE=$?
check "exit 1" "$(yes_if [ "${CODE}" -eq 1 ])"
check "names python3" "$(has "python3 MISSING")"
check "${T1} unchanged" "$(yes_if [ "$(rev "${T1}")" = "${BEFORE}" ])"

if [ "${SCRIPT}" != "${SRC_SCRIPT}" ]; then
  echo "== k) empty roster (the template as shipped) -> exit 1, nothing propagated"
  setup_base
  clone_work
  OUT="$(cd "${TMP}/work" && env CI_COMMIT_SHA="${SHA}" CI_PUSH_REMOTE="x" BROADCAST_REMOTE="${REMOTE}" bash "${SRC_SCRIPT}" 2>&1)"
  CODE=$?
  check "exit 1" "$(yes_if [ "${CODE}" -eq 1 ])"
  check "says the roster is empty" "$(has "TARGETS is empty")"
fi

echo
echo "result: ${PASS} ok, ${FAIL} failed"
[ "${FAIL}" -eq 0 ]
