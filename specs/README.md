<!-- ai-generated: 15% - reviewed from REQUIREMENTS.md, API.md, CHECKS.md and the course handout; no implementation yet -->
# specs/

This directory contains the design specification for the first build of svcdesk. It is intentionally created before any implementation work and is meant to be sufficient for later code generation and verification.

## Decision record in force

This specification is written for the following decisions:

- C1 = wallclock
- C2 = immutable
- C3 = matrix

These choices are a design decision for the implementation, not a claim that all requirements are simultaneously satisfiable. They resolve the contradictions by rejecting the minimal conflicting part of one side of each pair while preserving the rest of the requirement set.

## Specification index

- [01-overview-and-traceability.md](01-overview-and-traceability.md): scope, requirement traceability, constraints, and contract overview.
- [02-ticket-model-and-validation.md](02-ticket-model-and-validation.md): ticket schema, validation, and creation semantics.
- [03-state-machine-and-reopen.md](03-state-machine-and-reopen.md): state transitions, transition validation, and reopen rules.
- [04-sla-and-clocks.md](04-sla-and-clocks.md): SLA targets, business-hours clock, pause logic, breach logic, and test vectors T1–T8.
- [05-compose-and-operations.md](05-compose-and-operations.md): Docker Compose contract, persistence, environment variables, and service lifecycle.

## Implementation boundary

This directory is specification-only. No files under src/ are created or modified in this step, and no runtime or infrastructure implementation is being introduced here. The artifacts in this directory are intended to support the later implementation and verification sequence.

Every Markdown file in this directory keeps the AI disclosure header in its first ten lines, as required by the lab rules.
