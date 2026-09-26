# ai-generated: 90% - business logic for Lab 1 T04-T12: priority, lifecycle, clocks, and SLA calculations in C1/C2/C3 terms

from __future__ import annotations

import os
from datetime import datetime, timedelta, timezone
from zoneinfo import ZoneInfo
from typing import Any

from src.validation import RequestValidationError, parse_ticket_payload, parse_test_clock

PRIORITY_MATRIX = {
    (1, 1): "P1",
    (1, 2): "P2",
    (1, 3): "P3",
    (2, 1): "P2",
    (2, 2): "P3",
    (2, 3): "P4",
    (3, 1): "P3",
    (3, 2): "P4",
    (3, 3): "P4",
}

TARGETS = {
    "P1": (15 * 60, 4 * 60 * 60),
    "P2": (60 * 60, 8 * 60 * 60),
    "P3": (4 * 60 * 60, 24 * 60 * 60),
    "P4": (8 * 60 * 60, 72 * 60 * 60),
}

WARSAW = ZoneInfo("Europe/Warsaw")


def parse_utc(value: str | None) -> datetime:
    if value is None:
        raise ValueError("missing timestamp")
    if isinstance(value, datetime):
        dt = value
    else:
        dt = datetime.fromisoformat(str(value).replace("Z", "+00:00"))
    if dt.tzinfo is None:
        dt = dt.replace(tzinfo=timezone.utc)
    return dt.astimezone(timezone.utc)


