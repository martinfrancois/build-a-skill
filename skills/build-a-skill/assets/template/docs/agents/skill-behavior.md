# Skill Behavior

## Scope

Editing `skills/my-skill/SKILL.md`, its references, or `skills/my-skill/agents/openai.yaml`.

## Rules

- Write the skill from the issue that describes the failure, never from an eval's
  `criteria.json`. A skill copied from criteria passes its own test and teaches nothing else.
- The `description` decides when an agent loads the skill. Write it in the third person, name
  what the skill does, then list the situations that should trigger it with "Use whenever ...,
  even if the user never says ...". Keep it under 1,024 characters.
- Keep `SKILL.md` short: when to use, the hard stop near the top, a numbered workflow whose
  last step is a check the agent can tell is done, a reference table, and one bad, then good
  example. Move detail that only some tasks need into `references/`.
- A hard stop is a rule that beats every other step. Keep one or two; a long list of hard stops
  means none of them stands out.
- Runtime references must not contain answer keys: no eval scenario names, expected outputs,
  scoring rubrics, run IDs, or score claims. The validator rejects the common markers.
- Examples in references use a different domain from every eval task, so a high score shows the
  agent applied the rule rather than recognized the example.
- User-facing output follows the convention without naming the skill's own machinery. Reviews
  explain the code; they do not say "per the skill" or "hard stop" unless the user asked about
  the workflow.
- The skill auto-selects by default. To make it explicit-only, follow the README section on
  explicit-only skills; it covers Codex and Claude Code.

## References

- [Eval Guidance](evals.md)
- [Workflow](workflow.md)
