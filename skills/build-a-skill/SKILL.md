---
name: build-a-skill
description: Builds an Agent Skill with evals out of the current conversation, once the agent has produced the code or result the user wanted after one or more corrections. It captures every correction, scaffolds a repository from a template, writes the skill and at least three evals, replays the first prompt with the skill installed to check it gets it right the first time, scores the evals with and without it, and installs the skill. Use whenever the user asks to turn this conversation, these corrections, or this fix into a skill; to make the agent stop repeating a mistake it was just corrected on; or to build, create, or extract a skill from what just happened; also when the user says the agent finally got it right and should keep doing it this way, even if they never say "skill". Not for writing a skill from scratch with no conversation behind it.
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

## Workflow

1. **Find where it started.** Locate the first prompt that produced the almost-right output: the
   task, not the first correction. Read backwards through the conversation; if the context was
   summarized or the start is older, open the session transcript on disk
   ([transcripts.md](references/transcripts.md)). Record the commit checked out before that prompt
   (`git log -1 --format=%H --before="<prompt time>"`, or the commit the transcript shows). If you
   cannot tell where it started, quote your best candidate and ask the user: "Is this the prompt
   where it started?" Do not guess.
2. **Capture every round.** For each correction between the start and now, write down: the
   code before, the prompt, what you produced, the user's correction in their words, and the
   version that stayed. Then write why the version that stayed is better, in one sentence per
   round. Keep it in `notes/capture.md` of the new repository.
3. **Choose a name and a place.** Propose a kebab-case name for the habit (`java-optionals`,
   `commit-messages`) and a directory for the new repository, by default a sibling of the current
   one. Ask once if either is unclear.
4. **Scaffold the repository.**
   - Copy [the template folder](assets/template/) from this skill's resolved path:
     `cp -r "$(readlink -f <this skill's folder>)/assets/template/." <new repository>/`. If the
     copy is refused, ask for the approval; never retype the template.
   - Run `./scripts/start_skill.sh <name>` in the new repository: it renames `skills/my-skill`,
     replaces the name in every file, deletes the example scenarios, and empties the table in
     `evals/NUMBERING.md`.
   - `git init` and commit the scaffold, so the replay and the runs have a history to compare.
5. **Write the skill.** Rewrite `skills/<name>/SKILL.md`, its references, `agents/openai.yaml`
   and `.tessl-plugin/plugin.json` from the capture notes only, as
   [writing-the-skill.md](references/writing-the-skill.md) describes, then check the draft:
   - a description in four parts: what it does, a "Use for any of" list of at least five short
     keywords, an "even if" clause, and a "Not for" clause;
   - at most two hard stops, each a whole correction;
   - every hard stop and workflow step is something the user said: delete the rest, including a
     ban on the opposite of what they asked for and any helper or style the kept version happens
     to use;
   - a numbered workflow that ends in a check;
   - every pair under "Not like this" and "Like this", with a one-sentence why.
6. **Write the evals.** In `evals-reference/`, one scenario per correction, as
   [evals.md](references/evals.md) describes: the message a user would send about their own code,
   which ships with the scenario as files, with the trap in it and no hint; a checklist whose
   points sit on the habit. Write at least three; with fewer corrections, add the same kind of
   request in another domain. In the new repository, run
   `python3 ./scripts/validate_eval_criteria.py evals evals-reference evals-regression` until it
   passes.
7. **Replay the first prompt.** In a fresh session with the new skill installed, check out the
   commit from step 1 and run the prompt from step 1 unchanged
   ([replay-and-prove.md](references/replay-and-prove.md)). Compare the result with the version
   that stayed. If it differs in the habit the skill teaches, fix the skill (never the prompt)
   and replay again.
8. **Prove it, with a stop rule** ([replay-and-prove.md](references/replay-and-prove.md)).
   - Ask the user once: screen locally first (`./scripts/local_screen.sh`, needs a DeepSeek API
     key, saves Tessl credits), or go straight to hosted Tessl runs. Follow their choice, and
     report local numbers as local screening results, never as hosted scores.
   - For hosted runs, link the repository first: `tessl project create <name> --workspace
     <workspace>` (ask the user for the workspace). Keep going past the monthly allowance; stop
     only when `tessl org usage --json` shows `credits.blocked` true or Tessl refuses a run,
     then offer the local screen.
   - If `tessl` is not logged in, or the chosen screen has no DeepSeek key, stop and tell the
     user what to set up. Never edit the scripts or swap in another model or endpoint.
   - Run `tessl review run --threshold 100 skills/<name>/SKILL.md` and fix every finding, then
     each scenario with and without the skill. Every with-skill score must reach 100 without
     leading tasks or answer keys.
   - At most three runs per scenario per change; if a run is stuck or a score does not move,
     stop and report. Promote a scenario to `evals/` only by the rule in `evals/NUMBERING.md`.
9. **Install it and report.** Link the skill into the user's agent and report as
   [replay-and-prove.md](references/replay-and-prove.md) says. It is done when the replay produced
   the version that stayed, the review scores 100, and at least three scenarios sit in `evals/` at
   100 with the skill and 30 points lower without; say which of these is still missing, and why.

## References

| File | Read it when |
|---|---|
| [transcripts.md](references/transcripts.md) | You need the session transcript on disk, or the start of the story is unclear |
| [writing-the-skill.md](references/writing-the-skill.md) | You write or revise `SKILL.md`, its description, or its references |
| [evals.md](references/evals.md) | You write a scenario, choose points, or decide which suite it belongs in |
| [replay-and-prove.md](references/replay-and-prove.md) | You replay the first prompt, run evals, or install the skill |
| `README.md` in [the template](assets/template/) | You want the same steps written for a person doing them by hand |
