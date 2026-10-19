# Eval Guidance

## Scope

Editing `evals/`, `evals-reference/`, `evals-regression/`, scoring rules, or any claim about how
much the skill helps.

## Rules

### Honesty

- Don't cheat. A score is only worth something if the run could have failed.
- Don't leak the fix in `task.md`. Write the prompt a user would type: the task, the version or
  environment, and the inputs. Never the diagnosis, the convention, or the shape of the answer.
- Never edit `criteria.json` to make a run pass. If a criterion is unfair (it asks for something
  the task never required, or rejects a correct answer), fix it as its own `fix(evals)` commit
  with the reason, then rerun both variants.
- Every with-skill result must reach 100 in every suite. Below 100, fix the skill and rerun that
  scenario. Do not move a failing scenario to another suite to hide it.

### Scenario format

- Each scenario folder holds four files:
  - `task.md` starts with a `#` heading, contains a line starting with `Assume` that names the
    version or environment (`Assume Python 3.12.`), and asks for a named file such as
    `settings.py` or `review.md`.
  - `capability.txt` is one line naming the capability under test.
  - `criteria.json` is a Tessl `weighted_checklist`: `context`, `type`, and `checklist` items with
    `name`, `description`, and `max_score`. Nothing else, so `tessl eval lint` stays clean.
  - `criteria-meta.json` holds this repository's `metadata` (`invocation`, `task_type`,
    `evidence_type`) and a `categories` map from each checklist name to `safety`, `quality`, or
    `maintainability`.
- Score each scenario out of 100: 15 safety points (the file exists, behavior is preserved), 80
  quality points (what the skill teaches), 5 maintainability points (the change stays focused).
- Put the quality points where the with-skill and without-skill runs differ. A check both
  variants pass earns few points.
- `invocation` is `natural` when the prompt never names the skill and `explicit` when it says
  `Use $my-skill`. Report the two separately; only natural scenarios show that the description
  triggers the skill.

### Suites

- `evals/` is the main suite and the only source of lift claims. Run it with both variants.
- `evals-reference/` holds candidates and broad coverage. Run it with both variants.
- `evals-regression/` holds scenarios both variants already solve, plus scenarios that need text
  only the skill contains. Run it with the skill only.
- `evidence_type` says why a scenario sits where it does: `ordinary_lift`, `focused_main`,
  `focused_reference`, `solved_regression`, or `skill_context_dependent`. The validator enforces
  which suite each value may live in.
- New scenarios start in `evals-reference/`. Classify each one from an isolated run:

  ```bash
  tessl eval view <run-id> --json > /var/tmp/eval-run.json
  python3 scripts/classify_eval_result.py /var/tmp/eval-run.json --scenario-dir <scenario-dir>
  ```

  Promotion to `evals/` needs 100 with the skill and a delta of at least 30 percentage points.
  [NUMBERING.md](../../evals/NUMBERING.md) has the full rule and the numbering scheme.

### Runtime references

- No answer keys in `skills/my-skill/references/`: no scenario names, expected outputs, rubrics,
  run IDs, or scores.
- A task that shares identifiers or long phrases with a runtime reference is not ordinary lift.
  The validator flags it; rewrite the task in another domain, or classify it as focused evidence
  with a written `runtime_reference_overlap_rationale`.

### Spending credits

- Freeze the skill text before measuring. Any edit to the skill or its references invalidates
  every run made before it.
- Run the quality review to 100 first, then targeted scenarios, then full suites. The order and
  commands are in [Workflow](workflow.md).
- If the baseline already scores high, check whether the task is too easy before changing the
  skill.

## References

- [Workflow](workflow.md)
- [Skill Behavior](skill-behavior.md)
