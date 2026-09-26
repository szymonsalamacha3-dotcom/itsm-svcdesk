# ai-generated: 85% - validation and request parsing for T03 only; no endpoint or business logic beyond payload normalization

from __future__ import annotations

import os
import uuid
from datetime import datetime, timezone
from typing import Any, Mapping


class RequestValidationError(ValueError):
    def __init__(self, message: str, code: str = "validation", status_code: int = 422):
        super().__init__(message)
        self.message = message
        self.code = code
        self.status_code = status_code

    def to_error(self) -> dict[str, dict[str, str]]:
        return {"error": {"code": self.code, "message": self.message}}


def _is_test_clock_enabled() -> bool:
    value = os.getenv("SVCDESK_TEST_CLOCK", "").strip().lower()
    return value in {"1", "true"}


def parse_test_clock(value: str | None, *, enabled: bool | None = None) -> str | None:
    if value is None or value == "":
        return None
    if enabled is None:
        enabled = _is_test_clock_enabled()
    if not enabled:
        return None

    text = str(value).strip()
    try:
        parsed = datetime.fromisoformat(text.replace("Z", "+00:00"))
    except ValueError as exc:
        raise RequestValidationError("invalid X-Test-Clock") from exc

    if parsed.tzinfo is None:
        raise RequestValidationError("invalid X-Test-Clock")

    utc_value = parsed.astimezone(timezone.utc).replace(microsecond=0)
    return utc_value.isoformat().replace("+00:00", "Z")


def _normalize_boolean(raw: Any, field_name: str) -> bool:
    if isinstance(raw, bool):
        return raw
    raise RequestValidationError(f"{field_name} must be a boolean")


def _normalize_int_in_range(raw: Any, field_name: str, minimum: int, maximum: int) -> int:
    if isinstance(raw, bool) or not isinstance(raw, int):
        raise RequestValidationError(f"{field_name} must be an integer between {minimum} and {maximum}")
    value = int(raw)
    if value < minimum or value > maximum:
        raise RequestValidationError(f"{field_name} must be between {minimum} and {maximum}")
    return value


def parse_ticket_payload(payload: Mapping[str, Any] | None, *, test_clock: str | None = None, test_clock_enabled: bool | None = None) -> dict[str, Any]:
    if not isinstance(payload, Mapping):
        raise RequestValidationError("invalid request body")

    title = payload.get("title")
    if title is None or str(title).strip() == "":
        raise RequestValidationError("title is required")
    title_text = str(title)
    if len(title_text) > 200:
        raise RequestValidationError("title must be 1..200 characters")

    description = payload.get("description")
    if description is not None:
        description_text = str(description)
        if len(description_text) > 4000:
            raise RequestValidationError("description must be at most 4000 characters")
    else:
        description_text = ""

    reporter = payload.get("reporter")
    if reporter is None or not isinstance(reporter, Mapping):
        raise RequestValidationError("reporter is required")

    reporter_name = reporter.get("name")
    if reporter_name is None or str(reporter_name).strip() == "":
        raise RequestValidationError("reporter.name is required")
    reporter_name_text = str(reporter_name)
    if len(reporter_name_text) > 100:
        raise RequestValidationError("reporter.name must be 1..100 characters")

    reporter_email = reporter.get("email")
    if reporter_email is not None and not isinstance(reporter_email, str):
        raise RequestValidationError("reporter.email must be a string or null")

    reporter_vip = reporter.get("vip", False)
    vip_value = _normalize_boolean(reporter_vip, "reporter.vip")

    impact = payload.get("impact")
    if impact is None:
        raise RequestValidationError("impact is required")
    impact_value = _normalize_int_in_range(impact, "impact", 1, 3)

    urgency = payload.get("urgency")
    if urgency is None:
        raise RequestValidationError("urgency is required")
    urgency_value = _normalize_int_in_range(urgency, "urgency", 1, 3)

    related_to = payload.get("related_to")
    if related_to is not None and related_to != "" and not isinstance(related_to, str):
        related_to = str(related_to)

    final_clock = parse_test_clock(test_clock, enabled=test_clock_enabled)
    if final_clock is None:
        final_clock = datetime.now(timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z")

    normalized = {
        "id": str(uuid.uuid4()),
        "title": title_text.strip(),
        "description": description_text,
        "reporter": {
            "name": reporter_name_text.strip(),
            "email": reporter_email,
            "vip": vip_value,
        },
        "impact": impact_value,
        "urgency": urgency_value,
        "priority": None,
        "state": "new",
        "created_at": final_clock,
        "acknowledged_at": None,
        "resolved_at": None,
        "closed_at": None,
        "related_to": related_to,
        "sla": None,
    }

    for key in list(payload.keys()):
        if key in {"id", "priority", "state", "created_at", "acknowledged_at", "resolved_at", "closed_at", "sla"}:
            continue
        if key == "reporter":
            continue

    return normalized


__all__ = ["RequestValidationError", "parse_ticket_payload", "parse_test_clock"]
