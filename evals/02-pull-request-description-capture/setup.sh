#!/usr/bin/env bash
# Rebuilds the repository as it was in the session: main with the old limiter, and the branch
# the user asked to open a pull request for, three commits ahead. Tessl uploads only declared
# scenario files, so the branch's files are written from this script.
set -euo pipefail
cd gateway-limits
if [ -d .git ]; then
  exit 0
fi
commit() { git -c user.name=Dev -c user.email=dev@example.com commit -q -m "$1"; }
git init -q -b main
git add -A
commit "Sliding-window rate limiter per client"
git switch -q -c fix/retry-double-count
mkdir -p "$(dirname src/main/java/limits/RateLimiter.java)"
cat > src/main/java/limits/RateLimiter.java <<'SESSION_FILE'
package limits;

import java.time.Clock;
import java.time.Duration;
import java.time.Instant;
import java.util.HashMap;
import java.util.LinkedHashMap;
import java.util.Map;

/** Allows at most {@code limit} requests per client in a sliding window; a retry counts once. */
public final class RateLimiter {
    private final int limit;
    private final Duration window;
    private final Clock clock;
    private final Map<String, LinkedHashMap<String, Instant>> seen = new HashMap<>();

    public RateLimiter(int limit, Duration window, Clock clock) {
        this.limit = limit;
        this.window = window;
        this.clock = clock;
    }

    public synchronized boolean allow(String clientId, String requestId) {
        Instant now = clock.instant();
        LinkedHashMap<String, Instant> requests = seen.computeIfAbsent(clientId, id -> new LinkedHashMap<>());
        requests.values().removeIf(time -> time.isBefore(now.minus(window)));
        if (requests.containsKey(requestId)) {
            return true;
        }
        if (requests.size() >= limit) {
            return false;
        }
        requests.put(requestId, now);
        return true;
    }
}
SESSION_FILE
mkdir -p "$(dirname src/test/java/limits/RateLimiterTest.java)"
cat > src/test/java/limits/RateLimiterTest.java <<'SESSION_FILE'
package limits;

import static org.junit.jupiter.api.Assertions.assertFalse;
import static org.junit.jupiter.api.Assertions.assertTrue;

import java.time.Clock;
import java.time.Duration;
import java.time.Instant;
import java.time.ZoneOffset;
import org.junit.jupiter.api.Test;

class RateLimiterTest {
    private final Clock clock = Clock.fixed(Instant.parse("2026-01-01T00:00:00Z"), ZoneOffset.UTC);

    @Test
    void retriesOfOneRequestCountOnce() {
        RateLimiter limiter = new RateLimiter(2, Duration.ofMinutes(1), clock);
        assertTrue(limiter.allow("client", "req-1"));
        assertTrue(limiter.allow("client", "req-1"));
        assertTrue(limiter.allow("client", "req-1"));
        assertTrue(limiter.allow("client", "req-2"));
        assertFalse(limiter.allow("client", "req-3"));
    }
}
SESSION_FILE
git add -A
commit "Count a retried request once (#212)"
mkdir -p "$(dirname docs/rate-limits.md)"
cat > docs/rate-limits.md <<'SESSION_FILE'
# Rate limits

Each client may send 100 requests per minute. A retry that carries the same `X-Request-Id` as
an earlier request in the window counts once, so retrying after a 429 does not use up more of
the limit.
SESSION_FILE
git add -A
commit "Document how retries count against the limit"
# Portable in-place edit: GNU and BSD sed disagree on -i.
sed 's#<version>0.1.0</version>#<version>0.1.1</version>#' pom.xml > pom.xml.next
mv pom.xml.next pom.xml
git add -A
commit "Bump to 0.1.1"
