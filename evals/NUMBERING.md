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
- evals-reference 02: deleted, moved to `evals/` as main 02 after the hosted runs of 2026-11-02 (25 without the skill, 100 with)
- evals-reference 03: deleted, moved to `evals/` as main 03 after the hosted runs of 2026-11-02 (21 without the skill, 100 with)

## Current numbers

Update this table whenever a scenario is added, moved, or deleted. The validator flags a row whose
folder no longer exists.

| Suite | Number | Scenario |
|---|---|---|
| main | 01 | `evals/01-java-upsert-capture` |
| main | 02 | `evals/02-pull-request-description-capture` |
| main | 03 | `evals/03-python-file-writes-two-rounds` |
| reference | 04 | `evals-reference/04-typescript-unknown-json-capture` |

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

## Registry eval of 0.1.0 and the 0.1.1 fixes (2026-11-01)

The registry eval of 0.1.0, run `01a1603f-47e8-729b-a7a3-f1b0b48c4986`, scored main 01 at 56
without the skill and 96 with it. With the skill it lost 2 points on trigger words (no short
names for the pattern) and 2 on the pair (inline labels instead of headings, a why of several
sentences).

| Run | Skill text | Without | With | What the with-skill run lost |
| --- | --- | --- | --- | --- |
| `01a198fb-416f-76d8-9d75-79f0a97b3e19` | trigger names, pair headings | 61 | 95 | a second, invented hard stop; the skill's trigger words included the eval's method name |
| `01a19902-5437-7585-94a2-e49f3b5e891d` | one hard stop per correction, eval names kept out of the skill | 64 | 100 | nothing |

Local screen of main 01 with the skill, three runs each: 96, 93, 86 on 0.1.0; 96, 99, 97 after
the first fixes; 97, 97, 98 after the second.

Quality review after the path fixes: validation 100 (it was 15 of 16 checks), description 100,
content 92.5, 97 overall. Content scored 100, 92.5, 85 and 92.5 on four reviews of nearly the
same body. A review costs 10 credits on CLI 0.119.0.

The registry eval of 0.1.1, run `01a19934-4fad-7665-94b8-e93b96417886`, scored main 01 at 64
without the skill and 96 with it, 4 points lost on trigger words: the description listed
situations in code terms instead of the names a user would type. 0.1.2 asks for at least three
such names in step 5. Local screen with the skill on 0.1.2: 99, 98, 98.

The registry eval of 0.1.2, run `01a1993d-ed11-728b-bf66-4ded8f4a9ed0`, scored main 01 at 64
without the skill and 100 with it; its publish review gave 97. 0.1.3 rewrites the SKILL.md body
more tightly, with the same steps and guards, and reviewed at 100 twice. Local screen with the
skill on 0.1.3: 98, 97, 97.

## Realistic scenarios and three main scenarios for 1.0.0 (2026-11-02)

The registry listing gives a full aggregate score only to a main suite of three or more, and
0.1.3 had one. Two scenarios were added (03, Python with two corrections; 04, TypeScript), and
all four were rebuilt as real sessions: the project ships as a directory fixture, `setup.sh`
rebuilds its git state as the session left it (the accepted version uncommitted, or for 02 a
branch with the change to describe), and `task.md` holds the earlier turns and the user's
request for a skill, with no list of files to write. The first hosted runs of that shape failed in setup, because Tessl uploads only declared
scenario files; `setup.sh` now writes the accepted version itself.

Hosted runs on the realistic scenarios, without the skill / with it. Each round follows a change
to the skill text named in the last column; the quality review scored 100 before each round
except f (97).

| Round | 01 | 02 | 03 | 04 | Skill change before the round |
| --- | --- | --- | --- | --- | --- |
| b | 34 / 97 | 39 / 95 | 22 / 96 | 35 / 96 | evals ship code as fixtures |
| c | 27 / 100 | 39 / 96 | 23 / 98 | 33 / 94 | three short trigger names, same kind of request |
| d | 30 / 100 | 36 / 98 | 27 / timeout | 34 / 98 | whole correction as the hard stop |
| e | 22 / 100 | 26 / 100 | 24 / 97 | 30 / 98 | `start_skill.sh`, replay time limit, no `tessl login` |
| f | 34 / 100 | 33 / 99 | 25 / timeout | 40 / 94 | trigger names as a plain list, short prompts |
| g | 24 / 97 | 35 / 100 | 29 / 96 | 29 / 96 | same language as the conversation |
| h | 33 / 96 | 35 / 98 | 25 / 93 | 27 / 99 | examples from a habit no eval tests |
| i | 28 / 100 | 31 / 100 | 22 / 98 | 28 / 96 | stop when no login or key; "Use for any of" list |
| j | 30 / 100 | | 30 / 100 | 33 / 96 | every rule something the user said |
| k | 31 / 100 | 25 / 100 | 21 / 100 | | 03 rebuilt on a habit the template does not teach; ask local screen or hosted first, run past the allowance |
| l | 31 / 100 | 43 / 100 | 29 / 93 | | the local screen confines fixture paths and runs setup scripts only with `-x` (review 97) |
| m | 31 / 100 | 27 / 100 | 20 / 100 | | step 8 names no model or price (review 100) |

The two timeouts hit Tessl's 30-minute solve limit; in round h a run took 27 minutes because the
agent patched `local_screen.sh` to use its own Claude credentials and screened twelve runs. The
skill now stops and asks when there is no login or key.

Until round j, 03 was a session about error messages, the habit the template's example skill
teaches, so the copied template carried part of its answer. Round k ran it rebuilt on two
corrections about writing files (pass an encoding, write beside the file and swap it in).

Placement: 01, 02 and 03 form the main suite, all three at 100 with the skill in rounds k and m,
round m on the text this release ships, and 69, 73 and 80 points lower without it there. In
round l, 03 lost 7 points with the skill on trigger words, an encoding rule stretched to reads,
and a faint hint in one eval task, so its 100 is not yet stable. 04 meets the delta in every
round but scored 94 to 99 with the skill, so it stays in reference until a fix holds it at 100.

Local screen of round k's text (DeepSeek V4.1 Flash, Haiku judge), two runs each: 03 at 25 and
20 without the skill, 89 and 88 with it; 02 at 93 and 92 with it. The skill arm came out about
ten points under the hosted run, as in October.
