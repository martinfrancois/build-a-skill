# Changelog

## 0.1.2 (2026-11-01)

### Fixes

* build-a-skill: step 5 asks for at least three short names people use for the habit in the
  description, and writing-the-skill.md says a description of what the code does is not a
  trigger word; the registry eval of 0.1.1 lost 4 points on main 01 there (96 with the skill)
* template: `docs/agents/skill-behavior.md` asks for those short names too
* changelog: the 0.1.1 entry said main 01 scores 100; that was a hosted run before the last
  edits, and the registry eval of 0.1.1 scored 96

## 0.1.1 (2026-11-01)

### Fixes

* build-a-skill: from the registry eval of 0.1.0 (96 with the skill) and two hosted runs after
  it, the second at 100 with the skill and 64 without; the registry eval of 0.1.1 scored 96
  (see 0.1.2)
  * the description lists the short names people give the pattern among its trigger words
  * the pair sits under "Not like this" and "Like this" headings, with a one-sentence why that
    restates the correction
  * at most two hard stops, each a correction the user made and nothing more; choices the
    kept version happens to make are not rules unless the user asked for them
  * the last workflow step checks that the code compiles and no longer contains what the
    correction rejected
  * the eval's class, method and field names appear nowhere in the skill, trigger words
    included
* build-a-skill: the quality review's two path warnings are gone (validation 100), and step 8
  gives the review command
* template: the example skill's `references/examples.md` uses the "Not like this" and "Like
  this" headings, and `docs/agents/skill-behavior.md` states the same hard-stop rule
* credits: a quality review costs 10 credits on CLI 0.119.0; the skill, the template and the
  README no longer call it free

## 0.1.0 (2026-10-21)

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

* evals: first hosted run, 64% without the skill and 99% with (1.54x); the Java capture
  scenario moved to the main suite (56 without, 100 with)

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
