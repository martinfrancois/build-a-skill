#!/usr/bin/env bash
# Screen eval scenarios locally before spending Tessl credits, or when Tessl blocks
# hosted runs: run each scenario through Claude Code with DeepSeek V4.1 Flash (the
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
  scripts/local_screen.sh [-n runs] [-p parallel] [-m baseline|skill] [-s start] [-x] <scenario-dir>...
  scripts/local_screen.sh --summary [-m baseline|skill]

Runs each scenario's task.md through Claude Code with DeepSeek V4.1 Flash as the
solver and grades every run against criteria.json with a Claude judge. See
docs/agents/local-screening.md. -x runs the scenarios' setup scripts on this
machine with your account; pass it only for scenarios you wrote or have read.
USAGE
}

repo="$(cd "$(dirname "$0")/.." && pwd -P)"
skill_dirs=("$repo"/skills/*/)
[ "${#skill_dirs[@]}" = 1 ] && [ -d "${skill_dirs[0]}" ] || { echo "expected exactly one skill under skills/, found ${#skill_dirs[@]}" >&2; exit 2; }
skill_name="$(basename "${skill_dirs[0]}")"
out_root="${LOCAL_SCREEN_OUT:-$repo/.local-screen}"
key_file="${DEEPSEEK_API_KEY_FILE:-$HOME/deepseek-api-key}"
runs=2; par=3; mode=baseline; start=1; summary=0; run_setup=0
while [ $# -gt 0 ]; do
  case "$1" in
    -n) runs="$2"; shift 2 ;;
    -p) par="$2"; shift 2 ;;
    -m) mode="$2"; shift 2 ;;
    -s) start="$2"; shift 2 ;;
    -x) run_setup=1; shift ;;
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

# A path from scenario.json names a place inside a folder: relative, with no ".." part.
stays_inside() {
  case "/$1/" in
    //* | */../*) return 1 ;;
  esac
}

# Whether directory $1, with symlinks resolved, lies under the canonical directory $2.
resolves_under() {
  local real
  real="$(cd "$1" && pwd -P)" || return 1
  case "$real/" in "$2"/*) return 0 ;; *) return 1 ;; esac
}

# Copies folder $3 of scenario $1 into $4 under work directory $2. A scenario may come from an
# untrusted contribution, so neither path may leave its folder, and the source may hold no
# symlinks: with none copied, no later destination can resolve outside the work directory.
copy_into_work() {
  local scenario_dir="$1" work="$2" from="$1/$3" to="$2/$4"
  if ! stays_inside "$3" || ! stays_inside "$4"; then
    echo "$3 -> $4: scenario.json paths must be relative, with no '..'" >&2
    return 1
  fi
  if [ ! -d "$from" ] || ! resolves_under "$from" "$scenario_dir"; then
    echo "$3: not a folder inside the scenario" >&2
    return 1
  fi
  if [ -n "$(find "$from" -type l | head -n 1)" ]; then
    echo "$3: holds a symlink, which the local screen does not copy" >&2
    return 1
  fi
  mkdir -p "$to"
  resolves_under "$to" "$work" || { echo "$4: resolves outside the work directory" >&2; return 1; }
  cp -a "$from/." "$to/"
}

# Installs what Tessl installs before the agent starts, in the same order: directory fixtures
# from scenario.json, then its include folders (resources/ by default), then its setup scripts
# (setup.sh last by default), run in the work directory. Commit fixtures need a clone from the
# network, which the local screen does not do. Setup scripts run on this machine with the
# user's account, so they run only with -x.
install_scenario_files() {
  local scenario_dir work spec path install script setup_copy_dir
  scenario_dir="$(cd "$1" && pwd -P)"
  work="$(cd "$2" && pwd -P)"
  spec="$scenario_dir/scenario.json"
  if [ -f "$spec" ]; then
    if jq -e '.fixtures // {} | to_entries | any(.value.type != "directory")' "$spec" > /dev/null; then
      echo "$spec: only directory fixtures run locally" >&2
      return 1
    fi
    while IFS=$'\t' read -r path install; do
      copy_into_work "$scenario_dir" "$work" "$path" "$install" || return 1
    done < <(jq -r '.fixtures // {} | to_entries[] | [.value.path, .value.installPath] | @tsv' "$spec")
    while IFS= read -r path; do
      copy_into_work "$scenario_dir" "$work" "$path" "$path" || return 1
    done < <(jq -r '.include // [] | .[]' "$spec")
  fi
  if [ -d "$scenario_dir/resources" ] && ! { [ -f "$spec" ] && jq -e 'has("include")' "$spec" > /dev/null; }; then
    copy_into_work "$scenario_dir" "$work" resources resources || return 1
  fi
  {
    [ -f "$spec" ] && jq -r '.setup // [] | .[]' "$spec"
    [ -f "$scenario_dir/setup.sh" ] && echo "./setup.sh"
  } | awk '!seen[$0]++' | while IFS= read -r script; do
    if [ "$run_setup" != 1 ]; then
      echo "$scenario_dir: runs $script; read it, then pass -x to run it on this machine" >&2
      return 1
    fi
    if ! stays_inside "$script" || [ ! -f "$scenario_dir/$script" ]; then
      echo "$script: not a file inside the scenario" >&2
      return 1
    fi
    # Tessl uploads the setup script without the other files in the scenario folder, so run a
    # copy of it alone in a temporary directory: a script that reads a file beside it fails here
    # as it would there. env -i keeps this script's variables, the key file's path among them,
    # out of its environment.
    setup_copy_dir="$(mktemp -d)"
    cp "$scenario_dir/$script" "$setup_copy_dir/"
    (cd "$work" && env -i HOME="$setup_copy_dir" PATH="$PATH" bash "$setup_copy_dir/$(basename "$script")") \
      || { rm -r "${setup_copy_dir:?}"; return 1; }
    rm -r "${setup_copy_dir:?}"
  done
}

solve_one() {
  local scenario_dir="$1" i="$2" name run_dir work prompt
  scenario_dir="$(cd "$scenario_dir" && pwd -P)"
  name="$(basename "$scenario_dir")"
  run_dir="$out/$name/run-$i"
  work="$run_dir/work"
  if [ -e "$run_dir" ]; then echo "[$name] run $i exists, skipping (use -s for new run numbers)"; return 0; fi
  mkdir -p "$work"
  install_scenario_files "$scenario_dir" "$work" || { echo "[$name] run $i: could not install the scenario's files" >&2; return 0; }
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
export -f solve_one install_scenario_files copy_into_work stays_inside resolves_under
export out mode cfg key_file repo skill_name run_setup

runs_to_do=()
for s in "$@"; do
  for i in $(seq "$start" $((start + runs - 1))); do runs_to_do+=("$s"$'\t'"$i"); done
done
printf '%s\n' "${runs_to_do[@]}" | xargs -P "$par" -L 1 bash -c 'solve_one "$0" "$1"'
