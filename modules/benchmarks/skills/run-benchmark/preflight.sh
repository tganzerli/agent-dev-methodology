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
# Linux (/proc) and macOS (sysctl, memory_pressure). A value that cannot be measured
# is written as `null` and named by `check`; it never becomes a false 0.
set -uo pipefail
export LC_ALL=C

SWAP_PCT_CEIL="${SWAP_PCT_CEIL:-60}"
MEM_FREE_PCT_FLOOR="${MEM_FREE_PCT_FLOOR:-40}"

measure() {
  swap_used="" swap_total="" mem_free="" load1="" boot="" swap_pct="" uptime_days=""
  case "$(uname -s)" in
    Linux)
      if [ -r /proc/meminfo ]; then
        read -r st sf mt ma < <(awk '
          /^SwapTotal:/{st=$2} /^SwapFree:/{sf=$2} /^MemTotal:/{mt=$2} /^MemAvailable:/{ma=$2}
          END{print st+0, sf+0, mt+0, ma+0}' /proc/meminfo)
        swap_used=$(( (st - sf) / 1024 )); swap_total=$(( st / 1024 ))
        [ "$mt" -gt 0 ] && [ "$ma" -gt 0 ] && mem_free=$(( ma * 100 / mt ))
      fi
      load1=$(awk '{print $1}' /proc/loadavg 2>/dev/null)
      up=$(awk '{printf "%d", $1}' /proc/uptime 2>/dev/null)
      [ -n "$up" ] && boot=$(( $(date +%s) - up ))
      ;;
    Darwin)
      su=$(sysctl -n vm.swapusage 2>/dev/null)
      swap_used=$(sed -n 's/.*used = \([0-9.,]*\)M.*/\1/p' <<<"$su" | tr ',' '.')
      swap_total=$(sed -n 's/.*total = \([0-9.,]*\)M.*/\1/p' <<<"$su" | tr ',' '.')
      swap_used=${swap_used%.*}; swap_total=${swap_total%.*}
      mem_free=$(memory_pressure 2>/dev/null | sed -n 's/.*free percentage: \([0-9]*\)%.*/\1/p')
      load1=$(sysctl -n vm.loadavg 2>/dev/null | tr -d '{}' | awk '{print $1}' | tr ',' '.')
      # `{ sec = N, usec = M }` - anchor on `{ sec`, since `.*sec = ` matches usec.
      boot=$(sysctl -n kern.boottime 2>/dev/null | sed -n 's/{ sec = \([0-9]*\).*/\1/p')
      ;;
  esac
  [ -n "$boot" ] && uptime_days=$(( ( $(date +%s) - boot ) / 86400 ))
  if [ -n "$swap_used" ] && [ -n "$swap_total" ]; then
    swap_pct=$(awk -v u="$swap_used" -v t="$swap_total" 'BEGIN{if(t<=0){print 0}else{printf "%.0f", u*100/t}}')
  fi
  missing=""
  for v in swap_pct mem_free load1 uptime_days; do
    [ -z "${!v}" ] && missing="${missing:+$missing, }$v"
  done
}

val() { [ -n "$1" ] && echo "$1" || echo "null   # could not measure"; }

emit_yaml() {
  cat <<YAML
host_state:
  measured_at: "$(date +%FT%T%z)"
  swap_used_mb: $(val "$swap_used")
  swap_total_mb: $(val "$swap_total")
  swap_pct: $(val "$swap_pct")
  mem_free_pct: $(val "$mem_free")
  load1: $(val "$load1")
  uptime_days: $(val "$uptime_days")
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
    echo "[preflight] swap ${swap_pct:-?}% (${swap_used:-?}/${swap_total:-?} MB, ceiling ${SWAP_PCT_CEIL}%) · free ${mem_free:-?}% (floor ${MEM_FREE_PCT_FLOOR}%) · load1 ${load1:-?} · uptime ${uptime_days:-?}d"
    outside=0
    [ -n "$swap_pct" ] && [ "$swap_pct" -gt "$SWAP_PCT_CEIL" ] && outside=1
    [ -n "$mem_free" ] && [ "$mem_free" -lt "$MEM_FREE_PCT_FLOOR" ] && outside=1
    [ -n "$missing" ] && echo "[preflight] could not measure: ${missing}"
    if [ "$outside" = 1 ] || [ -n "$missing" ]; then
      why="host outside the declared floor"
      [ "$outside" = 0 ] && why="host state could not be measured (${missing})"
      if [ "${BENCH_ALLOW_DIRTY_HOST:-0}" = 1 ]; then
        echo "[preflight] ⚠ ${why}; continuing because BENCH_ALLOW_DIRTY_HOST=1."
        echo "[preflight] The override IS stamped into the page's host_state. Absolutes of this"
        echo "[preflight] run are not comparable with those of a prepared window."
        emit_yaml 1
        exit 0
      fi
      echo "[preflight] ABORT: ${why}."
      echo "[preflight] Options:"
      echo "[preflight]   1. prepare the host (reboot, close what holds memory or CPU), or make the"
      echo "[preflight]      missing probe available, and repeat;"
      echo "[preflight]   2. measure anyway, declared: BENCH_ALLOW_DIRTY_HOST=1"
      echo "[preflight]      - the override goes into the page's host_state, it does not vanish."
      exit 1
    fi
    echo "[preflight] OK - within the floor."
    emit_yaml 0
    ;;
  *)
    sed -n '2,18p' "$0"; exit 2 ;;
esac
