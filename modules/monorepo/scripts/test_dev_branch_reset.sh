#!/bin/sh
# Self-test of scripts/dev_branch_reset.py.
#
# Builds temporary repos (a bare remote, the working clone, and a second clone
# playing the broadcast/promotion) and asserts the properties the script promises.
# Case 9 is a NEGATIVE PROOF: it runs three NAIVE criteria on the same scenarios and
# requires them to be WRONG -- without it, a script degenerating into "0 ahead",
# "equal trees" or "compare only what exists on both sides" would pass green.
set -eu

HERE=$(cd "$(dirname "$0")" && pwd)
RESET="${HERE}/dev_branch_reset.py"
[ -f "${RESET}" ] || { echo "ERROR: ${RESET} does not exist." >&2; exit 2; }

TMP=$(mktemp -d)
trap 'rm -rf "${TMP}"' EXIT

OK=0
FAILED=0
assert() { # assert <description> <got> <expected>
  if [ "$2" = "$3" ]; then
    OK=$((OK + 1)); echo "  ok    $1"
  else
    FAILED=$((FAILED + 1)); echo "  FAIL  $1 (expected=$3 got=$2)" >&2
  fi
}
contains() { printf '%s' "$1" | grep -qF -- "$2" && echo yes || echo no; }

G() { git -c user.email=t@t -c user.name=t "$@"; }

# setup <dir> [branch]: origin.git (bare), work (clone) and other (clone), both on the branch.
setup() {
  D="${TMP}/$1"; B="${2:-dev_probe}"
  mkdir -p "${D}"
  git init -q --bare "${D}/origin.git"
  git clone -q "${D}/origin.git" "${D}/work" 2>/dev/null
  (
    cd "${D}/work"
    mkdir -p notes; echo base > notes/base.md; echo x > notes/x.md
    G add -A; G commit -q -m base; G branch -M main; G push -q origin main
    G checkout -q -b "${B}"; G push -q origin "${B}"
  )
  git clone -q "${D}/origin.git" "${D}/other" 2>/dev/null
  ( cd "${D}/other"; G checkout -q "${B}" )
}
# commit_in <clone> <file> <content> <message>
commit_in() {
  ( cd "$1"; mkdir -p "$(dirname "$2")"; printf '%s\n' "$3" > "$2"; G add -A; G commit -q -m "$4" )
}
# Simulated promotion: "other" writes the SAME content in another commit and publishes it.
promote() { # promote <dir> <file> <content> [branch]
  commit_in "${1}/other" "$2" "$3" "promoted (copy)"
  ( cd "${1}/other"; G push -q origin "${4:-dev_probe}" )
}
run() { # run <dir> args... -> RC and OUT
  D="$1"; shift
  OUT=$(python3 "${RESET}" --root "${D}/work" "$@" 2>&1) && RC=0 || RC=$?
}
head_of() { git -C "${1}/work" rev-parse HEAD; }
short_of() { git -C "${1}/work" rev-parse --short HEAD; }
backups() { git -C "${1}/work" for-each-ref --format='%(refname:short)' 'refs/heads/backup/*' | grep -c . || true; }

echo "== case 1: local content already promoted (different hashes) -> safe; --apply backs up and resets"
setup c1
commit_in "${TMP}/c1/work" notes/a.md v1 "local authoring"
promote "${TMP}/c1" notes/a.md v1
run "${TMP}/c1"
assert "diverged (ahead and behind) but safe: exit 0" "${RC}" "0"
assert "report says SAFE" "$(contains "${OUT}" 'VERDICT: SAFE')" yes
H1=$(head_of "${TMP}/c1"); S1=$(short_of "${TMP}/c1")
run "${TMP}/c1" --apply --expect-head "${S1}" --date 2026-01-01
assert "--apply: exit 0" "${RC}" "0"
assert "HEAD == origin/dev_probe after reset" "$(git -C "${TMP}/c1/work" rev-parse HEAD)" "$(git -C "${TMP}/c1/work" rev-parse origin/dev_probe)"
assert "backup points at the old HEAD" "$(git -C "${TMP}/c1/work" rev-parse backup/dev_probe-2026-01-01)" "${H1}"
assert "tree after reset == backup tree (nothing lost)" "$(git -C "${TMP}/c1/work" rev-parse 'HEAD^{tree}')" "$(git -C "${TMP}/c1/work" rev-parse 'backup/dev_probe-2026-01-01^{tree}')"
run "${TMP}/c1"
assert "after the reset: 0 ahead, still safe" "$(contains "${OUT}" 'ahead: 0')" yes

