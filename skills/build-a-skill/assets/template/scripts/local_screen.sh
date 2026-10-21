#!/usr/bin/env bash
# Screen eval scenarios locally before spending Tessl credits, or when the credits
# are used up: run each scenario through Claude Code with DeepSeek V4.1 Flash (the
# model behind Tessl's default solver) and grade the result with a Claude judge.
# Baseline mode gives the solver no skill context and decides suite placement;
# skill mode copies the one skill under skills/ into the work directory.
# Run with -h for usage; docs/agents/local-screening.md has the full method.
#
# Needs: a DeepSeek API key file at $DEEPSEEK_API_KEY_FILE (default
# ~/deepseek-api-key), the claude CLI, jq, python3. Output goes to
# $LOCAL_SCREEN_OUT (default .local-screen/, gitignored). One run costs one to
# two US cents. An existing run directory is left alone; pick new run numbers
# with -s to rerun. The judge uses the regular claude login; LOCAL_SCREEN_JUDGE
# sets its model (default haiku). Local numbers are never hosted evidence.
set -euo pipefail

usage() {
  cat <<'USAGE'
Usage:
  scripts/local_screen.sh [-n runs] [-p parallel] [-m baseline|skill] [-s start] <scenario-dir>...
  scripts/local_screen.sh --summary [-m baseline|skill]

Runs each scenario's task.md through Claude Code with DeepSeek V4.1 Flash as the
solver and grades every run against criteria.json with a Claude judge. See
docs/agents/local-screening.md.
USAGE
}

repo="$(cd "$(dirname "$0")/.." && pwd -P)"
skill_dirs=("$repo"/skills/*/)
[ "${#skill_dirs[@]}" = 1 ] && [ -d "${skill_dirs[0]}" ] || { echo "expected exactly one skill under skills/, found ${#skill_dirs[@]}" >&2; exit 2; }
skill_name="$(basename "${skill_dirs[0]}")"
out_root="${LOCAL_SCREEN_OUT:-$repo/.local-screen}"
key_file="${DEEPSEEK_API_KEY_FILE:-$HOME/deepseek-api-key}"
runs=2; par=3; mode=baseline; start=1; summary=0
while [ $# -gt 0 ]; do
  case "$1" in
    -n) runs="$2"; shift 2 ;;
    -p) par="$2"; shift 2 ;;
    -m) mode="$2"; shift 2 ;;
    -s) start="$2"; shift 2 ;;
    --summary) summary=1; shift ;;
    -h|--help) usage; exit 0 ;;
    --) shift; break ;;
    -*) echo "unknown flag $1" >&2; exit 2 ;;
    *) break ;;
  esac
done
case "$mode" in baseline|skill) ;; *) echo "-m takes baseline or skill, not $mode" >&2; exit 2 ;; esac
out="$out_root/$mode"
mkdir -p "$out"

if [ "$summary" = 1 ]; then
  for d in "$out"/*/; do
    [ -d "$d" ] || continue
    name="$(basename "$d")"
    jq -s -r --arg n "$name" '
      map(.assessmentResults | (100 * (map(.score) | add) / (map(.max_score) | add)))
      | select(length > 0)
      | "\($n)\t\(length) runs\tmean=\((add / length) | round)\tmin=\(min | round)\tmax=\(max | round)"' \
      "$d"/run-*/assessment.json 2>/dev/null || true
  done
  exit 0
fi

[ $# -gt 0 ] || { echo "no scenario directories given" >&2; exit 2; }
[ -r "$key_file" ] || { echo "DeepSeek API key file not readable: $key_file" >&2; exit 2; }

cfg="$out_root/claude-config"
mkdir -p "$cfg"
[ -f "$cfg/settings.json" ] || printf '{"hasCompletedOnboarding":true}\n' > "$cfg/settings.json"

solve_one() {
  local scenario_dir="$1" i="$2" name run_dir work prompt
  scenario_dir="$(cd "$scenario_dir" && pwd -P)"
  name="$(basename "$scenario_dir")"
  run_dir="$out/$name/run-$i"
  work="$run_dir/work"
  if [ -e "$run_dir" ]; then echo "[$name] run $i exists, skipping (use -s for new run numbers)"; return 0; fi
  mkdir -p "$work"
  prompt="$(cat "$scenario_dir/task.md")"
  if [ "$mode" = skill ]; then
    mkdir -p "$work/.claude/skills"
    cp -a "$repo/skills/$skill_name" "$work/.claude/skills/"
    prompt="Use the $skill_name skill available in this project for this task.

$prompt"
  fi
  echo "[$name] run $i ($mode)"
  (
    cd "$work"
    CLAUDE_CONFIG_DIR="$cfg" \
    ANTHROPIC_BASE_URL=https://api.deepseek.com/anthropic \
    ANTHROPIC_API_KEY="$(cat "$key_file")" \
    timeout 900 claude -p --model deepseek-flash --output-format json \
      --restricted --permission-mode acceptEdits --permission-prompts none --max-turns 40 \
      "$prompt" > "$run_dir/solver.json" 2> "$run_dir/solver.err" || echo "[$name] run $i: solver exit $?"
  )
  DEEPSEEK_API_KEY_FILE="$key_file" python3 "$repo/scripts/local_screen_judge.py" \
    "$scenario_dir" "$run_dir" "${LOCAL_SCREEN_JUDGE:-haiku}" "$mode"
}
export -f solve_one
export out mode cfg key_file repo skill_name

runs_to_do=()
for s in "$@"; do
  for i in $(seq "$start" $((start + runs - 1))); do runs_to_do+=("$s"$'\t'"$i"); done
done
printf '%s\n' "${runs_to_do[@]}" | xargs -P "$par" -L 1 bash -c 'solve_one "$0" "$1"'
