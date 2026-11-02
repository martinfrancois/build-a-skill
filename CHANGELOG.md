# Changelog

## 1.0.0 (2026-11-02)

### Features

* build-a-skill: writes at least three eval scenarios, one or more per correction, and finishes
  only when the review scores 100 and at least three scenarios sit in the main suite at 100 with
  the skill and 30 points lower without; the Tessl registry gives a full aggregate score only to
  a main suite of three or more
* build-a-skill: the evals it writes are realistic: the task is the message a user would send
  about their own code, and that code ships with the scenario as a directory fixture in
  `scenario.json`, with a `setup.sh` for git history, instead of being pasted into the prompt
* build-a-skill: before the first hosted run it asks once whether to screen locally first with
  DeepSeek V4.1 Flash, which saves Tessl credits, or to go straight to hosted runs, and follows
  the answer; hosted runs go on past the monthly allowance and stop only when Tessl blocks them
* template: `scripts/start_skill.sh <name>` renames the example skill, deletes the example
  scenarios and empties the numbering table in one step
* template: the repository it produces has an `AGENTS.md`, and a `CLAUDE.md` that imports it,
  linking the rule pages, so agents find the credit policy and the local screening method
* template: the local screen installs a scenario's fixtures and runs its setup scripts the way
  Tessl does, and the validator accepts shipped project files in place of an `Assume` sentence
* evals: every scenario now replays a real session: the project on disk with its git history as
  the session left it, the earlier turns, and the user's request for a skill; two new scenarios
  (Python with two corrections about writing files, TypeScript) and three in the main suite

### Fixes

* build-a-skill: a hard stop states the whole correction, what it rejected and what it asked
  for; every rule is something the user said, so a helper the kept version happens to use or a
  ban on the opposite of the request is not a rule; the description has four parts, with a
  "Use for any of" list of at least five short keywords
* build-a-skill: its own examples of trigger words come from a habit no eval tests, and
  neither its SKILL.md nor the skills it writes carry a "When to use" section, which repeated
  the description
* build-a-skill: the replay runs under `timeout 600`; with no Tessl login, or no DeepSeek key
  for a chosen local screen, it stops and asks the user, and never edits the scripts or swaps in
  another model
* template: the local screen's judge reads its prompt from stdin; a copied template made the
  prompt too long for one command-line argument
* template: the local screen keeps fixture paths inside the work directory, copies no symlinks,
  and runs a scenario's setup scripts only with `-x`, in an empty environment
* template: `run_eval_suite.sh` refuses a second run in the same checkout, which uploaded the
  other run's staged scenarios
* template: the example skill's pair uses the "Not like this" and "Like this" headings, and the
  local screening doc no longer carries another repository's scores as if they were its own

## 0.1.3 (2026-11-02)

### Fixes

* build-a-skill: a leaner SKILL.md body that reviews at 100: the intro no longer restates the
  description, step 4 is four bullets, step 5 is a checklist the agent runs against its draft,
  and the reference pointers lost their repeated phrasing

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
