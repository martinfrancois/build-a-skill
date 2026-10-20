# Maintaining Agent Docs

## Scope

Changing `AGENTS.md` or files under `docs/agents/`.

## Rules

- `AGENTS.md` holds only the one-sentence project description, the startup instruction, the
  durable-correction rule, and links. Topic guidance goes in a page under `docs/agents/`, linked
  from `AGENTS.md`.
- When asked to add guidance to `AGENTS.md`, write it into the matching `docs/agents/` page, or
  a new page from the template below, and add only a link to `AGENTS.md`.
- When the user corrects wording, naming, scope, eval design, or project policy, write the
  correction into the page it belongs to, so the next session follows it without being told.
- If a requested change conflicts with an existing rule, stop and ask the user which one to
  keep.
- Pages under `docs/agents/` must make sense on their own. Summarize a decision and its reason
  instead of pointing at an issue, a pull request, a transcript, or a hosted run. The validator
  rejects issue numbers, pull request numbers, and run IDs here.
- Delete rules that are vague or that an agent follows without being told.

## Template for a new page

```md
# <Title>

## Scope

What this page covers.

## Rules

- Clear, actionable rules.

## References

- Related pages.
```
