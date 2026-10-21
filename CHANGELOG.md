# Changelog

## 0.1.0 (unreleased)

### Features

* build-a-skill: a skill that turns the conversation it is invoked in into a new skill with
  evals, replays the first prompt, and proves the result; the former starter is its template
* skill starter: `my-skill` with an example error message convention, its references, and Codex
  display metadata
* evals: one main, one reference, and one regression scenario, with numbering and promotion rules
* scripts: suite runner, criteria validator, and result classifier for Tessl evals
* agent docs: workflow, eval, skill behavior, and doc maintenance rules

* template: `scripts/local_screen.sh` and its judge, which run the scenarios locally against
  the model behind Tessl's default solver for a cent a run when the credits are used up, with
  `docs/agents/local-screening.md`; the skill falls back to it in the prove step

### Fixes

* build-a-skill: copy the template from the skill's resolved path and never retype it, make
  the first commit after scaffolding, and link the repository to a tessl project before the
  first hosted run; found on the first end-to-end trial, 2026-10-21
