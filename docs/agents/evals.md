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
  - `task.md` starts with a `#` heading, contains an `Assume` sentence that names the version or
    environment (`Assume Python 3.12.`), and asks for a named file such as `settings.py` or
    `review.md`.
  - `capability.txt` is one line naming the capability under test.
  - `criteria.json` is a Tessl `weighted_checklist`: `context`, `type`, and `checklist` items with
    `name`, `description`, and `max_score`. Nothing else, so `tessl eval lint` stays clean.
  - `criteria-meta.json` holds this repository's `metadata` (`invocation`, `task_type`,
    `evidence_type`) and a `categories` map from each checklist name to `safety`, `quality`, or
    `maintainability`.
- Score each scenario out of 100: 15 safety points (the file exists, behavior is preserved), 80
  quality points (what the skill teaches), 5 maintainability points (the change stays focused).
  The validator checks the split in every scenario.
- Put the quality points where the with-skill and without-skill runs differ. A check both
  variants pass earns few points.
- `invocation` is `natural` when the prompt never names the skill and `explicit` when it says
  `Use $my-skill`. Report the two separately; only natural scenarios show that the description
  triggers the skill. The validator does not require a mix, because an explicit-only skill can
  have no natural scenarios.
- A scenario needs the skill's own text when its task or criteria use one of these phrases:
  "skill bundle", "the skill's", "as the skill says", "from the skill", or "bundled". The
  validator then requires `evidence_type: skill_context_dependent` in `evals-regression/`. If the
  scenario does not need the skill's text, reword the phrase instead of moving it.

### Suites

- `evals/` is the main suite and the only source of lift claims. Run it with both variants.
- `evals-reference/` holds candidates and broad coverage. Run it with both variants.
- `evals-regression/` holds scenarios both variants already solve, plus scenarios that need text
  only the skill contains. Run it with the skill only.
- `evidence_type` says why a scenario sits where it does: `ordinary_lift`, `focused_main`,
  `focused_reference`, `solved_regression`, or `skill_context_dependent`. The validator enforces
  which suite each value may live in.
- New scenarios start in `evals-reference/`. A scenario starts in `evals-regression/` only when
  it needs text that exists only in the skill; a reference scenario moves there once it scores 100
  both with and without the skill. Classify each one from an isolated run:

  ```bash
  tessl eval view <run-id> --json > /var/tmp/eval-run.json
  python3 scripts/classify_eval_result.py /var/tmp/eval-run.json --scenario-dir <scenario-dir>
  ```

  Promotion to `evals/` needs 100 with the skill and a delta of at least 30 percentage points.
  Move the folder rather than copy it: a main task that shares 85% or more of its eight-word runs
  with a reference or regression task fails the validator as a duplicate.
  [NUMBERING.md](../../evals/NUMBERING.md) has the full rule and the numbering scheme.

### Runtime references

- No answer keys in `skills/my-skill/references/`: no scenario names, expected outputs, rubrics,
  run IDs, or scores.
- A scenario that shares code identifiers with a runtime reference, or a run of five words with
  it anywhere in its task, capability, or criteria (code included), is not ordinary lift. The validator flags
  it; move the reference example to another domain, or classify the scenario as focused
  evidence with a written `runtime_reference_overlap_rationale`.

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
