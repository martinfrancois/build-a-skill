# Skill template

A working Agent Skill with Tessl evals, copied into a new repository by the
[build-a-skill](../../../../README.md) skill. The example skill, `my-skill`, teaches an agent one
team convention for error messages, and three eval scenarios measure whether it changes what the
agent writes. The build-a-skill skill replaces the example with yours; the steps below are the
same work written for a person doing it by hand.

## Build your first skill

Follow these in order.

1. **Capture the almost-right output and the version you wanted.** The next time an agent hands
   you code that is close but wrong in a way you keep correcting, save it untouched. Then fix it by
   hand into the version you wanted. Keep the prompt, the model, and both versions.
2. **Write it as a self-contained issue.** Put the prompt, the agent's output, your version, and
   one paragraph on why the difference matters into a single text. Someone who never saw the
   session should be able to act on it.
3. **Replay the task with and without.** Start two fresh sessions with the same prompt. In one,
   paste the issue text in as guidance. If the plain session already gets it right, you have no
   skill to write; go back to step 1. If the guided session still gets it wrong, the issue is not
   clear yet; rewrite it and replay.
4. **Reduce to an eval.** Make a folder in `evals-reference/` with the same four files as
   `evals/01-settings-loader-errors`:
   - `task.md`: the prompt a user would type, with no fix, an `Assume ...` sentence for the
     version, and no skill name unless the scenario is explicit. The shipped reference example
     is explicit, so it opens with "Use $my-skill"; leave those words out of a natural scenario.
   - `capability.txt`: one line naming what the scenario tests.
   - `criteria.json`: checks worth 15 safety, 80 quality, and 5 maintainability points. Start its
     `context` with "Reference coverage"; the validator keeps "Main eval" for `evals/`.
   - `criteria-meta.json`: the invocation, task type, evidence type, and a category per check.

   Then clean up the example:
   - Delete the three example scenarios, which test the error message convention.
   - Replace the rows of the "Current numbers" table in `evals/NUMBERING.md` with yours. The
     validator flags rows whose folder no longer exists.
   - In `scripts/validate_eval_criteria.py`, keep the general programming words at the top of
     `DOMAIN_IDENTIFIERS` and replace the entries under its `# Example domain` comment with the
     identifiers every task in your domain shares.
   - Run `python3 scripts/validate_eval_criteria.py`.

   The validator also fails a main task that repeats 85% or more of a reference or regression
   task, so move a scenario between suites instead of copying it.
5. **Write SKILL.md from the issue only.** Rewrite these from the issue, in your own subject:
   - `skills/my-skill/SKILL.md`: the `description` (what the skill does, then the situations that
     should trigger it) and the whole body.
   - `skills/my-skill/references/`: both files, with examples from a domain none of your eval
     tasks use.
   - `skills/my-skill/agents/openai.yaml`: `short_description` and `default_prompt`. Keep
     `display_name` unless you rename the skill.
   - `.tessl-plugin/plugin.json`: `description`, `summary`, and `repository` and `homepage`
     (the URL of your copy of this repo).

   Do not open your `criteria.json` while you write; a skill copied from the checklist passes its
   own test and nothing else. Then run `python3 scripts/validate_eval_criteria.py` again: its
   check for overlap between your eval tasks and the references only means something once the
   references are yours.
6. **Run the quality review to 100.** Run
   `tessl review run --threshold 100 skills/my-skill/SKILL.md` and fix every finding until it
   passes.
7. **Run the eval suite until every with-skill scenario is 100, without leading prompts.**
   `scripts/run_eval_suite.sh reference`. When a with-skill score is below 100, fix the skill, not
   the task: adding hints to `task.md` or loosening `criteria.json` makes the number meaningless.
   Once the scenario scores 100 with the skill and at least 30 points less without it, move it
   to `evals/` and change the start of its `context` from "Reference coverage" to "Main eval".
   `evals/NUMBERING.md` has the full rule.
8. **Weight by difference.** Read the per-check results of the run without the skill
   (`tessl eval view <run-id>`). Move quality points toward the checks it missed and away from the
   ones both runs passed, keep the 15/80/5 split, and rerun both variants. This changes how many
   points a check carries, never what it asks for.
