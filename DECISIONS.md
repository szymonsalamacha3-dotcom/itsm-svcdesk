---
svcdesk_decisions:
  C1: wallclock      # wallclock | business
  C2: immutable      # reopen | immutable
  C3: matrix         # matrix | vip
---
<!-- ai-generated: 90% - Copilot Agent drafted the document from the course requirements; I selected and reviewed C1, C2 and C3 -->

# Decisions

## C1

**Decision:** We choose wallclock for P1: both the acknowledgement and resolution targets for P1 are measured from created_at with no business-hours pause. P2 to P4 remain on the business-hours clock.

**Rejected alternative:** The business-hours clock for P1 would delay escalation until the next opening and would make Friday-evening P1 tickets wait until Monday instead of breaching at 15 minutes or 4 hours from creation.

**Reason:** This keeps the P1 SLA aligned with the requirement that a critical ticket is treated as urgent around the clock. The decision preserves the business-hours logic for all lower priorities while rejecting the minimal contradictory part of R-13 for P1 only, so the service still matches the operational need for executive incident handling.

**Service owner:** The service desk operations manager is the owner of this decision because P1 tickets represent high-severity incidents that must be visible and acted on without waiting for the next business window.

**Customer outcome:** A reporter with a critical outage sees the desk treat the issue as genuinely urgent immediately after creation, and the organisation still gets a deterministic SLA calculation that is easy to audit across the Monday report.

## C2

**Decision:** We choose immutable for closed tickets: reopen is allowed only from resolved tickets within 7 days, and a closed ticket is rejected with 409 regardless of age. A new ticket must be created with related_to if the work continues after closure.

**Rejected alternative:** The reopen-from-closed behaviour would allow a closed case to be reopened inside the window, but it would blur the line between a completed case and an active incident and would make the closed state less trustworthy for reporting.

**Reason:** The service must refuse actions that would make reports wrong. Closing a ticket is a deliberate completion event, and preserving immutability keeps the history accurate for audits, SLA review, and the desk's Monday backlog reports. We reject only the conflicting part of R-10 that allows reopening a closed ticket, while keeping the reopened-resolved behaviour intact.

**Service owner:** The service owner for this decision is the IT service desk lead, because the closed state is the official completion record and the desk must preserve an accurate historical dataset for operational reporting.

**Customer outcome:** A reporter can still ask for a failed fix to be revisited while it is still within the resolved window, but the organisation does not lose the integrity of closed-case reporting or create ambiguous repair histories.

## C3

**Decision:** We choose matrix for VIP handling: the service stores reporter.vip, but the computed priority follows the impact/urgency matrix exactly and does not boost a low-priority ticket. This preserves the matrix as the single source of priority truth.

**Rejected alternative:** The vip rule would raise a VIP ticket at P3 or P4 to P2 after the matrix, which would make the priority depend on the reporter identity instead of the operational impact alone.

**Reason:** This keeps the service objective and predictable: desk triage is driven by damage and urgency, not by personal status. We reject the conflicting part of R-06 that says VIP tickets are never lower than P2, but we retain the business value of recording VIP status for visibility and special handling outside the priority computation.

**Service owner:** The service desk product owner is the correct owner because priority policy directly affects triage fairness, queue ordering, and operational accountability across all desk agents.

**Customer outcome:** The organisation gets a stable, explainable priority model that supports consistent queueing and SLA reporting, while VIP reporters still remain visible in the ticket data even though the service does not distort the matrix for reporting integrity.
