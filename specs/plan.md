<!-- ai-generated: 20% - based on the accepted specification and the resolved C1/C2/C3 decisions for implementation planning only -->
# Lab 1 implementation plan

## 1. Objective

Implement a Python 3.13 FastAPI service named svcdesk that satisfies the published HTTP contract in API.md and the published checks in CHECKS.md, while staying consistent with the decisions recorded in DECISIONS.md:

- C1 = wallclock
- C2 = immutable
- C3 = matrix

This document is a planning artifact only. It does not create code under src/ and does not change Docker or compose configuration.

## 2. Architectural decisions

### Service runtime

- Use FastAPI with Python 3.13.
- Run as a single HTTP service on port 8080.
- Expose only JSON request/response bodies.
- Keep all business logic in a small service layer with a storage layer behind it.
- Use a single SQLite database file persisted through a named volume in Docker Compose.

### Data model

- A ticket is the single canonical entity.
- Persist the ticket record and its associated timestamps and SLA fields.
- Keep server-owned fields authoritative: id, priority, state, created_at, acknowledged_at, resolved_at, closed_at, sla.
- Maintain a clear distinction between inbound user data and derived service data.

### Decision-driven behavior

- C1 = wallclock: P1 uses wall-clock due instants; P2-P4 use business-hours due instants.
- C2 = immutable: reopen is allowed only from resolved tickets within 7 days; closed tickets are rejected with 409.
- C3 = matrix: priority is computed solely from the impact/urgency matrix; VIP status is stored but does not adjust priority.

## 3. Delivery phases

### Phase 1 — Foundation and persistence

Create the FastAPI application shell, dependency structure, configuration, SQLite persistence, and CRUD helpers for tickets. This phase establishes the data contract before branching into workflow logic.

Deliverables:

- app module layout
- database initialization and migration/bootstrap
- ticket repository functions
- JSON error responses and 404 handling

Required requirements:

- R-01, R-18, R-19, R-22, R-23, R-24, R-25

Related checks:

- L1-CORE-1.01 to 1.04
- L1-CORE-2.20, 2.21, 2.22, 2.23

### Phase 2 — Ticket creation and validation

Implement ticket creation, validation, default fields, and exact response shape. Ensure server-owned and unknown fields are ignored. Accept the test clock header when enabled and reject malformed values.

Deliverables:

- request schema validation
- create endpoint behavior and exact 201 success response
- unknown-field handling
- test clock injection logic

Required requirements:

- R-03, R-05, R-17, R-18, R-20, R-21

Related checks:

- L1-CORE-2.03, 2.04, 2.05, 2.06, 2.16 to 2.19

### Phase 3 — Priority matrix and C3 behavior

Implement the matrix-based priority calculation and ensure that user-supplied priority is ignored. Confirm that VIP is stored but does not alter the computed matrix result under the chosen C3 = matrix decision.

Deliverables:

- priority function based on impact and urgency
- VIP preservation without priority mutation
- one source of truth for priority assignment

Required requirements:

- R-04, R-05, R-06, R-20

Related checks:

- L1-CORE-2.07 to 2.15
- L1-CORE-2.46 to 2.48

### Phase 4 — State machine and transition enforcement

Implement the lifecycle states and the endpoint-by-endpoint transitions. Restrict invalid transitions to 409 with JSON error body. Enforce the immutable-closed behavior as selected by C2 = immutable.

Deliverables:

- state machine rules
- transition validation
- state timestamps for acknowledge, resolve, close
- reopen logic and 7-day window

Required requirements:

- R-07, R-08, R-09, R-10, R-11, R-25

Related checks:

- L1-CORE-2.24 to 2.35, 2.49

### Phase 5 — SLA and due instants

Implement the SLA target algorithm for P1 through P4, with business-hours logic for P2-P4 and wall-clock logic for P1 under C1 = wallclock. Compute both ack and resolve due instants, and validate them against the published vectors T1-T8.

Deliverables:

- priority-to-target map
- business-hours utility calculations in Europe/Warsaw
- due instant generation
- exact tie handling at 16:00 close time
- per-request evaluation logic

Required requirements:

- R-12, R-13, R-14, R-15, R-16, R-17

Related checks:

- L1-CORE-2.36 to 2.41

### Phase 6 — Breach and pause logic

Compute ack_breached, resolve_breached, and paused using the request clock or the real time as needed. Ensure equality is not breach and that paused is false for wall-clock targets.

Deliverables:

- /sla endpoint response body
- breach evaluation
- pause evaluation
- request-clock evaluation against stored timestamps

Required requirements:

- R-15, R-16, R-21

Related checks:

- L1-CORE-2.42 to 2.45

### Phase 7 — Validation and final verification pass

Run the checker and fix any drift from the API contract or decision-specific behavior. Confirm that the observed values match C1, C2 and C3 as recorded in DECISIONS.md.

Deliverables:

- final conformance validation
- decision-value consistency verification
- final API contract validation against the checker

Required requirements:

- all R-01 to R-25

Related checks:

- L1-CORE-2.01 to 2.49
- L1-CORE-3.01 to 3.03
- L1-CORE-4.01 to 4.03

## 4. Implementation order and dependencies

The sequence below is the working order for implementation:

1. Persistence and application shell
2. Ticket schema and validation
3. Create ticket endpoint and list/get endpoints
4. Priority computation and matrix logic
5. State transitions and invalid-transition handling
6. Reopen window and closed-ticket immutability
7. Test clock handling
8. SLA due calculation for all priorities
9. /sla breach and pause response
10. Final conformance checks and decision-value alignment

Dependencies:

- Validation must be complete before create-list-get endpoints are trusted.
- Priority computation must exist before creating and listing valid tickets with expected priority.
- State machine must be implemented before reopen and closure checks are meaningful.
- SLA logic must be ready before /sla tests are exercised.
- Final verification depends on all earlier phases being correct.

## 5. Completion criteria for each phase

A phase is complete when all of the following are satisfied:

- the HTTP contract matches the relevant section of API.md,
- the implementation agrees with the published checker expectations,
- the states and transitions match the selected decisions,
- the error conditions return JSON with a top-level error object,
- the service can be exercised with the published test vectors and clock semantics,
- the feature is stable against zero or more repeated runs.

## 6. Verification strategy

The implementation should be checked by the project checker after each phase as follows:

1. bootstrap and health tests,
2. create/list/get and validation,
3. matrix and VIP checks,
4. state machine and reopen checks,
5. SLA vectors and breach/pause checks,
6. full L1-CORE-2 conformance run,
7. DECISIONS consistency checks.

This phased validation mirrors the sequence in HANDOUT.md and ensures that design issues are caught before the full conformance pass.
