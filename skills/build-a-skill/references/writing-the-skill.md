# Writing the skill

## From the conversation only

Every rule in the skill traces to a correction the user made in this conversation. Write the
rule, the pair (not like this, like this), and the why from the capture notes. Anything you add
because it "might also go wrong" is speculation and becomes a rule the agent follows with
confidence and no evidence; leave it out.

## The description is the trigger

Agents read only the `name` and `description` at startup and decide from them whether to open
the rest. Write the description in the third person: what the skill does, then the situations
that should load it, in the words a user would type, ending with "even if the user never says
...". Under 1,024 characters. Be generous with trigger words; agents undertrigger.

## The shape of SKILL.md

- A title and two sentences on what the skill is for.
- One or two hard stops: the rules that beat every other step. More than two means none stands
  out.
- "When to use": three to five bullets.
- A numbered workflow whose last step is a check the agent can tell is done.
- A reference table: file, and when to read it.
- One pair: bad, then good, with the why in one sentence.

Keep `SKILL.md` under about 120 lines. Detail that only some tasks need goes into `references/`.

## References as pairs with the why

Each round from the capture notes becomes one section in `references/examples.md`:

```markdown
## <the habit, in five words>

Not like this:

<the almost-right code>

Like this:

<the version that stayed>

Why: <one sentence from the correction>
```

The why tells the agent which rules bend. Keep the examples in the domain of the conversation;
the eval tasks must use a different domain or a different shape, so the agent cannot score by
copying.

## Do not teach to the test

Never open an eval's `criteria.json` while writing the skill, and never quote a scenario name,
expected output, or score in the skill or its references. The template's validator rejects the
common markers.

## The other files

- `agents/openai.yaml`: `display_name`, a `short_description` of 25 to 64 characters, and a
  `default_prompt` that starts with `Use $<name> when ...`.
- `.tessl-plugin/plugin.json`: `name` as `<owner>/<name>`, `description` and `summary` in one
  sentence each, `repository` and `homepage` as the new repository's URL.
- To make the skill load only when called by hand, follow "Make it explicit-only" in the
  template README.
