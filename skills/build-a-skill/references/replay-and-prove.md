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
`claude -p "<prompt>"` does the same. Check in the transcript that the skill was opened; a skill
that did not load has nothing to teach.

## Prove it

Hosted runs cost credits; spend them in this order and stop at the first stage that is not
clean:

0. `tessl project create $NAME --workspace <workspace>` once, so `tessl.json` is linked to a
   project; ask the user for the workspace. Without it every hosted run fails after the free
   local checks pass. If tessl says the credit allowance is used up, stop and report.
1. `tessl review run --threshold 100 skills/$NAME/SKILL.md`, and fix every finding.
2. Freeze the skill text.
3. `scripts/run_eval_suite.sh reference <scenario>` for each scenario, both variants.
4. `scripts/run_eval_suite.sh reference`, then `main` once scenarios have moved there.

The finish line: every with-skill scenario at 100, without leading tasks or answer keys. Any
edit to `SKILL.md` or its references invalidates earlier runs.

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
