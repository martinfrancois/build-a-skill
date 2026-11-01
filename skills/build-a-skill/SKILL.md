---
name: build-a-skill
description: Builds an Agent Skill with evals out of the current conversation, once the agent has produced the code or result the user wanted after one or more corrections. It writes the skill and one eval per correction, replays the first prompt with the skill installed to check it gets it right the first time, and scores the evals with and without it. Use whenever the user asks to turn this conversation, these corrections, or this fix into a skill; to make the agent remember this or stop repeating a mistake; or to build, create, or extract a skill from what just happened; also when the user says the agent finally got it right and should keep doing it this way, even if they never say "skill". Not for writing a skill from scratch with no conversation behind it.
license: MIT
---

# Build a skill from this conversation

The conversation holds everything a skill needs: the task, the almost-right output, every
correction, and the version that stayed. Run this while those rounds are still in the
conversation or its transcript.

## Hard stops

- Write the skill from what happened in this conversation, never from guesses about what else
  might go wrong. A rule without a correction behind it is speculation.
- No eval task may be an example the skill contains, and no task may hint at the answer. Never
  edit criteria to make a run pass ([evals.md](references/evals.md)).

## When to use

- The user asks to build, create, or extract a skill from this conversation or these fixes.
- The user corrected the agent at least once and now has the result they wanted.
- The user asks how to stop the agent from repeating a mistake it just made.

## Workflow

1. **Find where it started.** Locate the first prompt that produced the almost-right output: the
   task, not the first correction. Read backwards through the conversation; if the context was
   summarized or the start is older, open the session transcript on disk
   ([transcripts.md](references/transcripts.md)). Record the commit checked out before that
   prompt (`git log --before` with the prompt's time, or the commit the transcript shows). If
   you cannot tell where it started, quote your best candidate and ask the user: "Is this the
   prompt where it started?" Do not guess.
2. **Capture every round.** For each correction between the start and now, write down: the
   code before, the prompt, what you produced, the user's correction in their words, and the
   version that stayed. Then write why the version that stayed is better, in one sentence per
   round. Keep it in `notes/capture.md` of the new repository.
3. **Choose a name and a place.** Propose a kebab-case name for the habit (`java-optionals`,
   `error-messages`) and a directory for the new repository, by default a sibling of the current
   one. Ask once if either is unclear.
4. **Scaffold the repository.**
   - `cp -r` everything under [the template folder](assets/template/) into that directory, from
     this skill's resolved path (`readlink -f`). If the copy is refused, ask for the approval;
     never retype the template.
   - Rename `skills/my-skill` to `skills/<name>` and replace every `my-skill` in `tessl.json`,
     `.tessl-plugin/plugin.json`, `README.md`, and `scripts/`.
   - Delete the three example scenarios; keep `evals/NUMBERING.md` with an empty table.
   - `git init` and commit the scaffold, so the replay and the runs have a history to compare.
5. **Write the skill.** Rewrite `skills/<name>/SKILL.md`, its references, `agents/openai.yaml`
   and `.tessl-plugin/plugin.json` from the capture notes only, as
   [writing-the-skill.md](references/writing-the-skill.md) describes, then check the draft:
   - the description has at least three short names people use for the habit, not only a
     description of the code;
   - each hard stop is a correction the user made, two at most;
   - the workflow is numbered and its last step is a check the agent can tell is done;
   - every pair sits under "Not like this" and "Like this", with a one-sentence why.
6. **Write one eval per round.** In `evals-reference/`, one scenario per correction, as
   [evals.md](references/evals.md) describes: a task someone would type, with the trap in it and
   no hint; a checklist whose points sit on the habit. In the new repository, run
   `python3 ./scripts/validate_eval_criteria.py evals evals-reference evals-regression` until it
   passes.
7. **Replay the first prompt.** In a fresh session with the new skill installed, check out the
   commit from step 1 and run the prompt from step 1 unchanged
   ([replay-and-prove.md](references/replay-and-prove.md)). Compare the result with the version
   that stayed. If it differs in the habit the skill teaches, fix the skill (never the prompt)
   and replay again.
8. **Prove it, with a stop rule** ([replay-and-prove.md](references/replay-and-prove.md)).
   - Link the repository first: `tessl project create <name> --workspace <workspace>` (ask the
     user for the workspace), or every hosted run fails.
   - Before every hosted run, the review included, read `tessl org usage --json`. If
     `credits.overLimit` is true or `credits.remaining` is below the run's estimate, do not try
     another workspace: run `./scripts/local_screen.sh` in the new repository instead, both
     arms, and report its numbers as local screening results, never as hosted scores.
   - Run `tessl review run --threshold 100 skills/<name>/SKILL.md` and fix every finding, then
     each scenario with and without the skill. Every with-skill score must reach 100 without
     leading tasks or answer keys.
   - At most three runs per scenario per change; if a run is stuck or a score does not move,
     stop and report. Promote a scenario to `evals/` only by the rule in `evals/NUMBERING.md`.
9. **Install it and report.** Link the skill into the user's agent
   ([replay-and-prove.md](references/replay-and-prove.md)), then tell the user: where the
   repository is, the first prompt and commit you replayed, what the replay produced, the scores
   both ways, and anything you had to ask or assume.

The task is done when the replay produces the version that stayed, every with-skill scenario
scores 100, the validator passes, and the skill is installed.

## References

| File | Read it when |
|---|---|
| [transcripts.md](references/transcripts.md) | You need the session transcript on disk, or the start of the story is unclear |
| [writing-the-skill.md](references/writing-the-skill.md) | You write or revise `SKILL.md`, its description, or its references |
| [evals.md](references/evals.md) | You write a scenario, choose points, or decide which suite it belongs in |
| [replay-and-prove.md](references/replay-and-prove.md) | You replay the first prompt, run evals, or install the skill |
| `README.md` in [the template](assets/template/) | You want the same steps written for a person doing them by hand |
