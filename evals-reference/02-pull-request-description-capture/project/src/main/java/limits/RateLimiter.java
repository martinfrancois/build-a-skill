package limits;

import java.time.Clock;
import java.time.Duration;
import java.time.Instant;
import java.util.ArrayDeque;
import java.util.Deque;
import java.util.HashMap;
import java.util.Map;

/** Allows at most {@code limit} requests per client in a sliding window. */
public final class RateLimiter {
    private final int limit;
    private final Duration window;
    private final Clock clock;
    private final Map<String, Deque<Instant>> seen = new HashMap<>();

    public RateLimiter(int limit, Duration window, Clock clock) {
        this.limit = limit;
        this.window = window;
        this.clock = clock;
    }

    public synchronized boolean allow(String clientId) {
        Instant now = clock.instant();
        Deque<Instant> times = seen.computeIfAbsent(clientId, id -> new ArrayDeque<>());
        while (!times.isEmpty() && times.peekFirst().isBefore(now.minus(window))) {
            times.removeFirst();
        }
        if (times.size() >= limit) {
            return false;
        }
        times.addLast(now);
        return true;
    }
}