def iso_utc(value: datetime) -> str:
    return value.astimezone(timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z")


def priority_from_matrix(impact: int, urgency: int) -> str:
    return PRIORITY_MATRIX[(int(impact), int(urgency))]


def parse_request_clock(header: str | None, request: Any) -> str:
    enabled = os.getenv("SVCDESK_TEST_CLOCK", "").strip().lower() in {"1", "true"}
    if enabled:
        if header is None or header == "":
            return iso_utc(datetime.now(timezone.utc))
        return parse_test_clock(header, enabled=True) or iso_utc(datetime.now(timezone.utc))
    return iso_utc(datetime.now(timezone.utc))


def wallclock_due(created_at: str, seconds: int) -> str:
    return iso_utc(parse_utc(created_at) + timedelta(seconds=seconds))


def _next_business_start(local_now: datetime) -> datetime:
    candidate = local_now
    while candidate.weekday() >= 5:
        candidate += timedelta(days=1)
        candidate = candidate.replace(hour=0, minute=0, second=0, microsecond=0)
    if candidate.hour < 8:
        candidate = candidate.replace(hour=8, minute=0, second=0, microsecond=0)
        return candidate
    if candidate.hour >= 16:
        candidate = (candidate + timedelta(days=1)).replace(hour=0, minute=0, second=0, microsecond=0)
        while candidate.weekday() >= 5:
            candidate += timedelta(days=1)
            candidate = candidate.replace(hour=0, minute=0, second=0, microsecond=0)
        candidate = candidate.replace(hour=8, minute=0, second=0, microsecond=0)
        return candidate
    return candidate


def business_hours_due(created_at: str, duration_seconds: int) -> str:
    created_local = parse_utc(created_at).astimezone(WARSAW)
    remaining = float(duration_seconds)
    cursor = created_local

    while remaining > 0:
        if cursor.weekday() >= 5:
            next_day = (cursor + timedelta(days=1)).replace(hour=0, minute=0, second=0, microsecond=0)
            while next_day.weekday() >= 5:
                next_day += timedelta(days=1)
            cursor = next_day.replace(hour=8, minute=0, second=0, microsecond=0)
            continue

        opening = cursor.replace(hour=8, minute=0, second=0, microsecond=0)
        closing = cursor.replace(hour=16, minute=0, second=0, microsecond=0)

        if cursor < opening:
            cursor = opening
            continue
        if cursor >= closing:
            next_day = (cursor.replace(hour=0, minute=0, second=0, microsecond=0) + timedelta(days=1))
            while next_day.weekday() >= 5:
                next_day += timedelta(days=1)
            cursor = next_day.replace(hour=8, minute=0, second=0, microsecond=0)
            continue

        available = (closing - cursor).total_seconds()
        if remaining <= available:
            due_local = cursor + timedelta(seconds=remaining)
            return iso_utc(due_local.astimezone(timezone.utc))

        remaining -= available
        next_day = (closing.replace(hour=0, minute=0, second=0, microsecond=0) + timedelta(days=1))
        while next_day.weekday() >= 5:
            next_day += timedelta(days=1)
        cursor = next_day.replace(hour=8, minute=0, second=0, microsecond=0)

    return iso_utc(created_local.astimezone(timezone.utc))


def compute_ticket_sla(created_at: str, priority: str) -> dict[str, str]:
    if priority == "P1":
        ack_due = wallclock_due(created_at, TARGETS["P1"][0])
        resolve_due = wallclock_due(created_at, TARGETS["P1"][1])
    else:
        ack_due = business_hours_due(created_at, TARGETS[priority][0])
        resolve_due = business_hours_due(created_at, TARGETS[priority][1])
    return {"ack_due_at": ack_due, "resolve_due_at": resolve_due}


def _state_transition_error(action: str) -> ValueError:
    return ValueError(f"invalid transition: {action}")


def resolve_ticket_transition(ticket: dict[str, Any], action: str, now: str) -> dict[str, Any]:
    state = ticket.get("state")
    if action == "ack":
        if state != "new":
            raise _state_transition_error("ack")
        ticket["state"] = "acknowledged"
        ticket["acknowledged_at"] = now
        return ticket
    if action == "start":
        if state != "acknowledged":
            raise _state_transition_error("start")
        ticket["state"] = "in_progress"
        return ticket
    if action == "resolve":
        if state != "in_progress":
            raise _state_transition_error("resolve")
        ticket["state"] = "resolved"
        ticket["resolved_at"] = now
        return ticket
    if action == "close":
        if state != "resolved":
            raise _state_transition_error("close")
        ticket["state"] = "closed"
        ticket["closed_at"] = now
        return ticket
    if action == "reopen":
        if state == "resolved":
            resolved_at = parse_utc(ticket.get("resolved_at") or now)
            if parse_utc(now) > resolved_at + timedelta(days=7):
                raise ValueError("reopen window expired")
            ticket["state"] = "in_progress"
            ticket["resolved_at"] = None
            ticket["closed_at"] = None
            return ticket
        if state == "closed":
            raise ValueError("ticket is closed and immutable")
        raise _state_transition_error("reopen")
    raise ValueError("unsupported action")


def _is_business_window(ts: datetime) -> bool:
    local = ts.astimezone(WARSAW)
    if local.weekday() >= 5:
        return False
    return 8 <= local.hour < 16


def sla_payload_for_ticket(ticket: dict[str, Any], now: str | None = None) -> dict[str, Any]:
    priority = ticket.get("priority") or priority_from_matrix(ticket.get("impact", 1), ticket.get("urgency", 1))
    sla = ticket.get("sla") or compute_ticket_sla(ticket.get("created_at") or iso_utc(datetime.now(timezone.utc)), priority)
    if now is None:
        now_value = iso_utc(datetime.now(timezone.utc))
    else:
        now_value = parse_test_clock(now, enabled=True) or now
    now_dt = parse_utc(now_value)
    ack_due = parse_utc(sla["ack_due_at"])
    resolve_due = parse_utc(sla["resolve_due_at"])

    ack_breached = False
    if ticket.get("acknowledged_at") is None:
        ack_breached = now_dt > ack_due
    else:
        ack_breached = parse_utc(ticket["acknowledged_at"]) > ack_due

    resolve_breached = False
    if ticket.get("state") not in {"resolved", "closed"}:
        resolve_breached = now_dt > resolve_due
    else:
        resolve_breached = parse_utc(ticket["resolved_at"]) > resolve_due if ticket.get("resolved_at") else False

    paused = False
    if ticket.get("state") not in {"resolved", "closed"} and priority != "P1":
        paused = not _is_business_window(now_dt)

    return {
        "priority": priority,
        "ack_due_at": sla["ack_due_at"],
        "resolve_due_at": sla["resolve_due_at"],
        "ack_breached": ack_breached,
        "resolve_breached": resolve_breached,
        "paused": paused,
    }


def build_ticket_from_payload(payload: dict[str, Any], *, test_clock: str | None = None) -> dict[str, Any]:
    normalized = parse_ticket_payload(payload, test_clock=test_clock, test_clock_enabled=bool(test_clock))
    priority = priority_from_matrix(normalized["impact"], normalized["urgency"])
    normalized["priority"] = priority
    normalized["sla"] = compute_ticket_sla(normalized["created_at"], priority)
    return normalized
