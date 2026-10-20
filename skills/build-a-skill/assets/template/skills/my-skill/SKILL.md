---
name: my-skill
description: Writes and reviews code that follows this team's convention for error messages. Use whenever code raises, throws, returns, or logs an error, or a change or review touches error handling, in any language, even if the user never says "error message" or "convention".
license: MIT
---

# Error message convention

Every error message this team writes has one form:

```text
cannot <verb> <thing> "<offending value>": <what was expected or what to do next>
```

## Hard stop

Never put a secret into an error message or log line: passwords, tokens, API keys, session
IDs, card numbers, or URLs that carry credentials. Name the field and leave its value out. This
rule beats every step below, and [hard-stops.md](references/hard-stops.md) lists what counts as a
secret.

## When to use

- Writing code that raises, throws, returns, or logs an error.
- Changing or reviewing existing error handling.
- Cleaning up messages that came from another codebase or a generator.

## Workflow

1. List every message the task touches: raised or thrown errors, returned error values, and
   error-level log calls.
2. Start each message with `cannot`, a verb, and the thing that failed, all lowercase except
   identifiers: `cannot parse due date`, `cannot read RETRY_LIMIT`.
3. Put the offending value in double quotes right after the thing. If the value is a secret, the
   hard stop applies: keep the field name, drop the value.
4. After a colon, state what was expected or the next step the caller can take.
5. Write one plain line: no `Error:`, `Invalid`, or `Failed to` prefix, no apology, no exclamation
   mark, no trailing period.
6. When wrapping a lower-level exception, keep it attached as the cause (`raise ... from err` in
   Python, the `cause` argument in Java and JavaScript).
7. Reread every touched message against steps 2 to 6 and the hard stop. The step is done when
   each one passes.

In a review, write each finding as the original message, the problem, and the fixed message. In
code, write the requested file first, then explain.

## References

| File | Read it when |
|---|---|
| [examples.md](references/examples.md) | You want a whole function worked through, before and after |
| [hard-stops.md](references/hard-stops.md) | A message includes request data, credentials, or configuration values |

## Example

Bad:

```python
raise ValueError(f"Error: invalid due date {raw}!")
```

Good:

```python
raise ValueError(f'cannot parse due date "{raw}": expected a calendar date as YYYY-MM-DD')
```

The good version names what failed, shows the value the caller sent, and tells them how to fix
it.