echo "== case 2: new LOCAL-ONLY file -> refused, nothing changes"
setup c2
commit_in "${TMP}/c2/work" notes/b.md new "local only"
H2=$(head_of "${TMP}/c2")
run "${TMP}/c2"
assert "exit 1" "${RC}" "1"
assert "lists the file as new" "$(contains "${OUT}" 'LOCAL ONLY (new): notes/b.md')" yes
run "${TMP}/c2" --apply --expect-head "$(short_of "${TMP}/c2")"
assert "--apply refuses too" "${RC}" "1"
assert "HEAD intact" "$(head_of "${TMP}/c2")" "${H2}"
assert "no backup created" "$(backups "${TMP}/c2")" "0"

echo "== case 3: remote ahead (broadcast), local behind, local content promoted -> safe"
setup c3
commit_in "${TMP}/c3/work" notes/a.md v1 "local authoring"
promote "${TMP}/c3" notes/a.md v1
promote "${TMP}/c3" notes/c.md from-broadcast
run "${TMP}/c3"
assert "safe while behind" "${RC}" "0"
assert "report shows behind: 2" "$(contains "${OUT}" 'behind: 2')" yes

echo "== case 4: promoted and THEN changed on the remote -> refused (accepted false negative)"
setup c4
commit_in "${TMP}/c4/work" notes/a.md v1 "local authoring"
promote "${TMP}/c4" notes/a.md v2
run "${TMP}/c4"
assert "exit 1 (conservative)" "${RC}" "1"

echo "== case 5: local deletion the remote does not have yet -> refused"
setup c5
( cd "${TMP}/c5/work"; G rm -q notes/x.md; G commit -q -m "remove x" )
run "${TMP}/c5"
assert "exit 1" "${RC}" "1"
assert "lists it as deleted" "$(contains "${OUT}" 'LOCAL ONLY (deleted): notes/x.md')" yes

echo "== case 6: uncommitted tracked change -> refused; the reset does not run"
setup c6
commit_in "${TMP}/c6/work" notes/a.md v1 "local authoring"
promote "${TMP}/c6" notes/a.md v1
( cd "${TMP}/c6/work"; echo dirt >> notes/base.md )
H6=$(head_of "${TMP}/c6")
run "${TMP}/c6" --apply --expect-head "$(short_of "${TMP}/c6")"
assert "exit 1" "${RC}" "1"
assert "HEAD intact" "$(head_of "${TMP}/c6")" "${H6}"
assert "uncommitted change preserved" "$(grep -c dirt "${TMP}/c6/work/notes/base.md")" "1"

echo "== case 7: not a dev_<app> (dev_packages, staging_x, main, detached) -> refused"
for b in dev_packages staging_probe; do
  setup "c7_${b}" "${b}"
  run "${TMP}/c7_${b}"
  assert "${b}: exit 1" "${RC}" "1"
  assert "${b}: reason is the branch" "$(contains "${OUT}" 'branch is a dev_<app>')" yes
done
setup c7_main
( cd "${TMP}/c7_main/work"; G checkout -q main )
run "${TMP}/c7_main"
assert "main: exit 1" "${RC}" "1"
( cd "${TMP}/c7_main/work"; G checkout -q --detach )
run "${TMP}/c7_main"
assert "detached HEAD: exit 1" "${RC}" "1"

echo "== case 8: --apply without --expect-head, or with a wrong sha -> refused, nothing changes"
setup c8
commit_in "${TMP}/c8/work" notes/a.md v1 "local authoring"
promote "${TMP}/c8" notes/a.md v1
H8=$(head_of "${TMP}/c8")
run "${TMP}/c8" --apply
assert "no --expect-head: exit 1" "${RC}" "1"
run "${TMP}/c8" --apply --expect-head deadbee
assert "wrong sha: exit 1" "${RC}" "1"
assert "HEAD intact" "$(head_of "${TMP}/c8")" "${H8}"
assert "no backup" "$(backups "${TMP}/c8")" "0"

