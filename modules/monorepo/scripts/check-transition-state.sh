#!/usr/bin/env bash
# Fails if a dev_* branch exists on the remote while the pre-app transition section
# (§1.1 of git_branching_rule.md) is still in the rule. A transition state that
# outlives its own trigger stops being a transition and becomes a loophole; this
# check is what enforces the removal instead of someone remembering it.
# Usage: scripts/check-transition-state.sh [remote]   (default: origin)
set -euo pipefail
rule=".agents/rules/git_branching_rule.md"
remote="${1:-origin}"
cd "$(dirname "$0")/.."
dev_branches=$(git ls-remote --heads "$remote" 'dev_*' | awk '{print $2}')
if [ -n "$dev_branches" ] && grep -q '^## 1\.1\. Transition state' "$rule"; then
  echo "ERROR: ${rule}: dev_* exists (${dev_branches//$'\n'/ }) and §1.1 is still in the rule. Remove §1.1 (see §1.1 itself)."
  exit 1
fi
echo "ok: transition state consistent (dev_*: ${dev_branches:-none})"
