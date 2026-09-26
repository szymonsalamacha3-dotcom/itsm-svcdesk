<!-- ai-generated: 30% - derived from R-07, R-08, R-09, R-10, R-11 and API.md section 6 -->
# State machine and reopen rules

## 1. Transition model

The ticket lifecycle is exactly:

new -> acknowledged -> in_progress -> resolved -> closed

The state changes are driven by dedicated endpoints:

| Action | Endpoint | From | To | Side effect |
|---|---|---|---|---|
| acknowledge | POST /tickets/{id}/ack | new | acknowledged | acknowledged_at = now |
| start | POST /tickets/{id}/start | acknowledged | in_progress | none |
| resolve | POST /tickets/{id}/resolve | in_progress | resolved | resolved_at = now |
| close | POST /tickets/{id}/close | resolved | closed | closed_at = now |
| reopen | POST /tickets/{id}/reopen | resolved or closed (with C2 rules) | in_progress | clears resolved_at and closed_at |

All other transitions return 409 Conflict with JSON error body. This includes shortcuts such as:

- resolve from acknowledged,
- resolve from new,
- close from in_progress,
- close from new,
- reopen from new,
- any action on unknown ticket id (404).

## 2. Closed tickets and C2 = immutable

This specification selects C2 = immutable.

This means:

- a resolved ticket may be reopened while still within 7 days of resolution,
- a closed ticket may never be reopened,
- a closed ticket is considered immutable and must be handled by creating a new ticket referencing the old one via related_to,
- a client that tries to reopen a closed ticket receives 409.

R-09 is therefore treated as preserved in the strong form: closed tickets are not reopened; they are referenced by new tickets instead of continued in place.

## 3. Reopen window

For a resolved ticket, reopen is allowed while now <= resolved_at + 7 days.

For a closed ticket, because C2 = immutable, the service refuses reopen regardless of age.

If a reopened resolved ticket is reopened within the window, it returns to in_progress and the service clears the resolved_at timestamp. The original resolution target is not reset or extended.

Reopen after the 7-day window is 409. Reopen from a new ticket is 409.

## 4. Immutable-resource reasoning

This design prioritizes correctness of the dataset and SLA accounting over the convenience of reusing a closed ticket id. It prevents ambiguous reporting and preserves a clean state history for desk metrics.

This choice is also consistent with the requirement that the service rejects things that would make reports wrong (R-09, R-11, R-16).

## 5. State invariants

Implementation must enforce the following invariants:

- A new ticket has no event timestamps.
- An acknowledged ticket has acknowledged_at set but no resolved_at or closed_at.
- An in_progress ticket has acknowledged_at set and no resolved_at or closed_at.
- A resolved ticket has acknowledged_at and resolved_at set and closed_at null.
- A closed ticket has acknowledged_at, resolved_at, and closed_at set and remains immutable.
- Reopen is a transition back to in_progress and must clear both resolved_at and closed_at.

## 6. Unknown resources and invalid actions

Actions on a non-existent id return 404 with a JSON error body. Invalid transitions return 409 with JSON error body. The exact code strings are not semantically checked in Lab 1, but the presence of a top-level error object is required.
