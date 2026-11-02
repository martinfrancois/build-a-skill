package desk;

import java.time.Clock;
import java.util.ArrayList;
import java.util.List;

public final class TicketDesk {
    private final List<Ticket> tickets = new ArrayList<>();
    private final Clock clock;

    public TicketDesk(Clock clock) {
        this.clock = clock;
    }

    public List<Ticket> tickets() {
        return List.copyOf(tickets);
    }

    private Ticket touch(Ticket ticket) {
        ticket.touchedAt(clock.instant());
        return ticket;
    }

    private Ticket open(String reference) {
        Ticket ticket = new Ticket(reference, clock.instant());
        tickets.add(ticket);
        return ticket;
    }
}
