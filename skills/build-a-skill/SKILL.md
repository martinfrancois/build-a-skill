---
name: build-a-skill
description: Builds an Agent Skill with evals out of the current conversation, once the agent has produced the code or result the user wanted after one or more corrections. It writes the skill and one eval per correction, replays the first prompt with the skill installed to check it gets it right the first time, and scores the evals with and without it. Use whenever the user asks to turn this conversation, these corrections, or this fix into a skill; to make the agent remember this or stop repeating a mistake; or to build, create, or extract a skill from what just happened; also when the user says the agent finally got it right and should keep doing it this way, even if they never say "skill". Not for writing a skill from scratch with no conversation behind it.
license: MIT
---

# Build a skill from this conversation

The conversation holds everything a skill needs: the task, the almost-right output, every
correction, and the version that stayed. This skill turns that record into a skill folder with
evals, replays the first prompt to check that the skill gets it right the first time, and
proves it with runs with and without the skill.

## Hard stops

- Write the skill from what happened in this conversation, never from guesses about what else
  might go wrong. A rule without a correction behind it is speculation.
- No eval task may be an example the skill contains, and no task may hint at the answer. Never
  edit criteria to make a run pass. [evals.md](references/evals.md) has the rules.

## When to use

- The user asks to build, create, or extract a skill from this conversation or these fixes.
- The user corrected the agent at least once and now has the result they wanted.
- The user asks how to stop the agent from repeating a mistake it just made.

## Workflow

1. **Find where it started.** Locate the first prompt that produced the almost-right output: the
   task, not the first correction. Read backwards through the conversation; if the context was
   summarized or the start is older, open the session transcript on disk
   ([transcripts.md](references/transcripts.md) says where each agent keeps it). Record the
   commit that was checked out before that prompt (`git log --before` with the prompt's time, or
   the commit the transcript shows). If you cannot tell where it started, quote your best
   candidate and ask the user: "Is this the prompt where it started?" Do not guess.
2. **Capture every round.** For each correction between the start and now, write down: the
   code before, the prompt, what you produced, the user's correction in their words, and the
   version that stayed. Then write why the version that stayed is better, in one sentence per
   round. This is the material for the skill and for the evals; keep it in `notes/capture.md`
   of the new repository.
3. **Choose a name and a place.** Propose a kebab-case name for the habit (`java-optionals`,
   `error-messages`) and a directory for the new repository, by default a sibling of the current
   one. Ask once if either is unclear.
4. **Scaffold the repository.** Copy everything under [assets/template/](assets/template/) into
   that directory with `cp -r`, from the resolved path of this skill (`readlink -f`), because an
   installed skill is usually a symlink to a folder outside the working directory and the agent
   may need the user's approval for that path. If the copy is refused, ask for the approval;
   never retype the template by hand, which loses file modes and invites typos. Then rename
   `skills/my-skill` to `skills/<name>`, replace every `my-skill` in `tessl.json`,
   `.tessl-plugin/plugin.json`, `README.md`, and `scripts/` with the name, delete the three
   example scenarios, keep `evals/NUMBERING.md` with an empty table, and make the first commit
   (`git init`, then commit the scaffold) so the replay and the runs have a history to compare.
5. **Write the skill.** Rewrite `skills/<name>/SKILL.md` from the capture notes only, following
   [writing-the-skill.md](references/writing-the-skill.md): a description that names the task
   and the words a user would type when it should fire, one or two hard stops, a numbered
   workflow that ends in a check, and references that hold each round as a pair: not like this,
   like this, and why. Fill `agents/openai.yaml` and `.tessl-plugin/plugin.json`.
6. **Write one eval per round.** In `evals-reference/`, one scenario per correction, as
   [evals.md](references/evals.md) describes: a task someone would type, with the trap in it and
   no hint; a checklist whose points sit on the habit. Run
   `python3 scripts/validate_eval_criteria.py evals evals-reference evals-regression` until it
   passes.
7. **Replay the first prompt.** In a fresh session with the new skill installed, check out the
   commit from step 1 and run the prompt from step 1 unchanged. Compare the result with the
   version that stayed. If it differs in the habit the skill teaches, fix the skill (never the
   prompt) and replay again. [replay-and-prove.md](references/replay-and-prove.md) has the exact
   steps for each agent.
8. **Prove it, with a stop rule.** Link the repository to a tessl project first
   (`tessl project create <name> --workspace <workspace>`; ask the user for the workspace), or
   the hosted runs fail after the local checks pass. Run the quality review to 100 (free), then
   each scenario with and without the skill. Before the first eval run, read
   `tessl org usage --json`: if `credits.overLimit` is true or `credits.remaining` is below the
   run's estimate, do not run it even if Tessl would accept it, and do not try another
   workspace: run the local screen instead, `scripts/local_screen.sh` in the
   new repository, both arms (its `docs/agents/local-screening.md` has the setup; it needs a
   DeepSeek API key in `~/deepseek-api-key`, and asks the user for one if the file is missing),
   and report its numbers as local screening results, never as hosted scores. Every with-skill score must reach 100 without leading tasks or answer keys.
   At most three runs per scenario per change; if a run is stuck or a score does not move, stop
   and report instead of retrying. Promote a scenario to `evals/` only by the rule in
   `evals/NUMBERING.md`.
9. **Install it and report.** Link the skill into the user's agent
   ([replay-and-prove.md](references/replay-and-prove.md) has the commands), then tell the user:
   where the repository is, the first prompt and commit you replayed, what the replay produced,
   the scores both ways, and anything you had to ask or assume.

The task is done when the replay produces the version that stayed, every with-skill scenario
scores 100, the validator passes, and the skill is installed.

## References

| File | Read it when |
|---|---|
| [transcripts.md](references/transcripts.md) | You need the session transcript on disk, or the start of the story is unclear |
| [writing-the-skill.md](references/writing-the-skill.md) | You write or revise `SKILL.md`, its description, or its references |
| [evals.md](references/evals.md) | You write a scenario, choose points, or decide which suite it belongs in |
| [replay-and-prove.md](references/replay-and-prove.md) | You replay the first prompt, run evals, or install the skill |
| [assets/template/README.md](assets/template/README.md) | You want the same steps written for a person doing them by hand |
