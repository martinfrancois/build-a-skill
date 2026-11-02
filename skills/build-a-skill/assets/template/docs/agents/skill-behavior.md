# Skill Behavior

## Scope

Editing `skills/my-skill/SKILL.md`, its references, or `skills/my-skill/agents/openai.yaml`.

## Rules

- Write the skill from the issue that describes the failure, never from an eval's
  `criteria.json`. A skill copied from criteria passes its own test and teaches nothing else.
- The `description` decides when an agent loads the skill. Write it in the third person, in four
  parts, under 1,024 characters:
  1. What the skill does.
  2. "Use for any of" and at least five short keywords, one to three words each, the way people
     type them in a request ("error message", "raise"), not a description of what the code does.
  3. "even if the user never says" and the words of the fix.
  4. "Not for" and the nearest task the skill should not fire on.

  The front matter is YAML, so a colon followed by a space breaks an unquoted description, and
  `tessl skill lint` does not notice. Use a full stop or a semicolon, or quote the whole value.
- Keep `SKILL.md` short: the hard stop near the top, a numbered workflow whose last step is a
  check the agent can tell is done, a reference table, and one bad, then good example. Move
  detail that only some tasks need into `references/`.
- A hard stop is a rule that beats every other step, and each one is a correction the user made:
  what it rejected and what it asked for instead, nothing more. Keep at most two; a long list of
  hard stops means none of them stands out.
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