9. **Install it and use it.** Link the skill into your agent (see
   [Install the skill](#install-the-skill)) and use it on real work for a week.
10. **Capture the next failure as an issue.** When it gets something almost right again, that is
    step 1 for the next version.

## What is in this repo

| Path | What it holds |
|---|---|
| `skills/my-skill/SKILL.md` | The skill: description, hard stop, workflow, reference table, example |
| `skills/my-skill/references/` | `examples.md` (one function worked through) and `hard-stops.md` (what counts as a secret) |
| `skills/my-skill/agents/openai.yaml` | Display name and default prompt that Codex shows for the skill |
| `evals/` | Main suite, the only source of lift claims; ships with one example scenario |
| `evals-reference/` | Reference suite, where new scenarios start; ships with one example scenario |
| `evals-regression/` | Regression suite, run with the skill only; ships with one example scenario |
| `evals/NUMBERING.md` | How scenarios are numbered and when one moves to the main suite |
| `scripts/` | Suite runner, criteria validator, and result classifier |
| `AGENTS.md`, `docs/agents/` | Rules for coding agents working on this repo: workflow, evals, skill text |
| `tessl.json`, `.tessl-plugin/plugin.json` | Tessl project and plugin manifests, version 0.1.0 |

## How to run

The local checks are free:

```bash
python3 scripts/validate_eval_criteria.py
python3 -m py_compile scripts/*.py
bash -n scripts/*.sh
tessl skill lint .
tessl plugin lint .
for suite in evals evals-reference evals-regression; do tessl eval lint "$suite"; done
```

Hosted evals cost credits (see [Credits](#credits)). Log in once:

```bash
tessl login
```

Link this directory to a Tessl project in your workspace (`tessl workspace list` shows its
name). The `--workspace` flag takes precedence over the `martinfrancois/` prefix in `tessl.json`:

```bash
tessl project create skill-starter --workspace <your-workspace>
```

Once `evals/` has a scenario, run the main suite, with and without the skill:

```bash
tessl eval run --skill my-skill .
```

The suite script runs any suite with the right variants (both for `main` and `reference`, with
the skill only for `regression`) and can target single scenarios:

```bash
scripts/run_eval_suite.sh main
scripts/run_eval_suite.sh reference
scripts/run_eval_suite.sh regression
scripts/run_eval_suite.sh reference 01-webhook-error-review
```

### Screen locally for a cent a run

When the credits are used up, or before spending them, run the same scenarios on your own
machine against the model behind Tessl's default solver. You need a DeepSeek API key in
`~/deepseek-api-key` (see [Local screening](docs/agents/local-screening.md) for the setup):

```bash
scripts/local_screen.sh -n 2 evals-reference/01-webhook-error-review            # without the skill
scripts/local_screen.sh -m skill -n 2 evals-reference/01-webhook-error-review   # with the skill
scripts/local_screen.sh --summary && scripts/local_screen.sh --summary -m skill
```

Local numbers predict the hosted result and decide where a scenario belongs; they are never
hosted evidence.

To decide where a scenario belongs after a run:

```bash
tessl eval view <run-id> --json > /var/tmp/eval-run.json
python3 scripts/classify_eval_result.py /var/tmp/eval-run.json \
  --scenario-dir evals-reference/01-webhook-error-review
```

## Install the skill

A symlink keeps the installed skill in step with this repo, so every edit you make here is the
version the agent uses next.

### Claude Code

```bash
mkdir -p ~/.claude/skills
ln -s "$PWD/skills/my-skill" ~/.claude/skills/my-skill
```

Claude Code picks the skill when a task matches its description. To call it directly, start a
message with `/my-skill`:

```text
/my-skill review the error handling in src/upload.py
```

### Codex

```bash
mkdir -p ~/.agents/skills
ln -s "$PWD/skills/my-skill" ~/.agents/skills/my-skill
```

Codex picks the skill when a task matches its description. To call it directly, mention
`$my-skill`:

```text
$my-skill review the error handling in src/upload.py
```

## Make it explicit-only

Some skills should run only when you ask for them, such as a release checklist. Each agent has
its own switch, and you can set both.

For Codex, add this block to `skills/my-skill/agents/openai.yaml`:

```yaml
policy:
  allow_implicit_invocation: false
```

For Claude Code, add this line to the frontmatter of `skills/my-skill/SKILL.md`, below
`license: MIT`. It is a Claude Code field, not part of the Agent Skills spec:

```yaml
disable-model-invocation: true
```

After that, `$my-skill` and `/my-skill` still work, but neither agent loads the skill on its own.
Mark any eval scenario that relies on the skill as `"invocation": "explicit"` and name the skill
in its `task.md`.

## Credits

As of October 2026, Tessl Free includes 1,000 credits per calendar month, reset on the 1st, and
each paired scenario (one run with the skill, one without) costs 20 credits. That is 50 paired
scenario runs a month. One full pass over the starter suites is two paired scenarios plus one
with-skill-only scenario, so at most 60 credits. The suite script passes `--force`, so every run
is fresh and costs the full amount. Run single scenarios while you iterate and full suites only
when the skill text is frozen.

Check the balance before a hosted run, not after:

```bash
tessl org usage --json   # credits.remaining, credits.overLimit, credits.resetsAt
```

Three things that are easy to misread:

- The "Daily eval usage: N/1,000" line that `tessl eval run` prints is a separate cap of 1,000
  eval attempts per day (reset at 00:00 UTC). It is not your credit balance.
- Over the allowance, Tessl may still accept runs with a one-line notice instead of refusing
  them. That is not permission to keep spending: stop and use the
  [local screen](docs/agents/local-screening.md) until the month resets.
- Since CLI 0.117.0, `tessl review run` is free and runs even when the credits are used up.

## License

[MIT](LICENSE), copyright 2026 François Martin.
