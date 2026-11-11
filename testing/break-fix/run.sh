#!/bin/bash
# Break/fix runner.
#   run.sh list
#   run.sh break|diagnose|fix|verify <scenario>
#   run.sh cycle <scenario>   verify(pass) -> break -> verify(must fail) -> diagnose -> fix -> verify(pass)
#   run.sh all                cycle every scenario, write testing/reports/break-fix-report.md
set -uo pipefail
HERE="$(cd "$(dirname "$0")" && pwd)"; source "$HERE/lib.sh"
REPORTS="$ROOT/testing/reports"; mkdir -p "$REPORTS/evidence"
scn() { local d; d=$(ls -d "$HERE/scenarios/"*"$1"* 2>/dev/null | head -1); [ -n "$d" ] || { echo "unknown scenario: $1" >&2; exit 2; }; echo "$d"; }
step() { bash "$1/$2.sh"; }

cycle() {
  local d id; d=$(scn "$1"); id=$(basename "$d"); local result=PASS t0=$SECONDS t t_break t_detect t_fix t_recover
  echo "=== $id"
  # retry the baseline once: a service restarted by the previous scenario may still be settling
  step "$d" verify >/dev/null 2>&1 || { sleep 8; step "$d" verify >/dev/null 2>&1; } \
    || { echo "  baseline verify FAILED - lab not healthy"; echo "$id|BASELINE-FAIL|-|-|-|-|$((SECONDS-t0))"; return 1; }
  echo "  baseline ok"; t=$SECONDS; step "$d" break >/dev/null 2>&1; t_break=$((SECONDS-t)); echo "  fault injected (${t_break}s)"
  t=$SECONDS
  if step "$d" verify >/dev/null 2>&1; then echo "  !! fault not detected by verify"; result=NOT-DETECTED; else echo "  verify fails as expected"; fi
  t_detect=$((SECONDS-t))
  step "$d" diagnose 2>&1 | redact > "$REPORTS/evidence/$id.txt"; echo "  evidence -> testing/reports/evidence/$id.txt"
  t=$SECONDS; step "$d" fix >/dev/null 2>&1; t_fix=$((SECONDS-t)); echo "  fix applied (${t_fix}s)"
  t=$SECONDS
  if step "$d" verify >/dev/null 2>&1; then echo "  recovered"; else echo "  !! still failing after fix"; result=FIX-FAILED; fi
  t_recover=$((SECONDS-t))
  # id|result|inject s|detect s|fix s|verify-after-fix s|whole cycle s
  echo "$id|$result|$t_break|$t_detect|$t_fix|$t_recover|$((SECONDS-t0))"; [ "$result" = PASS ]
}

case "${1:-list}" in
  list) for f in "$HERE"/scenarios/*/scenario.json; do "$PY" -c "import json,sys;d=json.load(open(sys.argv[1]));print(f\"{d['id']:28} {d['ticket']}  {d['title']}\")" "$f"; done;;
  break|diagnose|fix|verify) d=$(scn "${2:?scenario}"); step "$d" "$1";;
  cycle) cycle "${2:?scenario}";;
  all)
    out="$REPORTS/break-fix-report.md"; rc=0
    { echo "# Break/fix report"; echo; echo "Run: $(date -u +%FT%TZ)"; echo; echo "| Scenario | Result | Inject (s) | Detect (s) | Fix (s) | Verify after fix (s) | Cycle (s) |"; echo "|---|---|---|---|---|---|---|"; } > "$out"
    for d in "$HERE"/scenarios/*/; do
      line=$(cycle "$(basename "$d")" | tee /dev/stderr | tail -1)
      IFS='|' read -r f_id f_res f_rest <<< "$line"; [ "$f_res" = PASS ] || rc=1
      echo "| $f_id | $f_res | ${f_rest//|/ | } |" >> "$out"
    done; echo "report -> $out"; exit $rc;;
  *) sed -n 2,7p "$0";;
esac
