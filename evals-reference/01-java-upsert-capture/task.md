# Turn this conversation into a skill

Below is the record of a conversation with a coding agent: the first prompt, what the agent
wrote, the correction, and the version that stayed. Turn it into a skill folder. Assume the
Agent Skills format (a `SKILL.md` with `name` and `description` in its front matter) and Java 17.

Write these files and nothing else: `skills/<name>/SKILL.md`, `skills/<name>/references/examples.md`,
and one eval scenario as `evals-reference/01-<slug>/task.md` and `evals-reference/01-<slug>/criteria.json`
(a weighted checklist: `context`, `type`, and `checklist` items with `name`, `description`,
`max_score`). Choose the name. Do not run anything.

## First prompt

> Add a method `findOrOpenTicket(String reference)` to `TicketDesk`: if a ticket with that
> reference exists, return it after marking it as touched, otherwise open a new one with that
> reference and return it.

## What the agent wrote

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

## The correction, in the user's words

> Don't loop over the list with an early return. Use a stream and the Optional API.

## The version that stayed

```java
public Ticket findOrOpenTicket(String reference) {
    return tickets.stream()
            .filter(ticket -> ticket.reference().equals(reference))
            .findFirst()
            .map(this::touch)
            .orElseGet(() -> open(reference));
}
```

The user accepted this and said nothing more.
