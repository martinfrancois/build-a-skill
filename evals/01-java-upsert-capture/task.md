Earlier in this session, in `ticket-desk/`:

**Me:** Add a method `findOrOpenTicket(String reference)` to `TicketDesk`: if a ticket with that
reference exists, return it after marking it as touched, otherwise open a new one with that
reference and return it.

**You:** Added to `src/main/java/desk/TicketDesk.java`:

```java
public Ticket findOrOpenTicket(String reference) {
    for (Ticket ticket : tickets) {
        if (ticket.reference().equals(reference)) {
            return touch(ticket);
        }
    }
    return open(reference);
}
```

**Me:** Don't loop over the list with an early return. Use a stream and the Optional API.

**You:** Changed it:

```java
public Ticket findOrOpenTicket(String reference) {
    return tickets.stream()
            .filter(ticket -> ticket.reference().equals(reference))
            .findFirst()
            .map(this::touch)
            .orElseGet(() -> open(reference));
}
```

**Me:** That's the one. Turn this into a skill so you write it like that the first time. Put it
next to ticket-desk.
