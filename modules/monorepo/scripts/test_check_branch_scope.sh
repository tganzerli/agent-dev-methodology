#!/bin/sh
# Self-test of scripts/check_branch_scope.sh, against a throwaway repo with a bare
# remote. The roster is passed through SCOPE_APPS / SCOPE_PKGS, so the template's
# empty roster_apps placeholder does not matter here.
set -eu

HERE=$(cd "$(dirname "$0")" && pwd)
SCOPE="${HERE}/check_branch_scope.sh"
[ -f "${SCOPE}" ] || { echo "ERROR: ${SCOPE} does not exist." >&2; exit 2; }

TMP=$(mktemp -d)
trap 'rm -rf "${TMP}"' EXIT
OK=0
FAILED=0
assert() { # assert <description> <got> <expected>
  if [ "$2" = "$3" ]; then OK=$((OK + 1)); echo "  ok    $1"
  else FAILED=$((FAILED + 1)); echo "  FAIL  $1 (expected=$3 got=$2)" >&2; fi
}
contains() { printf '%s' "$1" | grep -qF -- "$2" && echo yes || echo no; }
G() { git -c user.email=t@t -c user.name=t "$@"; }
run() { # run <branch> [env...] -> RC, OUT
  b="$1"; shift
  OUT=$(env "$@" sh scripts/check_branch_scope.sh "${b}" 2>&1) && RC=0 || RC=$?
}

git init -q --bare "${TMP}/origin.git"
git clone -q "${TMP}/origin.git" "${TMP}/w" 2>/dev/null
cd "${TMP}/w"
mkdir -p scripts apps/web apps/mobile packages/core
cp "${SCOPE}" scripts/
echo w > apps/web/a.txt; echo m > apps/mobile/a.txt; echo c > packages/core/a.txt
G add -A; G commit -q -m base; G branch -M main; G push -q origin main
for b in dev_packages dev_web dev_mobile; do G branch -q "${b}" main; G push -q origin "${b}"; done
# Each app line has its own work, as in a real repo.
for app in web mobile; do
  G checkout -q "dev_${app}"; echo own >> "apps/${app}/a.txt"; G commit -qam "own ${app}"; G push -q origin "dev_${app}"
done
export SCOPE_APPS="web mobile" SCOPE_PKGS="core"

echo "== in scope"
G checkout -q dev_web; G checkout -q -b feat/2026-01-01_a__web
echo x >> apps/web/a.txt; G commit -qam "web"
run feat/2026-01-01_a__web
assert "feat __web off dev_web, touching apps/web: exit 0" "${RC}" 0
assert "says OK" "$(contains "${OUT}" '[scope] OK')" yes

echo "== contamination"
echo x >> apps/mobile/a.txt; G commit -qam "mobile"
run feat/2026-01-01_a__web
assert "advisory: exit 0" "${RC}" 0
assert "advisory: reports apps/mobile" "$(contains "${OUT}" 'x apps/mobile')" yes
run feat/2026-01-01_a__web SCOPE_BARRIER_BLOCKING=1
assert "blocking: exit 1" "${RC}" 1

echo "== derivation"
G checkout -q dev_mobile; G checkout -q -b feat/2026-01-01_b__web
echo y >> apps/web/a.txt; G commit -qam "web from the mobile line"
run feat/2026-01-01_b__web SCOPE_BARRIER_BLOCKING=1
assert "feat __web off dev_mobile: derivation violation" "$(contains "${OUT}" 'derivation')" yes
# main moves ahead of dev_web (a release of another app), then a feat is cut from it.
G checkout -q main; echo r >> apps/mobile/a.txt; G commit -qam "mobile release"; G push -q origin main
G checkout -q -b feat/2026-01-01_c__web
echo z >> apps/web/a.txt; G commit -qam "web from main"
run feat/2026-01-01_c__web SCOPE_BARRIER_BLOCKING=1
assert "feat __web off main: derivation violation (only hotfix comes from main)" "$(contains "${OUT}" 'derivation')" yes
G checkout -q main; G checkout -q -b hotfix/2026-01-01_d__web
echo h >> apps/web/a.txt; G commit -qam "hotfix"
run hotfix/2026-01-01_d__web SCOPE_BARRIER_BLOCKING=1
assert "hotfix __web off main: exit 0" "${RC}" 0

echo "== contract/: default route (main) and the shared-package variant (dev_packages)"
G checkout -q dev_packages; echo p >> packages/core/a.txt; G commit -qam "packages line work"; G push -q origin dev_packages
G checkout -q -b contract/2026-01-01_f__core
echo k >> packages/core/a.txt; G commit -qam "contract package"
run contract/2026-01-01_f__core SCOPE_BARRIER_BLOCKING=1
assert "contract off dev_packages, default line main: derivation violation" "$(contains "${OUT}" 'derivation')" yes
run contract/2026-01-01_f__core SCOPE_BARRIER_BLOCKING=1 SCOPE_CONTRACT_LINE=dev_packages
assert "contract off dev_packages, SCOPE_CONTRACT_LINE=dev_packages: exit 0" "${RC}" 0
echo k >> apps/web/a.txt; G commit -qam "app code on a package-line contract"
run contract/2026-01-01_f__core SCOPE_BARRIER_BLOCKING=1 SCOPE_CONTRACT_LINE=dev_packages
assert "package-line contract touching apps/web: exit 1" "${RC}" 1

echo "== naming and configuration errors follow the mode"
run feature/2026-01-01_e__web
assert "unknown type, advisory: exit 0" "${RC}" 0
assert "unknown type is reported" "$(contains "${OUT}" "type 'feature' does not exist")" yes
run feature/2026-01-01_e__web SCOPE_BARRIER_BLOCKING=1
assert "unknown type, blocking: exit 1" "${RC}" 1
run feat/2026-01-01_a__web SCOPE_APPS= SCOPE_BARRIER_BLOCKING=1
assert "empty roster, blocking: exit 1" "${RC}" 1
run feat/2026-01-01_a__web SCOPE_APPS=
assert "empty roster, advisory: exit 0 and reported" "${RC}$(contains "${OUT}" 'empty app roster')" 0yes

echo
echo "${OK} ok, ${FAILED} failed"
[ "${FAILED}" -eq 0 ]
