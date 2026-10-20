#!/usr/bin/env bash
set -euo pipefail

usage() {
  cat <<'USAGE'
Usage:
  scripts/run_eval_suite.sh <main|reference|regression> [scenario ...] [-- tessl eval run args...]

Runs hosted Tessl evals with the repository's variant policy:
  main       -> with and without the skill
  reference  -> with and without the skill
  regression -> with the skill only

A scenario is a folder name, or a path inside the folder of the suite named first.

Examples:
  scripts/run_eval_suite.sh main -- --label "main check"
  scripts/run_eval_suite.sh reference 01-webhook-error-review -- --label "targeted reference"
  scripts/run_eval_suite.sh regression -- --label "regression safety"

The runs use the current Tessl default solver; `tessl eval run --list-agents` shows it. Picking
another one with --agent and --model after -- needs the modelSelection entitlement, which many
free plans lack.

Do not pass --skip-baseline. This script chooses variants from the suite purpose.
The runner passes --skill <name> so runs with the skill use this skill instead of relying on
solver auto-selection. The name is $SKILL_NAME, or the only folder under skills/. It also passes
--force so runs after a skill or runner fix cannot reuse stale hosted solutions.
USAGE
}

reject_variant_flag() {
  case "$1" in
    --skip-baseline|--skip-baseline=*)
      echo "Do not pass --skip-baseline; scripts/run_eval_suite.sh chooses variants by suite." >&2
      exit 2
      ;;
  esac
}

if [[ $# -lt 1 ]]; then
  usage >&2
  exit 2
fi

suite="$1"
shift

variant_args=()
case "$suite" in
  main)
    source_dir="evals"
    variant_label="with and without the skill"
    ;;
  reference)
    source_dir="evals-reference"
    variant_label="with and without the skill"
    ;;
  regression)
    source_dir="evals-regression"
    variant_label="with the skill only"
    variant_args=(--skip-baseline)
    ;;
  -h|--help|help)
    usage
    exit 0
    ;;
  *)
    echo "Unknown suite: $suite" >&2
    usage >&2
    exit 2
    ;;
esac

scenarios=()
extra_args=()
while [[ $# -gt 0 ]]; do
  if [[ "$1" == "--" ]]; then
    shift
    extra_args=("$@")
    break
  fi
  reject_variant_flag "$1"
  scenarios+=("$1")
  shift
done
for arg in ${extra_args[@]+"${extra_args[@]}"}; do
  reject_variant_flag "$arg"
done

if ! command -v tessl >/dev/null 2>&1; then
  echo "tessl CLI is required to run hosted evals." >&2
  exit 127
fi

repo_root="$(git rev-parse --show-toplevel 2>/dev/null || pwd)"
source_path="$repo_root/$source_dir"
# Tessl reads scenarios from evals/ only.
staged_evals="$repo_root/evals"
if [[ ! -d "$source_path" ]]; then
  echo "Missing suite directory: $source_path" >&2
  exit 1
fi

skill_name="${SKILL_NAME:-}"
if [[ -z "$skill_name" ]]; then
  skill_files=("$repo_root"/skills/*/SKILL.md)
  if [[ "${#skill_files[@]}" -ne 1 || ! -f "${skill_files[0]}" ]]; then
    echo "Set SKILL_NAME: expected exactly one skills/<name>/SKILL.md under $repo_root." >&2
    exit 2
  fi
  skill_name="$(basename "$(dirname "${skill_files[0]}")")"
fi

# Prints the scenarios in evals/, then runs tessl against the repository as a plugin.
run_staged_evals() {
  local scenario
  echo "Scenarios:"
  for scenario in "$staged_evals"/*/; do
    if [[ -d "$scenario" ]]; then
      printf '  %s\n' "$(basename "$scenario")"
    fi
  done | sort
  echo "Eval mode: $variant_label"
  (
    cd "$repo_root"
    # The ${name[@]+...} form keeps empty arrays working under set -u in bash 3.2 (macOS).
    tessl eval run ${variant_args[@]+"${variant_args[@]}"} --skill "$skill_name" --force \
      ${extra_args[@]+"${extra_args[@]}"} .
  )
}

# Exits when a suite folder holds no scenario folder, before tessl is called.
require_scenarios() {
  local scenario
  for scenario in "$1"/*/; do
    if [[ -d "$scenario" ]]; then
      return 0
    fi
  done
  echo "No scenarios found in $1" >&2
  exit 1
}

if [[ "$suite" == "main" && "${#scenarios[@]}" -eq 0 ]]; then
  require_scenarios "$source_path"
  echo "Running the main eval suite."
  run_staged_evals
  exit 0
fi

# A scenario is a folder name, or a path whose parent folder is the suite named first, so a
# reference scenario cannot run under the regression variant policy.
scenario_names=()
for requested in ${scenarios[@]+"${scenarios[@]}"}; do
  name="${requested%/}"
  if [[ "$name" == */* ]]; then
    parent="$(basename "$(dirname "$name")")"
    if [[ "$parent" != "$source_dir" ]]; then
      echo "Scenario $requested is not in $source_dir/; pass it to the suite its folder belongs to." >&2
      exit 2
    fi
    name="$(basename "$name")"
  fi
  if [[ ! -d "$source_path/$name" ]]; then
    echo "Unknown $suite scenario: $requested (looked in $source_dir/)" >&2
    exit 1
  fi
  scenario_names+=("$name")
done
if [[ "${#scenario_names[@]}" -eq 0 ]]; then
  require_scenarios "$source_path"
  for scenario in "$source_path"/*/; do
    if [[ -d "$scenario" ]]; then
      scenario_names+=("$(basename "$scenario")")
    fi
  done
fi

# Stage the requested scenarios in evals/ and restore the original folder on exit.
tmp_dir="$(mktemp -d)"
backup_evals="$tmp_dir/evals-original"
if [[ "$suite" == "main" ]]; then
  source_path="$backup_evals"
fi

restore() {
  set +e
  if [[ -d "$backup_evals" ]]; then
    rm -rf "${staged_evals:?}"
    mv "$backup_evals" "$staged_evals"
  fi
  rm -rf "${tmp_dir:?}"
}
trap restore EXIT

mv "$staged_evals" "$backup_evals"
mkdir -p "$staged_evals"
for name in "${scenario_names[@]}"; do
  cp -a "$source_path/$name" "$staged_evals/"
done

echo "Running the $suite eval suite with a temporary evals/ staging area."
run_staged_evals
