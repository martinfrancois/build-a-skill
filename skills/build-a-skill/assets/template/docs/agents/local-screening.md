# Local Screening With DeepSeek

## Scope

Use this to run eval scenarios against the model behind Tessl's default solver on your own
machine, for one to two cents a run, before spending Tessl credits or when the credit allowance
is used up (the free plan gives 1,000 credits per day, UTC). It covers setup, the commands, how
to read the output, and how to tune the skill against it. It does not replace hosted runs:
benchmark claims, release-readiness claims, and the registry score still come from Tessl.

## Why This Works

Tessl's default solver is `deepseek-v4.1-flash`. DeepSeek's own API serves the same model as
`deepseek-flash` and offers an Anthropic-compatible endpoint, so the `claude` CLI can drive it
unchanged with two environment variables. The author's `java-streams-skill` repository checked
the screen against hosted runs in October 2026: on its former main scenarios the hosted baseline
arm scored 100 where local runs scored 100, 94, 97, and 100, and on its two current main
scenarios the hosted baseline scored 26 and 60 where the local screen had predicted 30 and 69.
That is close enough to decide placement.

The harness differs from Tessl in three ways. The agent runs in Claude Code in restricted mode
(no Bash, no web, file tools confined to the work directory, edits accepted, 40 turns); Tessl runs
its own harness. The grader is Claude
Haiku with the scenario's `criteria.json` in the prompt; Tessl grades with its own judge. The
skill mode copies the one skill under `skills/` into `.claude/skills/` and tells the agent to use it; Tessl's
with-context arm installs the plugin. Expect a few points of drift per scenario on Tessl, in both
directions.

## Setup

1. Create an API key at <https://platform.deepseek.com/> and add credit. A run costs one to two
   US cents; ten US dollars covered about seven hundred runs in October 2026. DeepSeek halves the
   price in its off-peak window; the current window is on
   <https://api-docs.deepseek.com/quick_start/pricing/>.
2. Store the key alone, with no comment line and no trailing text, in `~/deepseek-api-key` and
   make it private:

   ```bash
   chmod 600 ~/deepseek-api-key
   ```

   Set `DEEPSEEK_API_KEY_FILE` to use another path. The scripts read the file at run time. Never
   paste the key into a shell profile, a commit, a transcript, or an issue.
3. Make sure `claude`, `jq`, and `python3` are on `PATH`, and that `claude` is logged in with the
   account that will pay for the judge calls. The judge defaults to Haiku; set
   `LOCAL_SCREEN_JUDGE` to pick another model.
4. Leave `CLAUDECODE` and every other Claude Code variable alone. The scripts isolate the solver
   with its own `CLAUDE_CONFIG_DIR` under the output directory, so the DeepSeek key never touches
   the regular Claude login and the regular login never leaks into the solver.

## Running

All commands run from the repository root. Output goes to `.local-screen/<mode>/<scenario>/run-N/`
(gitignored); set `LOCAL_SCREEN_OUT` to put it elsewhere, for example when comparing two skill
versions.

```bash
# baseline arm, no skill: the arm that decides suite placement
scripts/local_screen.sh -n 2 -p 4 evals-reference/<scenario>

# with the skill from the working tree copied into the agent's .claude/skills/
scripts/local_screen.sh -m skill -n 2 -p 4 evals/*/ evals-reference/*/

# more runs for a scenario whose two runs disagree
scripts/local_screen.sh -n 4 -s 3 evals-reference/<scenario>     # runs 3 to 6

# one line per scenario: run count, mean, min, max
scripts/local_screen.sh --summary
scripts/local_screen.sh --summary -m skill
```

What one run does:

1. Creates an empty work directory and passes the scenario's `task.md` as the prompt (skill mode
   also copies the one skill under `skills/` into `.claude/skills/` of that directory and prefixes the
   prompt with one line asking the agent to use it). An existing run directory is never deleted;
   rerun with `-s` and new run numbers.
2. Runs `claude -p --model deepseek-flash` with `ANTHROPIC_BASE_URL=https://api.deepseek.com/anthropic`
   and the key from the file, `--max-turns 40`, a 15-minute timeout, JSON output saved as
   `solver.json`. The solver runs with `--restricted --permission-mode acceptEdits
   --permission-prompts none`: it has no Bash or web tool, its file tools cannot leave the work
   directory, and anything that would ask for permission is denied. A scenario prompt from an
   untrusted contribution therefore cannot read the key file or any other host file through the
   agent; the key reaches only the DeepSeek API call. The agent cannot compile either, which
   matches Tessl's judge grading the files as written.
3. Calls `scripts/local_screen_judge.py`, which sends the task, the checklist from `criteria.json`,
   the files the agent wrote (skipping `.class` files, anything under `.claude/`, and files over
   60,000 bytes, with the API key redacted if the agent copied it anywhere) to the judge, and
   saves the item scores as `assessment.json` in the same shape as one Tessl solution. The
   agent's final message is left out, because Tessl's judge grades only the files: a task that
   asks for an explanation is only satisfied by an explanation in a file. Set
   `LOCAL_SCREEN_JUDGE_MESSAGE=1` to include the message when comparing with an older run. The console shows the
   total and one `lost` line per item that lost points, with the judge's reason.

Six parallel runs are fine on an ordinary developer machine; each solver run is one `claude`
process waiting on the network. A full pass over fifty scenarios, two runs each, takes about
twenty minutes and under two dollars.

## Reading The Output

Place scenarios by the baseline arm:

| Baseline over the runs | Placement |
| --- | --- |
| 98 to 100 in every run | `evals-regression/` |
| at least 30 points under 100 | `evals/` candidate, once the skill arm reaches 100 (the repo's with-context rule) |
| anything else | `evals-reference/` |

Rerun a scenario four to six times before trusting a mean when two runs differ by more than ten
points; several scenarios are bimodal (the solver either writes the pipeline or writes a loop).
Read the `lost` lines, not only the totals: they say what the solver did, which is the raw material
for both scenario fixes and skill fixes.

Keep the explicit-invocation finding in mind. On this solver, a prompt that names the skill
primes the code shape the skill teaches even without the skill, so an explicit variant of a
failing natural scenario can score far higher unaided. Screen an explicit scenario in its explicit
form; do not infer its baseline from a natural variant.

Record local numbers in the suite's `NUMBERING.md` as local screening results, with run counts
and ranges. Do not present them as hosted evidence anywhere.

## Tuning The Skill Against It

1. Run the skill arm over `evals/` and `evals-reference/` and collect every `lost` line.
2. For each loss, decide whether the skill is missing a rule or the scenario is unfair. A rule
   goes into the skill only when it is one the maintainer wants in every project, written in the
   skill's own words. Never copy a checklist description, a scenario's type or method names, or a
   scenario-specific hint into the skill; that is cheating, and it also stops working on the next
   scenario of the same kind.
3. Change the skill, then rerun the skill arm with `-n 3` on the scenarios that lost points and on
   a sample of regression scenarios, with `LOCAL_SCREEN_OUT` pointing to a fresh directory so the
   two versions can be compared side by side.
4. Run the baseline arm again only when a scenario's task or criteria changed; the skill text does
   not affect the baseline.
5. When every main scenario scores 100 with the skill locally, run the main suite on Tessl with
   both variants (`scripts/run_eval_suite.sh main`) as the hosted confirmation, and follow
   [Evals](evals.md) for what the hosted result must show before a release.

## References

- [Evals](evals.md)
- [Workflow](workflow.md)
