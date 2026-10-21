# Scenario numbering

## How numbers work

- `evals/` scenarios are numbered in the order they entered the main suite. A main number is
  never reused.
- `evals-reference/` and `evals-regression/` share one number space. A scenario keeps its number
  when it moves between them, so a regression scenario that came from reference still has its
  reference number.
- Gaps are allowed. When a scenario is deleted or moves out of a folder, add one line under
  [Gaps](#gaps) in the form `- <suite> <NN>: deleted, <reason>`, naming the suite the number
  left, for example `- evals-reference 03: deleted, the main suite covers it`. The validator
  fails on a gap without such a note, on a note in any other form, on a note that names another
  suite than the one git history last shows the number in, and on a note for a number that any
  suite of the same number space uses again.

## Promotion rule

New scenarios start in `evals-reference/`. A scenario starts in `evals-regression/` only when it
needs text that exists only in the skill. A reference scenario moves to `evals-regression/` once
it scores 100 both with and without the skill, and to `evals/` only when both hold:

1. With the skill, it scores 100. Every scenario in `evals/` must keep scoring 100 with the skill;
   a main scenario that drops below 100 means the skill or the scenario needs fixing before any
   lift number is reported.
2. Without the skill, it scores at least 30 points lower, so the delta is 30 percentage points or
   more.

Move the folder rather than copy it: a main `task.md` that shares 85% or more of its eight-word
runs with a reference or regression task fails the validator as a duplicate. Run
`scripts/classify_eval_result.py` on the run JSON to get the recommendation for one scenario.

## Gaps

None yet.

## Current numbers

Update this table whenever a scenario is added, moved, or deleted. The validator flags a row whose
folder no longer exists.

| Suite | Number | Scenario |
|---|---|---|
| main | 01 | `evals/01-settings-loader-errors` |
| reference | 01 | `evals-reference/01-webhook-error-review` |
| regression | 02 | `evals-regression/02-hard-stop-audit` |

## Local screening results (2026-10-21)

From `scripts/local_screen.sh` (DeepSeek V4.1 Flash as the solver, a Claude Haiku judge); not
hosted evidence. Two runs per arm on the skill as merged in PR 4, then three runs of the skill
arm after the tuning in the same pull request as these evals ("not for" clause in the
description, a read-back that deletes rules without a correction, eval tasks kept short).

| Scenario | Without the skill | With the skill, before tuning | With the skill, after tuning |
| --- | --- | --- | --- |
| reference 01 (Java upsert capture) | 57, 59 | 85, 86 | 86 to 95, mean 91 |
| reference 02 (pull request description capture) | 74, 73 | 82, 86 | 78 to 96, mean 87 |

What the solver loses without the skill: rules no correction supports, an eval in the
conversation's own domain, an imperative description, no check at the end of the workflow.
What it still loses with the skill: a rule or two beyond the correction (`orElseGet` over
`orElse`), an eval task written as a brief, and judge strictness on the `license` line. Both
stay in reference until the skill arm reaches 100 on the hosted run.

## Quality review (2026-10-21)

`tessl review run --force`, free since CLI 0.117.0: 95 (content 100, description 91), then 98
after the description named the replay and the scoring and gained a "not for" clause (content
100, description 100). The last 2 points are two validation warnings for paths that exist only
in the repository the skill generates (`skills/<name>/SKILL.md` and its local screening doc) and
links one level deeper than the reviewer expects (`assets/template/`). Rewording them away cost
7 content points (96), so the paths stay.
