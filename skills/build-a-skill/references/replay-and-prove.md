# Replay, prove, install

## Install the new skill

A symlink keeps the installed skill in step with the repository.

```bash
# Claude Code
mkdir -p ~/.claude/skills && ln -s "$REPO/skills/$NAME" ~/.claude/skills/$NAME
# Codex
mkdir -p ~/.agents/skills && ln -s "$REPO/skills/$NAME" ~/.agents/skills/$NAME
```

For another agent, ask the user where it reads skills from; the folder follows the Agent Skills
specification and needs no change.

## Replay the first prompt

The goal of the skill is to get the first pass right, without the rounds. So the test is the
first prompt, not a later correction.

1. Check out the commit from step 1 in a worktree so the current work is untouched:
   `git worktree add /tmp/replay-$NAME <commit>`.
2. Start a fresh session of the same agent in that worktree, with the skill installed and nothing
   else from this conversation.
3. Run the first prompt, unchanged.
4. Compare what comes out with the version that stayed, on the habit the skill teaches. Other
   differences do not matter.
5. If the habit is wrong again, fix the skill (its description if it did not load, its body or
   examples if it loaded and still missed), and replay once more. Never change the prompt to
   help the skill.

In Codex, `codex exec "<prompt>"` in the worktree runs one prompt and exits; in Claude Code,
`claude -p "<prompt>"` does the same. Put `timeout 600` in front of either: a replay that has not
finished in 10 minutes is stopped and reported as not finished, never waited on. Check in the
transcript that the skill was opened; a skill that did not load has nothing to teach.

Inside the Codex sandbox a nested `codex exec` cannot start: it needs to write its own state
under `~/.codex`, and the sandbox mounts the home directory read-only. The same sandbox refuses
`git worktree add` on a repository outside the workspace (clone it instead) and the symlink
into `~/.agents/skills`. When a step is refused, do not skip it and do not retry with other
paths: give the user the exact command to run outside the sandbox, wait for the result, and
continue from it. A replay that never ran is not a replay.

## Prove it

Hosted eval runs and the quality review cost credits (the template README's Credits section has
the prices). Before the first one, ask the user which approach they want, in one question:

- Screen locally first: `scripts/local_screen.sh` runs the same scenarios against the model
  behind Tessl's default solver, for one to two cents a run, and hosted runs follow only for
  what the screen says is ready. It saves credits and needs a DeepSeek API key.
- Go straight to hosted Tessl runs.

Follow their answer; if they already said which, do not ask again. Then go in this order and stop
at the first stage that is not clean:

0. `tessl project create $NAME --workspace <workspace>` once, so `tessl.json` is linked to a
   project; ask the user for the workspace. Without it every hosted run fails after the free local
   checks pass. When a `tessl` command says to log in, ask the user to run `tessl login`; never
   start it yourself, since it waits for a browser. The allowance is monthly
   (`credits.resetsAt` in `tessl org usage --json`), and going past it is fine: Tessl accepts
   runs over the allowance with a notice, and that is not a reason to stop, ask, or switch. Stop
   hosted runs only when `credits.blocked` is true or Tessl refuses a run because the credits
   are used up; then offer the local screen below. The "Daily eval usage: N/1,000" line
   `tessl eval run` prints is a separate daily attempt cap, not the balance. Another workspace
   is never a way around a block.
1. `tessl review run --threshold 100 skills/$NAME/SKILL.md`, and fix every finding.
2. Freeze the skill text.
3. `./scripts/run_eval_suite.sh reference <scenario>` for each scenario, both variants.
4. `./scripts/run_eval_suite.sh reference`, then `main` once scenarios have moved there.

The finish line: the review at 100, every with-skill scenario at 100 without leading tasks or
answer keys, and at least three scenarios promoted to `evals/`, which a full Impact and
aggregate score on the registry need. Any edit to `SKILL.md` or its references invalidates
earlier runs.

## The local screen

Use it when the user chose it, or once Tessl blocks hosted runs. The template carries
`scripts/local_screen.sh`: the same scenarios run on the user's machine against the model behind
Tessl's default solver (DeepSeek V4.1 Flash through its Anthropic-compatible endpoint), one to
two cents a run, graded by a Claude judge. It needs a DeepSeek API key in `~/deepseek-api-key`;
if the file is missing, ask the user for one and stop.

```bash
scripts/local_screen.sh -x -n 2 evals-reference/<scenario>            # baseline arm
scripts/local_screen.sh -x -m skill -n 2 evals-reference/<scenario>   # skill arm
scripts/local_screen.sh --summary; scripts/local_screen.sh --summary -m skill
```

`-x` runs the scenarios' `setup.sh` on this machine; you wrote them, so pass it. Read a
scenario's `setup.sh` first when someone else wrote it.

What keeps it close to Tessl, so leave each of these as the script sets them:

- The solver is `claude -p --model deepseek-flash` with `ANTHROPIC_BASE_URL` set to
  `https://api.deepseek.com/anthropic`, the same model Tessl names `deepseek-v4.1-flash`, in its
  own `CLAUDE_CONFIG_DIR` so neither login leaks into the other. Another model, endpoint, or the
  user's own Claude login measures something else.
- The work directory gets what Tessl installs, in the same order: the scenario's fixtures, its
  `resources/`, its setup scripts. In skill mode the skill goes into `.claude/skills/` and the
  prompt starts with one line asking the agent to use it.
- The solver runs restricted (no Bash, no web, edits accepted, 40 turns), and the judge grades
  only the files it wrote, as Tessl's judge does: a task that wants an answer in chat scores
  nothing on either, so every task names a file to write.

How to read it: the baseline arm lands within about ten points of the hosted baseline, close
enough to place a scenario. The skill arm of this kind of skill came out about ten points under
the hosted run, so a local 90 can be a hosted 100; a hosted run decides the last points. When two
runs of a scenario differ by more than ten points, run it four to six times before trusting a
mean, since some scenarios flip between two outcomes. Read the `lost` lines, not only the totals,
and tune the skill in its own words, never by copying a checklist line. Report the numbers as
local screening results with run counts and ranges, never as hosted scores, and say which hosted
runs are still owed. `docs/agents/local-screening.md` in the new repository has the full method.

## The stop rule

A goal without a stop rule turns a stuck run into a loop. Per scenario and per change, at most
three runs. If a run is stuck, poll it with `tessl eval view <run-id>`; if a score does not move
after a fix, stop and report what you tried and what you would try next. Never run `tessl eval
run` in a loop, and never silence its errors.

## Report

Tell the user, in this order: the repository path, the name of the skill, the first prompt and
the commit you replayed, what the replay produced against the version that stayed, the score of
each scenario with and without the skill, the credits used, and every question you asked or
assumption you made.
