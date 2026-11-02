# Writing the skill

## From the conversation only

Every rule in the skill traces to a correction the user made in this conversation. Write the rule,
the pair (not like this, like this), and the why from the capture notes. Anything you add because
it "might also go wrong" is speculation and becomes a rule the agent follows with confidence and
no evidence; leave it out. This covers the hard stops, every workflow step and every line of the
references: a rule about a neighbouring method, a style, a length, or a tool the user never
mentioned is out. The same holds for choices the version that stayed happens to make: they appear
in the pair, but they become a rule only if the user asked for them, so a workflow step says what
to do, never how the kept version happened to do it (a helper it happened to extract, a naming or
formatting detail). Places the habit might also apply, such as other input sources, other
languages, code review, or refactoring, are speculation too unless the conversation showed them,
in the description as anywhere else, and so is a ban on the opposite of what the user asked for.
After writing, read `SKILL.md` once more against the capture and delete every rule that no
correction supports.

## The description is the trigger

Agents read only the `name` and `description` at startup and decide from them whether to open the
rest, and agents undertrigger. Write the description in the third person, in four parts, under
1,024 characters:

1. What the skill does, with the verb of the task the conversation did: a conversation that
   wrote code gives "Writes ..." or "Adds ...", not "Writes and reviews ...".
2. "Use for any of" and a comma-separated list of at least five short keywords, one to three words
   each, the way a user types them in a request: the name of the task, the code or command where
   the mistake happens, and the words for what the correction rejected and what it asked for.
   Nouns and commands, not "-ing" phrases or sentences about a situation.
3. "even if the user never says" and the words of the fix.
4. "Not for" and the nearest task it should not fire on.

For a commit-message habit: "Writes git commit messages with a short imperative subject and a
body that says why. Use for any of commit, commit message, git commit, amend, squash, subject
line, commit body, even if the user never says imperative or body. Not for pull request
descriptions or changelogs."

The front matter is YAML: a colon followed by a space inside an unquoted description breaks it,
and `tessl skill lint` does not notice; `tessl review run` and the agents do. Use a full stop or a
semicolon instead, or quote the whole value.

## The shape of SKILL.md

- A title and two sentences on what the skill is for.
- At most two hard stops, each one the correction the user made, in what it said and nothing more:
  both what it rejected and what it asked for instead, in one bullet. Something the correction
  implies but never said, such as banning a neighbouring method, is not a hard stop. With more
  than two corrections, the two the user pressed hardest are hard stops and the rest become
  workflow steps; more than two means none stands out.
- A numbered workflow whose last step is a check the agent can tell is done: for code, it
  compiles and no longer contains what the correction rejected.
- A reference table: file, and when to read it.
- One pair under the headings "Not like this" and "Like this", with the why in one sentence.

Keep `SKILL.md` under about 120 lines. Detail that only some tasks need goes into `references/`.

The template's `skills/my-skill` is a team convention, not a conversation: it shows the layout
only. Replace every line of it; its rules, its review format, its languages, and its "Writes and
reviews" opening do not carry over unless the conversation showed them too.

## References as pairs with the why

Each round from the capture notes becomes one section in `references/examples.md`:

```markdown
## <the habit, in five words>

### Not like this

<the almost-right code>

### Like this

<the version that stayed>

Why: <one sentence from the correction>
```

Keep the two headings as written, so every pair is found by its heading. The why is exactly one
sentence and restates the user's correction, not a benefit you inferred; when the correction
gave several reasons, keep the one the user stated. The why tells the agent which rules bend.
Keep the examples in the domain of the conversation; the eval tasks must use a different domain
or a different shape, so the agent cannot score by copying.

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
