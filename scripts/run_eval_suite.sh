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
  scripts/run_eval_suite.sh main -- --agent claude --model claude-sonnet-4-6 --label "model check"

Model selection:
  The default commands use the current Tessl default solver. Picking a model with --agent and
  --model needs the modelSelection entitlement; on plans without it (including many free plans)
  Tessl answers "Missing required entitlement". Run `tessl eval run --list-agents` to see the
  current default. Background:
  - https://docs.tessl.io/changelog
  - https://tessl.io/blog/why-were-changing-our-default-eval-model/

Do not pass --variant or --skip-baseline. This script chooses variants from the suite purpose.
The runner passes --skill <name> so with-context runs exercise this skill instead of relying on
solver auto-selection. The name is $SKILL_NAME, or the only folder under skills/. It also passes
--force so runs after a skill or runner fix cannot reuse stale hosted solutions.
USAGE
}

print_suite_scenarios() {
  local dir="$1"
  local scenario

  for scenario in "$dir"/*; do
    if [[ -d "$scenario" ]]; then
      printf '  %s\n' "$(basename "$scenario")"
    fi
  done | sort
}

if [[ $# -lt 1 ]]; then
  usage >&2
  exit 2
fi

suite="$1"
shift

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
  case "$1" in
    --)
      shift
      extra_args=("$@")
      break
      ;;
    --variant|--variant=*|--skip-baseline|--skip-baseline=*)
      echo "Do not pass --variant or --skip-baseline; scripts/run_eval_suite.sh chooses variants by suite." >&2
      exit 2
      ;;
    *)
      scenarios+=("$1")
      shift
      ;;
  esac
done

for arg in "${extra_args[@]}"; do
  case "$arg" in
    --variant|--variant=*|--skip-baseline|--skip-baseline=*)
      echo "Do not pass --variant or --skip-baseline; scripts/run_eval_suite.sh chooses variants by suite." >&2
      exit 2
      ;;
  esac
done

if ! command -v tessl >/dev/null 2>&1; then
  echo "tessl CLI is required to run hosted evals." >&2
  exit 127
fi

eval_run_help="$(tessl eval run --help 2>&1 || true)"
# Match the whole flag: newer CLIs list --variant-json but reject --variant.
if grep -qE -- '--variant([^-[:alnum:]]|$)' <<<"$eval_run_help"; then
  case "$suite" in
    main|reference)
      variant_args=(--variant without-context --variant with-context)
      ;;
    regression)
      variant_args=(--variant with-context)
      ;;
  esac
elif grep -q -- "--skip-baseline" <<<"$eval_run_help"; then
  case "$suite" in
    main|reference)
      variant_args=()
      ;;
    regression)
      variant_args=(--skip-baseline)
      ;;
  esac
else
  echo "Unsupported tessl eval run CLI: expected --variant or --skip-baseline support." >&2
  exit 2
fi

repo_root="$(git rev-parse --show-toplevel 2>/dev/null || pwd)"
source_path="$repo_root/$source_dir"
skill_name="${SKILL_NAME:-}"
if [[ -z "$skill_name" ]]; then
  skill_dirs=("$repo_root"/skills/*/SKILL.md)
  if [[ "${#skill_dirs[@]}" -ne 1 || ! -f "${skill_dirs[0]}" ]]; then
    echo "Set SKILL_NAME: expected exactly one skills/<name>/SKILL.md under $repo_root." >&2
    exit 2
  fi
  skill_name="$(basename "$(dirname "${skill_dirs[0]}")")"
fi
skill_args=(--skill "$skill_name")
freshness_args=(--force)
if [[ ! -d "$source_path" ]]; then
  echo "Missing suite directory: $source_path" >&2
  exit 1
fi

if [[ "$suite" == "main" && "${#scenarios[@]}" -eq 0 ]]; then
  echo "Running main eval suite from the linked plugin path."
  echo "Scenarios:"
  print_suite_scenarios "$source_path"
  echo "Eval mode: $variant_label"

  (
    cd "$repo_root"
    tessl eval run "${variant_args[@]}" "${skill_args[@]}" "${freshness_args[@]}" "${extra_args[@]}" .
  )
  exit 0
fi

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
  else
    local base
    base="$(basename "$requested")"
    if [[ -d "$source_path/$base" ]]; then
      candidate="$source_path/$base"
    else
      echo "Unknown $suite scenario: $requested" >&2
      exit 1
    fi
  fi

  cp -a "$candidate" "$staged_evals/"
}

if [[ "${#scenarios[@]}" -eq 0 ]]; then
  found=false
  for scenario in "$source_path"/*; do
    if [[ -d "$scenario" ]]; then
      found=true
      cp -a "$scenario" "$staged_evals/"
    fi
  done
  if [[ "$found" == false ]]; then
    echo "No scenarios found in $source_path" >&2
    exit 1
  fi
else
  for scenario in "${scenarios[@]}"; do
    copy_scenario "$scenario"
  done
fi

echo "Running $suite eval suite from the linked plugin path with a temporary evals/ staging area."
echo "Scenarios:"
print_suite_scenarios "$staged_evals"
echo "Eval mode: $variant_label"

(
  cd "$repo_root"
  tessl eval run "${variant_args[@]}" "${skill_args[@]}" "${freshness_args[@]}" "${extra_args[@]}" .
)