echo "== case 9: NEGATIVE PROOF -- the naive criteria are wrong on these same scenarios"
A=$(git -C "${TMP}/c3/work" rev-list --count origin/dev_probe..HEAD)
assert "naive A (0 ahead) refuses case 3, which is safe" "$([ "${A}" = "0" ] && echo yes || echo no)" no
git -C "${TMP}/c3/work" diff --quiet origin/dev_probe HEAD && NAIVE_B=yes || NAIVE_B=no
assert "naive B (equal trees) refuses case 3, which is safe" "${NAIVE_B}" no
M2=$(git -C "${TMP}/c2/work" diff --name-only --diff-filter=M HEAD origin/dev_probe | grep -c . || true)
assert "naive C (modified-only) accepts case 2 -- WRONG: local-only file" "$([ "${M2}" = "0" ] && echo yes || echo no)" yes
M5=$(git -C "${TMP}/c5/work" diff --name-only --diff-filter=M HEAD origin/dev_probe | grep -c . || true)
assert "naive C accepts case 5 -- WRONG: local deletion" "$([ "${M5}" = "0" ] && echo yes || echo no)" yes
run "${TMP}/c2"; assert "...and the script refuses case 2" "${RC}" "1"
run "${TMP}/c5"; assert "...and the script refuses case 5" "${RC}" "1"

echo "== case 10: merge half-way -> refused"
setup c10
commit_in "${TMP}/c10/work" notes/a.md v1 "local authoring"
promote "${TMP}/c10" notes/a.md v1
git -C "${TMP}/c10/work" rev-parse HEAD > "${TMP}/c10/work/.git/MERGE_HEAD"
run "${TMP}/c10"
assert "exit 1" "${RC}" "1"
assert "says a merge is in progress" "$(contains "${OUT}" 'merge')" yes

echo "== case 11: an UNTRACKED file does not block and is not touched"
setup c11
commit_in "${TMP}/c11/work" notes/a.md v1 "local authoring"
promote "${TMP}/c11" notes/a.md v1
echo draft > "${TMP}/c11/work/draft.txt"
run "${TMP}/c11"
assert "safe" "${RC}" "0"
assert "warns about the untracked file" "$(contains "${OUT}" 'untracked')" yes
run "${TMP}/c11" --apply --expect-head "$(short_of "${TMP}/c11")"
assert "the untracked file survives the reset" "$([ -f "${TMP}/c11/work/draft.txt" ] && echo yes || echo no)" yes

echo "== case 11b: an UNTRACKED file the remote tracks -> refused (reset --hard would overwrite it)"
setup c11b
commit_in "${TMP}/c11b/work" notes/a.md v1 "local authoring"
promote "${TMP}/c11b" notes/a.md v1
promote "${TMP}/c11b" notes/newf.md theirs
echo mine > "${TMP}/c11b/work/notes/newf.md"
run "${TMP}/c11b" --apply --expect-head "$(short_of "${TMP}/c11b")"
assert "exit 1" "${RC}" "1"
assert "names the file" "$(contains "${OUT}" 'notes/newf.md')" yes
assert "local untracked content survives" "$(cat "${TMP}/c11b/work/notes/newf.md")" "mine"
echo "notes/ign.md" > "${TMP}/c11b/work/.git/info/exclude"
rm "${TMP}/c11b/work/notes/newf.md"; promote "${TMP}/c11b" notes/ign.md theirs
echo mine > "${TMP}/c11b/work/notes/ign.md"
run "${TMP}/c11b"
assert "ignored file the remote tracks: refused too" "${RC}" "1"

echo "== case 12: --format json parses"
run "${TMP}/c3" --format json
assert "valid json with safe=true" "$(printf '%s' "${OUT}" | python3 -c 'import json,sys; print("yes" if json.load(sys.stdin)["safe"] is True else "no")')" yes

echo
echo "${OK} ok, ${FAILED} failed"
[ "${FAILED}" -eq 0 ]
