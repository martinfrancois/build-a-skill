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

* evals: two reference scenarios for this skill itself (a Java capture and a pull request
  description capture in, a skill folder out), with the template's scripts linked at the root
  and local screening results in `evals/NUMBERING.md`

### Fixes

* credits: the allowance is 1,000 credits per calendar month, not per day; the "Daily eval
  usage" line is a separate attempt cap. The skill and the template check
  `tessl org usage --json` before a hosted eval run and switch to the local screen when the
  account is over the allowance, even though Tessl may still accept the run; the quality
  review is free since CLI 0.117.0
* build-a-skill: in the Codex sandbox the nested replay, the worktree and the install symlink
  are refused; the skill now hands the user the exact command instead of skipping the step;
  from the first Codex trial, 2026-10-21
* build-a-skill: the description ends with what the skill is not for, the skill is read back
  against the capture and every rule without a correction deleted, and eval tasks stay the
  length of a real prompt; from the first local screen of the skill's own evals, 2026-10-21
* build-a-skill: copy the template from the skill's resolved path and never retype it, make
  the first commit after scaffolding, and link the repository to a tessl project before the
  first hosted run; found on the first end-to-end trial, 2026-10-21
