Earlier in this session, in `gateway-limits/`:

**Me:** Open a pull request for this branch.

**You:** Opened #214 with this description:

```markdown
## Changes

- Updated `RateLimiter.java`
- Updated `RateLimiterTest.java`
- Added `docs/rate-limits.md`
- Bumped `pom.xml`
```

**Me:** A list of files tells the reviewer nothing. Lead with why the change exists, then what
changed in behavior, then how you verified it. The diff already lists the files.

**You:** Updated the description of #214:

```markdown
Clients that retried after a 429 were counted twice, so a burst of retries locked them out
for the whole window (#212).

The limiter now keys its window on the request id, so a retry of the same request is counted
once. The window length and the limit are unchanged.

Verified with a new test that replays the same request id three times and sees one count, and
with the existing limiter suite.
```

**Me:** Good. Make this a skill so the next PR description comes out like that. Put it next to
gateway-limits.
