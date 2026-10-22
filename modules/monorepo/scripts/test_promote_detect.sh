#!/bin/sh
# Self-test of scripts/promote_detect.py.
#
# Builds a temporary repo with the scenario that reproduced both failures of the
# old commit-graph detection and asserts the properties the fix promises. Case 4
# is a NEGATIVE PROOF: it runs the OLD logic on the same scenario and requires it
# to FAIL -- without it, a regression back to graph inference would pass green.
set -eu

HERE=$(cd "$(dirname "$0")" && pwd)
DET="${HERE}/promote_detect.py"
[ -f "${DET}" ] || { echo "ERROR: ${DET} does not exist." >&2; exit 2; }
WIKI=$(sed -n 's/^WIKI = "\(.*\)"$/\1/p' "${DET}")
[ -n "${WIKI}" ] || { echo "ERROR: could not read WIKI from ${DET}." >&2; exit 2; }

TMP=$(mktemp -d)
trap 'rm -rf "${TMP}"' EXIT

OK=0
FAILED=0
assert() { # assert <description> <got: yes/no> <expected>
  if [ "$2" = "$3" ]; then
    OK=$((OK + 1)); echo "  ok    $1"
  else
    FAILED=$((FAILED + 1)); echo "  FAIL  $1 (expected=$3 got=$2)" >&2
  fi
}
has() { echo "$1" | grep -qxF -- "$2" && echo yes || echo no; }
field() { echo "${OUT}" | python3 -c 'import json,sys;print("\n".join(json.load(sys.stdin)[sys.argv[1]]))' "$1"; }

cd "${TMP}"
git init -q -b main .
git config user.email t@t; git config user.name t
mkdir -p "${WIKI}/work/tasks" "${WIKI}/decisions" scripts

W=2026-01-01_probe
TRIO="${WIKI}/work/tasks/${W}.md"
ADR_WITH="${WIKI}/decisions/adr-with-trio.md"
ADR_ALONE="${WIKI}/decisions/adr-alone.md"
OLD=scripts/old-file.sh
MASK="${WIKI}/decisions/ ${WIKI}/_meta/ scripts/"

# (i) a commit touching the trio AND a file, which stays ON THE BASE. This is the
#     trap of the excess failure: the old logic reaches it and brings OLD along.
echo v1 > "${TRIO}"; echo v1 > "${OLD}"
git add -A; git commit -q -m "base: trio + old file"
git branch -f base_ref

# (ii) probe A -- trio and ADR in the SAME commit
echo v2 >> "${TRIO}"; echo a > "${ADR_WITH}"
git add -A; git commit -q -m "probe A: trio + ADR together"

# (iii) probe B -- ADR ALONE, trio untouched
echo b > "${ADR_ALONE}"
git add -A; git commit -q -m "probe B: ADR alone"

OUT=$(python3 "${DET}" "${W}" --mask "${MASK}" --base base_ref --source HEAD --format json)
DIV=$(field divergent); ORP=$(field orphan); ATT=$(field attributed); TRI=$(field divergent_trios)

echo "== case 1: knowledge committed APART from the trio must not vanish"
assert "probe B in DIVERGENT" "$(has "${DIV}" "${ADR_ALONE}")" yes
assert "probe B in ORPHAN"    "$(has "${ORP}" "${ADR_ALONE}")" yes

echo "== case 2: a file from a commit ALREADY ON THE BASE must not appear"
assert "old file not in DIVERGENT"  "$(has "${DIV}" "${OLD}")" no
assert "old file not in ATTRIBUTED" "$(has "${ATT}" "${OLD}")" no

echo "== case 3: knowledge committed with the trio is attributed"
assert "probe A in ATTRIBUTED" "$(has "${ATT}" "${ADR_WITH}")" yes
assert "probe A not in ORPHAN" "$(has "${ORP}" "${ADR_WITH}")" no

echo "== case 3b: a divergent trio is reported (catches drift of other work_ids)"
assert "trio in DIVERGENT_TRIOS" "$(has "${TRI}" "${TRIO}")" yes

echo "== case 4: NEGATIVE PROOF -- the OLD logic loses probe B and brings the old file"
OLDLOGIC=$(git log --format=%H -- "${TRIO}" \
  | while read -r c; do git show --name-only --format= "$c"; done \
  | sort -u | grep -E "^(${WIKI}/(decisions|_meta)/|scripts/)" || true)
assert "old logic LOSES probe B"           "$(has "${OLDLOGIC}" "${ADR_ALONE}")" no
assert "old logic BRINGS the old file"     "$(has "${OLDLOGIC}" "${OLD}")"       yes

echo
if [ "${FAILED}" -gt 0 ]; then
  echo "FAILED: ${FAILED} assertion(s) failed, ${OK} passed." >&2
  exit 1
fi
echo "OK: ${OK} assertions, 0 failures."
