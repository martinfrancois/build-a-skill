# Workflow

## Scope

Day-to-day work in this repository: changing the skill or evals, validating, committing, and
opening pull requests.

## Rules

- Before a change, state its goal as something a run can confirm, for example "scenario 01
  scores 100 with the skill and at most 70 without". A change without a measurable goal has no
  way to finish.
- Before committing changes to the skill, evals, or scripts, run the local checks. They are free:

  ```bash
  python3 scripts/validate_eval_criteria.py evals evals-reference evals-regression
  python3 -m py_compile scripts/*.py
  bash -n scripts/*.sh
  tessl skill lint .
  tessl plugin lint .
  for suite in evals evals-reference evals-regression; do tessl eval lint "$suite"; done
  ```

- Hosted runs cost Tessl credits. Spend them in this order and stop at the first stage that is
  not clean:
  1. Quality review at 100:
     `tessl review run --threshold 100 skills/my-skill/SKILL.md`. Fix every finding before any
     eval run.
  2. Freeze the skill text. Every run measures the exact `SKILL.md` and references it was given,
     so finish the wording first and do a local read of each affected `task.md` and
     `criteria.json` against it.
  3. Targeted runs of the scenarios the change affects:
     `scripts/run_eval_suite.sh <suite> <scenario-name>`.
  4. The full main suite, then reference, then regression:
     `scripts/run_eval_suite.sh main`, `reference`, `regression`.
- Any edit to `SKILL.md` or a file under `skills/my-skill/references/` invalidates every earlier
  run. Results from before the edit are history, not evidence for the current text.
- A with-skill score below 100 sends you back to stage 3 for that scenario only, after fixing
  the skill. Do not rerun a broad suite to fix one scenario.
- If a hosted run looks stuck, keep polling it with `tessl eval view <run-id>`. Scoring can lag
  behind execution. Rerun only after a scored failure and a fix.
- Commits and pull request titles use Conventional Commits: `fix(skill)` or `feat(skill)` for
  runtime skill text, `test(evals)` for adding or moving scenarios, `fix(evals)` for correcting
  an unfair task or criterion, `docs` for text that changes neither.
- Put any change that can move a score (skill text, references, active tasks, criteria, or
  suite membership) in its own commit, so it can be reverted alone.

## References

- [Eval Guidance](evals.md)
- [Skill Behavior](skill-behavior.md)
