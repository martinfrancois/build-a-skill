#!/usr/bin/env bash
# Rebuilds the state at the end of the session: the project committed as it was before the first
# prompt, and the version the user accepted left in the working tree, not yet committed. Tessl
# uploads only declared scenario files, so the accepted version is written from this script.
set -euo pipefail
cd ticket-desk
if [ ! -d .git ]; then
  git init -q -b main
  git add -A
  git -c user.name=Dev -c user.email=dev@example.com commit -q -m "Ticket desk with open and touch"
fi
mkdir -p "$(dirname src/main/java/desk/TicketDesk.java)"
cat > src/main/java/desk/TicketDesk.java <<'SESSION_FILE'
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

    public Ticket findOrOpenTicket(String reference) {
        return tickets.stream()
                .filter(ticket -> ticket.reference().equals(reference))
                .findFirst()
                .map(this::touch)
                .orElseGet(() -> open(reference));
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
SESSION_FILE
