#!/usr/bin/env bash
# preflight.sh - measure the host's state at the START of a run and decide whether it may begin.
#
# The ceilings are NOT a causal threshold; they are provisional and parameterizable.
# What this enforces is procedural: do not measure absolutes on an unprepared host
# without saying so in the artifact (benchmark_protocol_rule.md §4.1). Hence the
# override exists, and it STAMPS `override: true` into host_state instead of hiding it.
#
# Usage:
#   preflight.sh check   # decide; print the host_state block; exit 1 if outside the floor
#   preflight.sh yaml    # only print the host_state block, always exit 0
#
# Environment:
#   SWAP_PCT_CEIL (60)  MEM_FREE_PCT_FLOOR (40)  BENCH_HOST_PREPARATION ("not declared")
#   BENCH_ALLOW_DIRTY_HOST=1   run anyway, stamped
#
# Linux (/proc) and macOS (sysctl, memory_pressure). Elsewhere a value reads 0 and
# the check says so rather than pass silently.
set -uo pipefail
export LC_ALL=C

SWAP_PCT_CEIL="${SWAP_PCT_CEIL:-60}"
MEM_FREE_PCT_FLOOR="${MEM_FREE_PCT_FLOOR:-40}"

measure() {
  swap_used=0 swap_total=0 mem_free=0 load1=0 boot="" unknown=""
  case "$(uname -s)" in
    Linux)
      read -r swap_total swap_free mem_total mem_avail < <(awk '
        /^SwapTotal:/{st=$2} /^SwapFree:/{sf=$2} /^MemTotal:/{mt=$2} /^MemAvailable:/{ma=$2}
        END{print st+0, sf+0, mt+0, ma+0}' /proc/meminfo)
      swap_used=$(( (swap_total - swap_free) / 1024 )); swap_total=$(( swap_total / 1024 ))
      [ "$mem_total" -gt 0 ] && mem_free=$(( mem_avail * 100 / mem_total ))
      load1=$(awk '{print $1}' /proc/loadavg)
      boot=$(( $(date +%s) - $(awk '{printf "%d", $1}' /proc/uptime) ))
      ;;
    Darwin)
      swap_used=$(sysctl -n vm.swapusage | sed -n 's/.*used = \([0-9.,]*\)M.*/\1/p' | tr ',' '.')
      swap_total=$(sysctl -n vm.swapusage | sed -n 's/.*total = \([0-9.,]*\)M.*/\1/p' | tr ',' '.')
      swap_used=${swap_used%.*}; swap_total=${swap_total%.*}
      mem_free=$(memory_pressure 2>/dev/null | sed -n 's/.*free percentage: \([0-9]*\)%.*/\1/p')
      load1=$(sysctl -n vm.loadavg | tr -d '{}' | awk '{print $1}' | tr ',' '.')
      # `{ sec = N, usec = M }` - anchor on `{ sec`, since `.*sec = ` matches usec.
      boot=$(sysctl -n kern.boottime | sed -n 's/{ sec = \([0-9]*\).*/\1/p')
      ;;
    *) unknown="$(uname -s)" ;;
  esac
  swap_used=${swap_used:-0}; swap_total=${swap_total:-0}; mem_free=${mem_free:-0}
  uptime_days=$(( ( $(date +%s) - ${boot:-$(date +%s)} ) / 86400 ))
  swap_pct=$(awk -v u="$swap_used" -v t="$swap_total" 'BEGIN{if(t<=0){print 0}else{printf "%.0f", u*100/t}}')
}

emit_yaml() {
  cat <<YAML
host_state:
  measured_at: "$(date +%FT%T%z)"
  swap_used_mb: ${swap_used}
  swap_total_mb: ${swap_total}
  swap_pct: ${swap_pct}
  mem_free_pct: ${mem_free}
  load1: ${load1}
  uptime_days: ${uptime_days}
  preparation: "${BENCH_HOST_PREPARATION:-not declared}"
YAML
  [ "$1" = 1 ] && echo "  override: true"
  return 0
}

measure
case "${1:-check}" in
  yaml)
    emit_yaml "${BENCH_ALLOW_DIRTY_HOST:-0}"
    ;;
  check)
    echo "[preflight] swap ${swap_pct}% (${swap_used}/${swap_total} MB, ceiling ${SWAP_PCT_CEIL}%) · free ${mem_free}% (floor ${MEM_FREE_PCT_FLOOR}%) · load1 ${load1} · uptime ${uptime_days}d"
    bad=0
    [ -n "$unknown" ] && { echo "[preflight] cannot measure on ${unknown}"; bad=1; }
    [ "$swap_pct" -gt "$SWAP_PCT_CEIL" ] && bad=1
    [ "$mem_free" -lt "$MEM_FREE_PCT_FLOOR" ] && bad=1
    if [ "$bad" = 1 ]; then
      if [ "${BENCH_ALLOW_DIRTY_HOST:-0}" = 1 ]; then
        echo "[preflight] ⚠ host outside the floor; continuing because BENCH_ALLOW_DIRTY_HOST=1."
        echo "[preflight] The override IS stamped into the page's host_state. Absolutes of this"
        echo "[preflight] run are not comparable with those of a prepared window."
        emit_yaml 1
        exit 0
      fi
      echo "[preflight] ABORT: host outside the declared floor."
      echo "[preflight] Options:"
      echo "[preflight]   1. prepare the host (reboot, close what holds memory or CPU) and repeat;"
      echo "[preflight]   2. measure anyway, declared: BENCH_ALLOW_DIRTY_HOST=1"
      echo "[preflight]      - the override goes into the page's host_state, it does not vanish."
      exit 1
    fi
    echo "[preflight] OK - within the floor."
    emit_yaml 0
    ;;
  *)
    sed -n '2,19p' "$0"; exit 2 ;;
esac
