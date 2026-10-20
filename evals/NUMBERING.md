# Scenario numbering

## How numbers work

- `evals/` scenarios are numbered in the order they entered the main suite. A main number is
  never reused, so `01` stays `01` even after later scenarios join.
- `evals-reference/` and `evals-regression/` share one number space. A scenario keeps its number
  when it moves between them, which is why the starter regression scenario is `02`: number `01`
  is the reference scenario, and regression starts where reference left off.
- Gaps are allowed. When a scenario is deleted or moves out of a folder, add one line under
  [Gaps](#gaps) saying which number left, where it went, and why, with the number in backticks,
  for example "Reference `03` was deleted because the main suite covers it."
  That section is the only place for those notes, for all three suites; the validator fails on
  any gap whose number it does not list.

## Promotion rule

A new scenario starts in `evals-reference/`, or in `evals-regression/` if it can only be solved
with text that exists only in the skill. It moves to `evals/` only when both hold:

1. With the skill, it scores 100. Every scenario in `evals/` must keep scoring 100 with the skill;
   a main scenario that drops below 100 means the skill or the scenario needs fixing before any
   lift number is reported.
2. Without the skill, it scores at least 30 points lower, so the delta is 30 percentage points or
   more.

A scenario that scores 100 both with and without the skill moves to `evals-regression/`. Run
`scripts/classify_eval_result.py` on the run JSON to get the recommendation for one scenario.

## Gaps

None yet.

## Current numbers

| Suite | Number | Scenario |
|---|---|---|
| main | 01 | `evals/01-settings-loader-errors` |
| reference | 01 | `evals-reference/01-webhook-error-review` |
| regression | 02 | `evals-regression/02-hard-stop-audit` |
