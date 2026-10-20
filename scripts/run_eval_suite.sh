#!/usr/bin/env bash
set -euo pipefail

usage() {
  cat <<'USAGE'
Usage:
  scripts/run_eval_suite.sh <main|reference|regression> [scenario ...] [-- tessl eval run args...]

Runs hosted Tessl evals with the repository's variant policy:
  main       -> baseline control and with-context
  reference  -> baseline control and with-context
  regression -> with-context only

Examples:
  scripts/run_eval_suite.sh main -- --label "main check"
  scripts/run_eval_suite.sh reference 01-webhook-error-review -- --label "targeted reference"
  scripts/run_eval_suite.sh regression -- --label "regression safety"

The runs use the current Tessl default solver; `tessl eval run --list-agents` shows it. Picking
another one with --agent and --model after -- needs the modelSelection entitlement, which many
free plans lack.

Do not pass --skip-baseline. This script chooses variants from the suite purpose.
The runner passes --skill <name> so with-context runs exercise this skill instead of relying on
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
    variant_label="baseline control + with-context"
    ;;
  reference)
    source_dir="evals-reference"
    variant_label="baseline control + with-context"
    ;;
  regression)
    source_dir="evals-regression"
    variant_label="with-context only"
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
  for scenario in "$repo_root/evals"/*/; do
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

if [[ "$suite" == "main" && "${#scenarios[@]}" -eq 0 ]]; then
  echo "Running the main eval suite."
  run_staged_evals
  exit 0
fi

# Tessl reads scenarios from evals/, so stage the requested ones there and restore it on exit.
tmp_dir="$(mktemp -d)"
backup_evals="$tmp_dir/evals-original"
staged_evals="$repo_root/evals"
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

copy_scenario() {
  local requested="$1"
  local candidate

  if [[ -d "$source_path/$requested" ]]; then
    candidate="$source_path/$requested"
  elif [[ -d "$requested" ]]; then
    candidate="$(cd "$requested" && pwd)"
  elif [[ -d "$source_path/$(basename "$requested")" ]]; then
    candidate="$source_path/$(basename "$requested")"
  else
    echo "Unknown $suite scenario: $requested" >&2
    exit 1
  fi

  cp -a "$candidate" "$staged_evals/"
}

if [[ "${#scenarios[@]}" -eq 0 ]]; then
  for scenario in "$source_path"/*/; do
    if [[ -d "$scenario" ]]; then
      scenarios+=("$(basename "$scenario")")
    fi
  done
  if [[ "${#scenarios[@]}" -eq 0 ]]; then
    echo "No scenarios found in $source_path" >&2
    exit 1
  fi
fi
for scenario in "${scenarios[@]}"; do
  copy_scenario "$scenario"
done

echo "Running the $suite eval suite with a temporary evals/ staging area."
run_staged_evals
