# Workflow

## Scope

Changing the `build-a-skill` skill, its references, or the template it copies.

## Rules

- The skill is written for an agent that has just produced the result the user wanted and is
  told to turn the conversation into a skill. Every step must be doable by Claude Code and Codex
  with their ordinary tools, and must say what to do when another agent lacks something (ask
  the user). Agent-specific paths and commands live only in `references/transcripts.md` and
  `references/replay-and-prove.md`.
- The skill never guesses where the story started: when the first prompt cannot be found, it
  asks the user, as `references/transcripts.md` says. Keep that rule.
- Keep `SKILL.md` under about 120 lines; detail goes to `references/`. The description is the
  trigger: third person, what it does, then the situations and the words a user would type.
- The template under `assets/template/` is a complete repository: its own `README.md`,
  `AGENTS.md` rules under `docs/agents/`, three example scenarios, the scripts, and the
  manifests. A change to how a produced repository should work goes into the template, not into
  the skill text.
- Local checks before committing, all free:

  ```bash
  tessl skill lint .
  tessl plugin lint .
  python3 -m py_compile skills/build-a-skill/assets/template/scripts/*.py
  bash -n skills/build-a-skill/assets/template/scripts/*.sh
  (cd skills/build-a-skill/assets/template && python3 scripts/validate_eval_criteria.py evals evals-reference evals-regression)
  (cd skills/build-a-skill/assets/template && for suite in evals evals-reference evals-regression; do tessl eval lint "$suite"; done)
  ```

- Commits and pull request titles use Conventional Commits: `feat(skill)` or `fix(skill)` for
  the skill text and references, `feat(template)` or `fix(template)` for the template, `docs`
  for text that changes neither.
