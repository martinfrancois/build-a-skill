# Skill starter

A working Agent Skill with Tessl evals. The skill, `my-skill`, teaches an agent one team
convention for error messages, and three eval scenarios measure whether it changes what the agent
writes. Clone it, run the checks, then follow the steps below to replace the example with your
own convention.

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
   `evals/01-settings-loader-errors`: a `task.md` with the prompt a user would type (no fix, no
   skill name, one `Assume ...` line for the version), a one-line `capability.txt`, a
   `criteria.json` with 15 safety, 80 quality, and 5 maintainability points, and a
   `criteria-meta.json`. Start the `context` in `criteria.json` with "Reference coverage", not
   "Main eval"; the validator keeps "Main eval" for scenarios in `evals/`. Delete the three example scenarios, which test the error message
   convention, and update the table in `evals/NUMBERING.md`. Put the identifiers every task in
   your domain shares (language keywords, standard library names) into `DOMAIN_IDENTIFIERS` at
   the top of `scripts/validate_eval_criteria.py`. Then run
   `python3 scripts/validate_eval_criteria.py evals evals-reference evals-regression`.
5. **Write SKILL.md from the issue only.** Replace "error messages" in the `description` of
   `skills/my-skill/SKILL.md`, in `skills/my-skill/agents/openai.yaml`, and in the `description`
   and `summary` of `.tessl-plugin/plugin.json` with your subject, then rewrite the body and the
   two files in `skills/my-skill/references/` from the issue. Do not open your `criteria.json` while you write;
   a skill copied from the checklist passes its own test and nothing else.
6. **Run the quality review to 100.** Run
   `tessl review run --threshold 100 skills/my-skill/SKILL.md` and fix every finding until it
   passes.
7. **Run the eval suite until every with-skill scenario is 100, without leading prompts.**
   `scripts/run_eval_suite.sh reference`. When a with-skill score is below 100, fix the skill, not
   the task: adding hints to `task.md` or loosening `criteria.json` makes the number meaningless.
   Once the scenario scores 100 with the skill and at least 30 points less without it, move it
   to `evals/`. `evals/NUMBERING.md` has the full rule.
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
| `evals/01-settings-loader-errors` | Main suite: a natural prompt where the skill should change the answer |
| `evals-reference/01-webhook-error-review` | Reference suite: an explicit review of four messages |
| `evals-regression/02-hard-stop-audit` | Regression suite: a check that needs the skill's exact hard-stop text |
| `evals/NUMBERING.md` | How scenarios are numbered and when one moves to the main suite |
| `scripts/` | Suite runner, criteria validator, and result classifier |
| `AGENTS.md`, `docs/agents/` | Rules for coding agents working on this repo: workflow, evals, skill text |
| `tessl.json`, `.tessl-plugin/plugin.json` | Tessl project and plugin manifests, version 0.1.0 |

## How to run

The local checks are free:

```bash
python3 scripts/validate_eval_criteria.py evals evals-reference evals-regression
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

Run the main suite, with and without the skill:

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
`license: MIT`:

```yaml
disable-model-invocation: true
```

After that, `$my-skill` and `/my-skill` still work, but neither agent loads the skill on its own.
Mark any eval scenario that relies on the skill as `"invocation": "explicit"` and name the skill
in its `task.md`.

## Credits

As of October 2026, Tessl Free includes 1,000 credits a month, and each paired scenario (one run
with the skill, one without) costs 20 credits. That is 50 paired scenario runs a month. One full
pass over the starter suites is two paired scenarios plus one with-skill-only scenario, so at most
60 credits. The suite script passes `--force`, so every run is fresh and costs the full amount.
Run single scenarios while you iterate and full suites only when the skill text is frozen.

## License

[MIT](LICENSE), copyright 2026 François Martin.
