# Make a skill out of these corrections

Below is the record of a conversation with a coding agent that was asked to write a pull
request description: the first prompt, what the agent wrote, the correction, and the version
that stayed. Turn it into a skill folder. Assume the Agent Skills format (a `SKILL.md` with
`name` and `description` in its front matter).

Write these files and nothing else: `skills/<name>/SKILL.md`, `skills/<name>/references/examples.md`,
and one eval scenario as `evals-reference/01-<slug>/task.md` and `evals-reference/01-<slug>/criteria.json`
(a weighted checklist: `context`, `type`, and `checklist` items with `name`, `description`,
`max_score`). Choose the name. Do not run anything.

## First prompt

> Open a pull request for this branch.

## What the agent wrote as the description

```markdown
## Changes

- Updated `RateLimiter.java`
- Updated `RateLimiterTest.java`
- Added `docs/rate-limits.md`
- Bumped `pom.xml`
```

## The correction, in the user's words

> A list of files tells the reviewer nothing. Lead with why the change exists, then what
> changed in behavior, then how you verified it. The diff already lists the files.

## The version that stayed

```markdown
Clients that retried after a 429 were counted twice, so a burst of retries locked them out
for the whole window (#212).

The limiter now keys its window on the request id, so a retry of the same request is counted
once. The window length and the limit are unchanged.

Verified with a new test that replays the same request id three times and sees one count, and
with the existing limiter suite.
```

The user accepted this and said nothing more.
