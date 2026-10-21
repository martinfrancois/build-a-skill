# Writing the evals

An eval is a task plus a checklist with points. A runner gives the task to an agent twice, once
without the skill and once with it, and a model grades both answers against the checklist.

## One scenario per round

Each correction in the capture notes becomes one scenario folder in `evals-reference/`, numbered
in order, with four files (the template's three example scenarios show the exact shape):

- `task.md`: the prompt a user would type, starting with a `#` heading, with an `Assume ...`
  sentence naming the language version or environment, and a named file to produce. Ordinary
  work with the trap in it. No hint of the answer: not the pattern's name, not the shape, not
  "avoid X". Not the example from the skill's references, and not the conversation's code
  pasted in; a similar task in a different domain. Keep it the length of a real prompt: the
  class or the branch and the request, not a brief with an issue, commits and the outcome of
  the checks, which hands the grader what the agent should have produced.
- `capability.txt`: one line naming what the scenario tests.
- `criteria.json`: a Tessl `weighted_checklist` scored out of 100: 15 safety points, 80 quality
  points on the habit the skill teaches, 5 maintainability points. Put the quality points where
  the two runs will differ; a check both runs pass earns few points.
- `criteria-meta.json`: `invocation` (`natural` when the task never names the skill), `task_type`,
  `evidence_type` (`focused_reference` to start), and a category per check.

Run `python3 scripts/validate_eval_criteria.py evals evals-reference evals-regression` after each
scenario; it catches the point split, answer-key markers, and tasks copied from the references.

## Reading an eval before trusting it

- Would anyone type this prompt in real work?
- Could an agent without the skill pass it at all? If not, the eval measures whether the skill
  was loaded, not what it taught.
- Do most points go to the habit, not to formatting or file names?
- Is the task an example the skill already contains? Copying is not learning.

## Suites and promotion

- `evals-reference/` is where every scenario starts.
- `evals/` is the main suite and the only source of a lift claim. A scenario moves there when it
  scores 100 with the skill and at least 30 points lower without, by moving the folder, never by
  copying.
- `evals-regression/` holds scenarios both runs already solve, run with the skill only.

`evals/NUMBERING.md` in the template has the full rule and the table to update.

## Never

- Never edit `criteria.json` to make a run pass. An unfair criterion is fixed in its own commit
  with the reason, then both variants rerun.
- Never move a failing scenario to another suite to hide it.
- Never reweight to reach a number. The weights follow the habit, not the result.
