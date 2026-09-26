<!-- ai-generated: 25% - derived from the accepted specification and the implementation plan for the FastAPI build -->
# Lab 1 tasks

## Task overview

This task list is intended to drive the later implementation of svcdesk under src/ without changing Docker or compose files. Each task includes the scope, dependencies, completion criteria, and the requirement/check mapping it supports.

## Task T01 — App foundation and runtime configuration

**Goal:** Prepare the FastAPI application skeleton and runtime configuration for the service.

**Depends on:** none

**Requirements covered:** R-01, R-02, R-22, R-24, R-25

**Checks covered:** L1-CORE-1.01 to 1.04, L1-CORE-2.01, 2.02

**Completion criteria:**

- FastAPI app is initialized in Python 3.13.
- application exposes /health on port 8080 in the compose contract.
- /health returns the required JSON payload.
- service uses JSON-only responses and error handling.

## Task T02 — Persistence layer and ticket storage

**Goal:** Add a durable storage backend for tickets and allow records to survive service restart.

**Depends on:** T01

**Requirements covered:** R-18, R-23, R-22

**Checks covered:** L1-CORE-1.03, L1-CORE-2.05, 2.06, 2.20, 2.22, 2.23

**Completion criteria:**

- database bootstrap is implemented.
- ticket records are stored persistently.
- create/get/list operations can read and write the same data safely.
- ticket id generation is unique and opaque.

## Task T03 — Ticket validation and request parsing

**Goal:** Validate create-ticket payloads and reject invalid data with 400 or 422 and top-level error objects.

**Depends on:** T01, T02

**Requirements covered:** R-03, R-17, R-20, R-21

**Checks covered:** L1-CORE-2.03, 2.04, 2.16, 2.17, 2.18, 2.19, 2.21, 2.49

**Completion criteria:**

- title is required and length is 1..200.
- description is optional and <= 4000.
- reporter.name is required and length is 1..100.
- impact and urgency are required integers in 1..3.
- malformed X-Test-Clock results in 400 or 422.
- unknown fields are silently ignored.

## Task T04 — Ticket create/get/list endpoints

**Goal:** Expose the main read and create API endpoints that satisfy the HTTP contract.

**Depends on:** T02, T03

**Requirements covered:** R-01, R-02, R-18, R-19, R-25

**Checks covered:** L1-CORE-2.05, 2.06, 2.20, 2.21, 2.22, 2.23

**Completion criteria:**

- POST /tickets answers 201 with a full ticket object.
- GET /tickets returns all matching tickets in one array.
- GET /tickets/{id} returns 200 for known id and 404 for unknown id.
- a created ticket contains all required fields.

## Task T05 — Priority matrix and C3 = matrix

**Goal:** Compute priority solely from impact and urgency and ignore any attacker-supplied priority field.

**Depends on:** T03, T04

**Requirements covered:** R-04, R-05, R-06, R-20

**Checks covered:** L1-CORE-2.07 to 2.15, 2.46 to 2.48

**Completion criteria:**

- matrix values match API.md exactly.
- VIP reporter value is stored but does not alter priority.
- priority field in request body is ignored.
- VIP P1 stays P1 under the selected decision.

## Task T06 — State machine and legal transitions

**Goal:** Implement the lifecycle states and enforce valid transitions only.

**Depends on:** T04, T05

**Requirements covered:** R-07, R-08, R-09, R-10, R-11

**Checks covered:** L1-CORE-2.24 to 2.35, 2.49

**Completion criteria:**

- new -> acknowledged -> in_progress -> resolved -> closed is enforced.
- invalid transitions return 409 with top-level error object.
- unknown ids return 404.
- state timestamps are stored correctly.
- closed tickets are immutable under C2 = immutable.

## Task T07 — Reopen logic and immutable closed behavior

**Goal:** Enforce the selected C2 decision without violating the service's integrity rules.

**Depends on:** T06

**Requirements covered:** R-09, R-10, R-11

**Checks covered:** L1-CORE-2.32 to 2.35

**Completion criteria:**

- reopen from resolved is allowed within 7 days.
- reopen from closed is rejected with 409.
- reopen after 7 days + 1 second is rejected.
- reopened resolved ticket returns to in_progress without resetting original target.

## Task T08 — Test clock implementation

**Goal:** Implement per-request test clock validation and application for now-based logic.

**Depends on:** T03, T06

**Requirements covered:** R-21

**Checks covered:** L1-CORE-2.03, 2.04, 2.24, 2.28, 2.30, 2.32, 2.33, 2.35, 2.42 to 2.45

**Completion criteria:**

- SVCDESK_TEST_CLOCK=1 or true allows a valid X-Test-Clock header.
- malformed header is rejected.
- the clock is used only for the current request.
- action timestamps and SLA evaluations use the request clock for the request in question.

## Task T09 — SLA target calculation for P1-P4

**Goal:** Compute ack and resolve due instants for all priorities and all vectors.

**Depends on:** T05, T08

**Requirements covered:** R-12, R-13, R-14, R-17

**Checks covered:** L1-CORE-2.36 to 2.41

**Completion criteria:**

- P1 uses wallclock under C1 = wallclock.
- P2-P4 use business-hours clock.
- T1-T8 values match the published exact values.
- tie behavior at closing time follows the published rule.

## Task T10 — /sla breach and pause logic

**Goal:** Implement GET /tickets/{id}/sla with breach and pause status evaluated at current request time.

**Depends on:** T08, T09

**Requirements covered:** R-15, R-16, R-21

**Checks covered:** L1-CORE-2.42 to 2.45

**Completion criteria:**

- ack_breached and resolve_breached are correct.
- equality is not breach.
- paused is true only for open tickets whose resolution target is on business-hours clock and now is outside business hours.
- wall-clock SLA always returns paused = false.

## Task T11 — Compose, environment, and service readiness

**Goal:** Finalize the service runtime contract for Docker Compose.

**Depends on:** T01, T02, T04, T10

**Requirements covered:** R-22, R-23, R-24

**Checks covered:** L1-CORE-1.01 to 1.04

**Completion criteria:**

- compose defines svcdesk with build and no bind mounts.
- service listens on 8080.
- environment has SVCDESK_TEST_CLOCK set.
- /health responds within 120 seconds after docker compose up --wait.

## Task T12 — Full conformance and decision consistency

**Goal:** Run the published checker and confirm the implementation matches DECISIONS.md, API.md, and the checks.

**Depends on:** all previous tasks

**Requirements covered:** all R-01 to R-25

**Checks covered:** L1-CORE-2.01 to 2.49, L1-CORE-3, L1-CORE-4

**Completion criteria:**

- every required check passes.
- DECISIONS.md front matter values match live observed values.
- no requirement is violated by the chosen C1/C2/C3 decisions.

## Task dependency summary

- T01 -> T02 -> T03 -> T04
- T03 -> T05
- T04 + T05 -> T06 -> T07
- T03 + T06 -> T08
- T05 + T08 -> T09
- T08 + T09 -> T10
- T01 + T02 + T04 + T10 -> T11
- All -> T12

## Coverage summary

| Area | Tasks |
|---|---|
| health and basic API | T01, T04, T11 |
| validation and data model | T02, T03 |
| priority and C3 | T05 |
| state machine and C2 | T06, T07 |
| test clock | T08 |
| SLA, pause and breach | T09, T10 |
| end-to-end conformance | T12 |
