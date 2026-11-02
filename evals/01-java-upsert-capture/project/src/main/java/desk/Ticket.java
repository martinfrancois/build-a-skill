package desk;

import java.time.Instant;

public final class Ticket {
    private final String reference;
    private Instant lastTouched;

    Ticket(String reference, Instant openedAt) {
        this.reference = reference;
        this.lastTouched = openedAt;
    }

    public String reference() {
        return reference;
    }

    public Instant lastTouched() {
        return lastTouched;
    }

    void touchedAt(Instant when) {
        lastTouched = when;
    }
}
