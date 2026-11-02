# Writing the evals

An eval is a task plus a checklist with points. A runner gives the task to an agent twice, once
without the skill and once with it, and a model grades both answers against the checklist.

## One scenario per round

Each correction in the capture notes becomes one scenario folder in `evals-reference/`, numbered
in order, with these files:

- `task.md`: the message a user would send about their own code, in their words: "Add a method
  that ... to `Cart`", "Review the error handling in `webhook.py`", "Write the migration for the
  new `archived` column". Ordinary work with the trap in it, as close to how the habit came up in
  the conversation as another domain allows, and as short and plain as the conversation's first
  prompt: one or two sentences naming the file and the change, not a specification.
- The code the task works on ships with the scenario as files, the way it would sit on the
  user's disk, never pasted into the prompt. Put it in a folder beside `task.md` and declare it
  in `scenario.json` as a directory fixture:

  ```json
  {"fixtures": {"project": {"type": "directory", "path": "./project", "installPath": "shop"}}}
  ```

  When the task needs git history, such as a branch to describe or a change to review, add a
  `setup.sh` beside it: Tessl runs it in the working directory after installing the fixture.
  Tessl uploads only the declared files, so `setup.sh` writes any later version of a file
  itself, with a heredoc, instead of copying it from the scenario folder.
  The project's own files (`pom.xml`, `pyproject.toml`, `tsconfig.json`) set the language
  version; only a task that ships no files needs an `Assume ...` sentence.
- No hint of the answer in `task.md`: not the pattern's name, not the shape, not "avoid X", not
  the skill's name, no sentence on the quality the habit delivers, such as that a failure must
  be easy to diagnose or that bad input must be rejected, and no requirement on the part of the
  code the habit governs, such as what a message must name or how a value is typed. Nothing a
  user would not type either: no list of requirements, no list of files to write, no "do not
  run anything".
- Not the example from the skill's references, and not the conversation's code; a similar task
  in a different domain, which changes what the code is about and where its input comes from,
  not only its names. Keep the conversation's language and version: a TypeScript correction
  gets TypeScript evals. Its class, method and field names appear nowhere in the skill, not even in
  a list of trigger words; search the skill folder for each one before you save.
- `capability.txt`: one line naming what the scenario tests.
- `criteria.json`: a Tessl `weighted_checklist` scored out of 100: 15 safety points, 80 quality
  points on the habit the skill teaches, 5 maintainability points. More than half of all points
  go to the one correction the scenario tests; give compiling or behavior and scope a few of the
  quality points in their own items. Put the quality points where
  the two runs will differ; a check both runs pass earns few points.
- `criteria-meta.json`: `invocation` (`natural` when the task never names the skill), `task_type`,
  `evidence_type` (`focused_reference` to start), and a category per check.

Write at least three scenarios, even for a single correction. A published listing on the Tessl
registry shows Quality (the review), Impact (the main suite) and an aggregate score, and the
aggregate stays below 100 while `evals/` holds fewer than three scenarios. With fewer than three
corrections, add scenarios that make the same kind of request as the conversation in another
domain, such as a second class to add the method to or a different file to write. Keep the kind
of request: a conversation where the user asked for code gives requests for code, not code
reviews. Each extra scenario still tests a correction from the capture notes, never a rule the
conversation lacks.

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
  copying. Keep at least three scenarios there.
- `evals-regression/` holds scenarios both runs already solve, run with the skill only.

`evals/NUMBERING.md` in the template has the full rule and the table to update.

## Never

- Never edit `criteria.json` to make a run pass. An unfair criterion is fixed in its own commit
  with the reason, then both variants rerun.
- Never move a failing scenario to another suite to hide it.
- Never reweight to reach a number. The weights follow the habit, not the result.
