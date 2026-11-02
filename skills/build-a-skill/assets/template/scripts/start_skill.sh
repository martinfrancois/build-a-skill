#!/usr/bin/env bash
# Turns a fresh copy of this template into the repository of one skill, in one step: renames the
# example skill folder, replaces the example name in every text file, deletes the example
# scenarios, and empties the table in evals/NUMBERING.md. Run it once, right after the copy.
set -euo pipefail

usage() {
  echo "Usage: scripts/start_skill.sh <kebab-case-name>" >&2
}

example="my-skill"
name="${1:-}"
if [[ ! "$name" =~ ^[a-z0-9]+(-[a-z0-9]+)*$ ]]; then
  usage
  exit 2
fi
repo="$(cd "$(dirname "$0")/.." && pwd -P)"
cd "$repo"
if [[ ! -d "skills/$example" ]]; then
  echo "skills/$example not found; this copy was already started." >&2
  exit 1
fi

mv "skills/$example" "skills/$name"
# Every text file except this script and git's own; -i.bak keeps the sed call portable to macOS.
grep -rlI --exclude-dir=.git --exclude=start_skill.sh -e "$example" . | while IFS= read -r file; do
  sed -i.bak "s/$example/$name/g" "$file"
  rm "$file.bak"
done

for suite in evals evals-reference evals-regression; do
  for scenario in "$suite"/*/; do
    if [[ -d "$scenario" ]]; then
      rm -r "${scenario:?}"
    fi
  done
  mkdir -p "$suite"
  touch "$suite/.gitkeep"
done
# Keep the table header in NUMBERING.md and drop the rows for the deleted examples.
sed -i.bak -E '/^\| (main|reference|regression) \| [0-9]+ \|/d' evals/NUMBERING.md
rm evals/NUMBERING.md.bak

echo "Started skills/$name. Next: write SKILL.md, its references, agents/openai.yaml and"
echo ".tessl-plugin/plugin.json, then the eval scenarios in evals-reference/."
