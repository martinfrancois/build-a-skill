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

- evals-reference 01: deleted, moved to `evals/` as main 01 after the hosted run of 2026-10-21 (56 without the skill, 100 with)

## Current numbers

Update this table whenever a scenario is added, moved, or deleted. The validator flags a row whose
folder no longer exists.

| Suite | Number | Scenario |
|---|---|---|
| main | 01 | `evals/01-java-upsert-capture` |
| reference | 02 | `evals-reference/02-pull-request-description-capture` |

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

## Hosted run (2026-10-21)

Run `01a1602a-f150-7319-89ed-0f77710fafb9`, the Tessl default solver, both arms, 45 credits,
against the skill as of PR 10 (review 98).

| Scenario | Without the skill | With the skill | Placement |
| --- | --- | --- | --- |
| 01 Java upsert capture | 56 | 100 | main: 44 points under 100 without, 100 with |
| 02 pull request description capture | 73 | 99 | stays reference: 27 points under, and 99 with |

The suite as a whole: 64% without, 99% with, a lift of 1.54x (199 over 129). Without the skill
the solver loses on its own rules: invented rules beyond the correction (eight numbered rules
for a one-line correction), no numbered workflow ending in a check, and an eval in the
conversation's own domain, in 02 the very same rate-limiter change. With the skill, 02 lost one
point on the description's trigger words. The local screen had predicted 58 and 74 without,
91 and 87 with; it underestimated the skill arm by about 10 points.
