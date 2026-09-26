<!-- ai-generated: 35% - based on R-12 through R-17, R-23, API.md section 4, 5 and the T1-T8 vectors -->
# SLA targets, pause conditions, and test vectors

## 1. Priority targets

The service calculates acknowledgement and resolution targets from the ticket's priority and creation instant.

| priority | acknowledge within | resolve within |
|---|---|---|
| P1 | 15 min | 4 h |
| P2 | 1 h | 8 h |
| P3 | 4 h | 24 h |
| P4 | 8 h | 72 h |

This is defined by R-12 and API.md §4.

## 2. Clock choice for this specification

This specification selects C1 = wallclock.

That means:

- P1 acknowledgement and resolution deadlines are computed as wall-clock targets from created_at,
- P2–P4 continue to use the business-hours clock,
- A mixed P1 configuration is not allowed; the implementation must choose one of the two admissible values and keep it consistent for all P1 tickets.

This choice resolves the conflict between R-13 and R-14 by retaining the clock algorithm for P1 at wall-clock and preserving business-hours rules elsewhere.

## 3. Business-hours clock semantics

The business-hours clock is evaluated in Europe/Warsaw and counts only time between Monday and Friday, 08:00:00 and 16:00:00, with the half-open window [08:00:00, 16:00:00).

Rules:

- if created_at falls outside a business window, the count begins at the next opening time,
- the target duration is consumed across consecutive business windows,
- a target that ends exactly at closing time is due at 16:00:00 local time and not at 08:00:00 next morning,
- DST transitions are handled by the timezone database and do not cross into the middle of a business window in the course vectors,
- Polish public holidays are out of scope for this lab.

## 4. Due instant generation

For each ticket, the service computes `sla.ack_due_at` and `sla.resolve_due_at` using the selected clock strategy.

Important rules:

- all timestamps reported via API are RFC3339 instants in UTC with Z suffix,
- the due instant is compared using instants, never as strings,
- equality is not a breach,
- `GET /tickets/{id}/sla` reports the values at the request clock.

## 5. Breach logic

A target is breached when:

- the event has not happened and the due instant has passed, or
- the event has happened and the timestamp is later than the due instant.

The precise rules:

- ack_breached = true if not acknowledged and now > ack_due_at, or acknowledged_at > ack_due_at
- resolve_breached = true if not resolved and now > resolve_due_at, or resolved_at > resolve_due_at
- equality is not a breach
- reopened tickets are treated as not resolved again for the purposes of resolution breach
- once resolved or closed, the service uses the event timestamp to determine breach status

For a ticket whose targets are wall-clock, paused is always false. For a ticket whose resolution target is on the business-hours clock, paused is true when the ticket is still open and now is outside a business window.

## 6. Pause logic

The implementation must support:

- `paused` = true only when the ticket is not resolved or closed,
- the resolution target runs on the business-hours clock,
- the current request time falls outside the business window,
- the ticket still qualifies to be paused under the chosen clock strategy.

If the resolution target is wall-clock, `paused` is always false.

## 7. Required test vectors

The implementation must reproduce the exact values in the checker vectors. These vector values are part of the contract and must be encoded in the final implementation logic as test fixtures or deterministic business-hours calculations.

### T1
- ticket: P1, created_at 2026-10-14T10:00:00Z
- ack due: 2026-10-14T10:15:00Z (wall-clock) and same under business-hours
- resolve due: 2026-10-14T14:00:00Z (wall-clock and business hours)

### T2
- ticket: P3, created_at 2026-10-16T13:30:00Z
- ack due: 2026-10-16T17:30:00Z (wall-clock), 2026-10-19T09:30:00Z (business-hours)
- resolve due: 2026-10-17T13:30:00Z (wall-clock), 2026-10-21T13:30:00Z (business-hours)

### T3
- ticket: P1, created_at 2026-10-16T15:00:00Z
- With C1 = wallclock: ack due 2026-10-16T15:15:00Z, resolve due 2026-10-16T19:00:00Z
- With C1 = business: ack due 2026-10-19T06:15:00Z, resolve due 2026-10-19T10:00:00Z
- This vector is the decisive test for C1.

### T4
- ticket: P2, created_at 2026-10-17T10:00:00Z
- ack due: 2026-10-17T11:00:00Z (wall-clock), 2026-10-19T07:00:00Z (business-hours)
- resolve due: 2026-10-17T18:00:00Z (wall-clock), 2026-10-19T14:00:00Z (business-hours)
- tie rule: a target that ends exactly at closing time is due at 16:00 local, not next business morning.

### T5
- ticket: P4, created_at 2027-01-14T14:30:00Z
- ack due: 2027-01-14T22:30:00Z (wall-clock), 2027-01-15T14:30:00Z (business-hours)
- resolve due: 2027-01-17T14:30:00Z (wall-clock), 2027-01-27T14:30:00Z (business-hours)

### T6
- ticket: P1, created_at 2027-01-15T15:50:00Z
- With C1 = wallclock: ack due 2027-01-15T16:05:00Z, resolve due 2027-01-15T19:50:00Z
- With C1 = business: ack due 2027-01-18T07:15:00Z, resolve due 2027-01-18T11:00:00Z

### T7
- ticket: P2, created_at 2026-10-14T10:00:00Z
- ack due: 2026-10-14T11:00:00Z (wall-clock), 2026-10-14T11:00:00Z (business-hours)
- resolve due: 2026-10-14T18:00:00Z (wall-clock), 2026-10-15T10:00:00Z (business-hours)

### T8
- ticket: P3, created_at 2026-10-23T13:00:00Z
- ack due: 2026-10-23T17:00:00Z (wall-clock), 2026-10-26T10:00:00Z (business-hours)
- resolve due: 2026-10-24T13:00:00Z (wall-clock), 2026-10-28T14:00:00Z (business-hours)

## 8. Implementation notes for later work

The later implementation must:

- use Europe/Warsaw timezone data in the container image,
- calculate due instants using deterministic business-hours logic,
- expose the values through GET /tickets/{id}/sla,
- ensure no comparisons depend on string ordering of ISO timestamps,
- maintain the same logic across create and read APIs.
