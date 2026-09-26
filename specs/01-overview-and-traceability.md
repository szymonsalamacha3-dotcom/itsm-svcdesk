<!-- ai-generated: 20% - synthesized from REQUIREMENTS.md, API.md and CHECKS.md for the pre-implementation specification -->
# Specification overview and requirement traceability

## 1. Purpose

The svcdesk service is a small internal IT service-desk API for a company with around four hundred users across three offices. It must let desk agents, monitoring systems, and future integrations create and inspect tickets, compute priority from impact and urgency, maintain SLA clocks, and refuse requests that would make reports incorrect.

The system is HTTP-only and is expected to be used by automated tooling and by desk agents over JSON.

## 2. Scope and constraints

The service must satisfy all requirements R-01 through R-25, while respecting the API contract defined in API.md and the checker behavior in CHECKS.md.

The implementation must be a single service named svcdesk, must listen on port 8080, and must expose JSON-only HTTP endpoints. The service must run under Docker Compose, must not use bind mounts, and must persist ticket data across restarts.

The specification in this directory documents the behavior before any implementation under src/ is created.

## 3. Decision resolution record

The following decisions are adopted in this specification:

- C1 = wallclock
  - For P1 tickets, acknowledgement and resolution deadlines are calculated using the wall-clock target, not the business-hours-only target.
  - P2–P4 continue to use business-hours calculations.
- C2 = immutable
  - Closed tickets cannot be reopened; a closed ticket produces 409 regardless of age.
  - The client must create a new ticket referencing the prior one via related_to if a new issue needs to be tracked.
- C3 = matrix
  - Reporter VIP status is stored, but it does not modify the priority matrix result.
  - If a VIP ticket would otherwise rank below P2, it is not raised; the default matrix remains authoritative.

## 4. Requirement traceability

| Requirement | Meaning in this specification |
|---|---|
| R-01 | JSON-only HTTP API on port 8080 |
| R-02 | GET /health returns status ok and service svcdesk |
| R-03 | Ticket schema and reporter fields |
| R-04 | Priority matrix |
| R-05 | Priority is service-computed only |
| R-06 | Resolved by C3 = matrix |
| R-07 | State machine and timestamps |
| R-08 | Invalid transition handling |
| R-09 | Immutable closed tickets |
| R-10 | Reopen window for resolved tickets |
| R-11 | Reopen refusal after 7 days |
| R-12 | SLA targets by priority |
| R-13 | Business-hours pause rule |
| R-14 | P1 around-the-clock service decision resolved by C1 = wallclock |
| R-15 | GET /tickets/{id}/sla contract |
| R-16 | Breach and pause semantics |
| R-17 | RFC 3339 UTC timestamps |
| R-18 | Server-generated ids |
| R-19 | List and filtering |
| R-20 | Validation and error bodies |
| R-21 | Test clock semantics |
| R-22 | Compose and environment requirements |
| R-23 | Persistence across container restarts |
| R-24 | Startup readiness within 120 seconds |
| R-25 | 404 JSON error bodies |

## 5. Reference contract sources

This specification is derived from:

- REQUIREMENTS.md as the business intent,
- API.md as the exact HTTP contract,
- CHECKS.md as the conformance rules,
- HANDOUT.md as the lab rules and decision framework.

The API specification is the authoritative contract whenever the requirement wording and the HTTP contract differ in precision.

## 6. Out-of-scope and non-goals

The first build does not attempt to implement full multi-tenant or workflow orchestration beyond the described ticket lifecycle. It also does not validate related_to beyond carrying the identifier as a string field and preserving it in ticket data.

This build is intentionally minimal but must remain faithful to the published checker expectations.
