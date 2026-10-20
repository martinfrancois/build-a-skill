# Build a skill

An Agent Skill that turns the conversation you are in into a new skill with evals. Use it the
moment the agent has produced what you wanted after one or more corrections: it finds where the
story started, captures every round, writes the skill from those corrections only, scaffolds a
repository with eval suites, replays your first prompt with the skill installed, and proves the
skill with runs with and without it.

It works in Claude Code and Codex and is written to be agent-independent: the folder follows the
[Agent Skills specification](https://agentskills.io/specification), and the only agent-specific
parts (where transcripts live, how to install) are listed in
[transcripts.md](skills/build-a-skill/references/transcripts.md) and
[replay-and-prove.md](skills/build-a-skill/references/replay-and-prove.md). Another agent can
ask you for what it cannot find.

## Install

A symlink keeps the installed skill in step with this repository.

```bash
git clone https://github.com/martinfrancois/build-a-skill.git
cd build-a-skill
# Claude Code
mkdir -p ~/.claude/skills && ln -s "$PWD/skills/build-a-skill" ~/.claude/skills/build-a-skill
# Codex
mkdir -p ~/.agents/skills && ln -s "$PWD/skills/build-a-skill" ~/.agents/skills/build-a-skill
```

## Use

In the conversation where the agent finally got it right:

```text
/build-a-skill          # Claude Code
$build-a-skill          # Codex
```

or in plain words: "turn these corrections into a skill". The skill then:

1. finds the first prompt that produced the almost-right output, from the conversation or the
   session transcript on disk, and asks you if it cannot tell;
2. captures each round: code before, prompt, output, your correction, the version that stayed,
   and why;
3. proposes a name and a directory for the new repository;
4. copies the [template](skills/build-a-skill/assets/template/) there and writes `SKILL.md`,
   its examples as "not like this, like this, why" pairs, and one eval scenario per round;
5. replays your first prompt at the commit before it, with the new skill installed, and
   compares the result with the version that stayed;
6. runs the quality review and the evals until every with-skill scenario scores 100, with a stop
   rule of three runs per scenario, and installs the skill.

The template's [README](skills/build-a-skill/assets/template/README.md) holds the same steps for
doing them by hand.

## Credits

Hosted evals use Tessl credits: as of October 2026, Free includes 1,000 a month and a paired
scenario costs 20. The skill spends them in order (review, targeted scenarios, suites) and stops
at the first stage that is not clean.

## License

[MIT](LICENSE), copyright 2026 François Martin.
